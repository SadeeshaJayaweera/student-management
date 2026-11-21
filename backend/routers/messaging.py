"""backend/routers/messaging.py
Enterprise Messaging and Communication Router
Features multi-party & direct messaging threads, attachment support,
real-time unread badges, contact directories, and message history.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    Student,
    Lecturer,
    Course,
    Conversation,
    ConversationParticipant,
    Message,
)
from backend.schemas import (
    ConversationCreate,
    MessageSendPayload,
    ConversationParticipantOut,
    DirectMessageOut,
    ConversationListItemOut,
    ConversationDetailOut,
    MessagingContactOut,
)
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/messaging", tags=["Messaging & Communication"])


def serialize_participant(p: ConversationParticipant) -> ConversationParticipantOut:
    u = p.user
    role_str = u.role.value if hasattr(u.role, "value") else str(u.role)
    return ConversationParticipantOut(
        id=p.id,
        user_id=p.user_id,
        name=u.full_name if u else "User",
        role=role_str,
        email=u.email if u else "",
        last_read_at=p.last_read_at,
    )


def serialize_message(m: Message) -> DirectMessageOut:
    sender_name = m.sender.full_name if m.sender else "User"
    role_str = m.sender.role.value if (m.sender and hasattr(m.sender.role, "value")) else str(m.sender.role if m.sender else "user")
    return DirectMessageOut(
        id=m.id,
        conversation_id=m.conversation_id,
        sender_id=m.sender_id,
        sender_name=sender_name,
        sender_role=role_str,
        receiver_id=m.receiver_id,
        content=m.content,
        attachment_url=m.attachment_url,
        attachment_name=m.attachment_name,
        is_read=m.is_read,
        read_at=m.read_at,
        sent_at=m.sent_at,
    )


# ─── Conversation Endpoints ───────────────────────────────────────────────────

@router.post("/conversations", response_model=ConversationDetailOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initiate a direct or course inquiry messaging thread with another university member."""
    # Verify recipient exists
    rec_res = await db.execute(select(User).where(User.id == payload.recipient_id))
    recipient = rec_res.scalars().first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient user not found.")

    if recipient.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot start a conversation with yourself.")

    # Check course if provided
    course_code = None
    if payload.course_id:
        c_res = await db.execute(select(Course).where(Course.id == payload.course_id))
        course = c_res.scalars().first()
        if course:
            course_code = course.course_code

    now = datetime.utcnow()
    conversation = Conversation(
        subject=payload.subject or f"Conversation with {recipient.full_name}",
        thread_type=payload.thread_type,
        course_id=payload.course_id,
        created_by_id=current_user.id,
        last_message_at=now,
        status="active",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    # Add participants: current_user (creator) and recipient
    p_creator = ConversationParticipant(
        conversation_id=conversation.id,
        user_id=current_user.id,
        last_read_at=now,
    )
    p_recipient = ConversationParticipant(
        conversation_id=conversation.id,
        user_id=recipient.id,
        last_read_at=None,
    )
    db.add_all([p_creator, p_recipient])

    # Add initial message
    first_msg = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        receiver_id=recipient.id,
        content=payload.initial_message,
        attachment_url=payload.attachment_url,
        attachment_name=payload.attachment_name,
        is_read=False,
        sent_at=now,
    )
    db.add(first_msg)
    await db.commit()

    # Reload conversation with participants and message
    res = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.participants).selectinload(ConversationParticipant.user),
            selectinload(Conversation.messages).selectinload(Message.sender),
            selectinload(Conversation.course),
        )
        .where(Conversation.id == conversation.id)
    )
    loaded = res.scalars().first()

    return ConversationDetailOut(
        id=loaded.id,
        subject=loaded.subject,
        thread_type=loaded.thread_type,
        course_id=loaded.course_id,
        course_code=course_code,
        participants=[serialize_participant(p) for p in loaded.participants],
        messages=[serialize_message(m) for m in loaded.messages],
    )


@router.get("/conversations", response_model=List[ConversationListItemOut])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active conversation threads for the authenticated user, sorted by last message time."""
    # Find all conversation IDs where current_user is participant
    part_res = await db.execute(
        select(ConversationParticipant)
        .where(ConversationParticipant.user_id == current_user.id)
    )
    my_participations = {p.conversation_id: p for p in part_res.scalars().all()}
    if not my_participations:
        return []

    c_query = (
        select(Conversation)
        .options(
            selectinload(Conversation.participants).selectinload(ConversationParticipant.user),
            selectinload(Conversation.messages).selectinload(Message.sender),
            selectinload(Conversation.course),
        )
        .where(Conversation.id.in_(list(my_participations.keys())), Conversation.status == "active")
        .order_by(desc(Conversation.last_message_at))
    )
    c_res = await db.execute(c_query)
    conversations = c_res.scalars().all()

    out: List[ConversationListItemOut] = []
    for conv in conversations:
        my_part = my_participations.get(conv.id)
        last_read = my_part.last_read_at if my_part else None

        # Calculate unread messages
        unread_cnt = 0
        latest_snippet = None
        if conv.messages:
            latest_msg = conv.messages[-1]
            latest_snippet = latest_msg.content[:80] + ("..." if len(latest_msg.content) > 80 else "")

            for m in conv.messages:
                if m.sender_id != current_user.id:
                    if not last_read or m.sent_at > last_read or not m.is_read:
                        unread_cnt += 1

        c_code = conv.course.course_code if conv.course else None
        out.append(
            ConversationListItemOut(
                id=conv.id,
                subject=conv.subject,
                thread_type=conv.thread_type,
                course_id=conv.course_id,
                course_code=c_code,
                participants=[serialize_participant(p) for p in conv.participants],
                last_message_at=conv.last_message_at,
                latest_message_snippet=latest_snippet,
                unread_count=unread_cnt,
            )
        )
    return out


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full conversation stream and mark unread incoming messages as read."""
    res = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.participants).selectinload(ConversationParticipant.user),
            selectinload(Conversation.messages).selectinload(Message.sender),
            selectinload(Conversation.course),
        )
        .where(Conversation.id == conversation_id)
    )
    conv = res.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # Verify participation
    participant_user_ids = [p.user_id for p in conv.participants]
    if current_user.id not in participant_user_ids and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You are not a participant in this conversation.")

    # Update participant last_read_at and mark received messages as read
    now = datetime.utcnow()
    for p in conv.participants:
        if p.user_id == current_user.id:
            p.last_read_at = now

    for m in conv.messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
            m.read_at = now

    await db.commit()

    c_code = conv.course.course_code if conv.course else None
    return ConversationDetailOut(
        id=conv.id,
        subject=conv.subject,
        thread_type=conv.thread_type,
        course_id=conv.course_id,
        course_code=c_code,
        participants=[serialize_participant(p) for p in conv.participants],
        messages=[serialize_message(m) for m in conv.messages],
    )


@router.post("/conversations/{conversation_id}/messages", response_model=DirectMessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: int,
    payload: MessageSendPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a new message in an active conversation thread."""
    res = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.participants))
        .where(Conversation.id == conversation_id)
    )
    conv = res.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    participant_user_ids = [p.user_id for p in conv.participants]
    if current_user.id not in participant_user_ids and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You are not a participant in this conversation.")

    # Determine recipient (other participant in 1-on-1)
    receiver_id = None
    for p in conv.participants:
        if p.user_id != current_user.id:
            receiver_id = p.user_id
            break

    now = datetime.utcnow()
    msg = Message(
        conversation_id=conv.id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=payload.content,
        attachment_url=payload.attachment_url,
        attachment_name=payload.attachment_name,
        is_read=False,
        sent_at=now,
    )
    conv.last_message_at = now
    db.add(msg)

    # Update sender last_read_at
    for p in conv.participants:
        if p.user_id == current_user.id:
            p.last_read_at = now

    await db.commit()
    await db.refresh(msg)

    # Reload message with sender
    m_res = await db.execute(
        select(Message).options(selectinload(Message.sender)).where(Message.id == msg.id)
    )
    return serialize_message(m_res.scalars().first())


@router.post("/conversations/{conversation_id}/read")
async def mark_conversation_read(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all messages in the conversation as read by the current user."""
    res = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.participants), selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conv = res.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    now = datetime.utcnow()
    for p in conv.participants:
        if p.user_id == current_user.id:
            p.last_read_at = now

    for m in conv.messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
            m.read_at = now

    await db.commit()
    return {"success": True, "conversation_id": conversation_id, "read_at": now.isoformat()}


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve total unread message count across all conversations for header badges."""
    # Count messages received by current_user that are unread
    count_res = await db.execute(
        select(func.count(Message.id)).where(
            Message.receiver_id == current_user.id,
            Message.is_read == False,  # noqa: E712
        )
    )
    total_unread = count_res.scalar() or 0
    return {"unread_count": total_unread}


@router.get("/contacts", response_model=List[MessagingContactOut])
async def search_messaging_contacts(
    q: Optional[str] = Query(None, min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search directory of instructors, advisors, and peers for new message thread."""
    query = select(User).where(User.id != current_user.id, User.is_active == True)  # noqa: E712
    if q:
        query = query.where(
            or_(
                User.full_name.ilike(f"%{q}%"),
                User.username.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
            )
        )
    query = query.limit(20)
    res = await db.execute(query)
    users = res.scalars().all()

    contacts: List[MessagingContactOut] = []
    for u in users:
        role_str = u.role.value if hasattr(u.role, "value") else str(u.role)
        ctx = f"Role: {role_str.capitalize()}"
        contacts.append(
            MessagingContactOut(
                user_id=u.id,
                name=u.full_name,
                role=role_str,
                email=u.email,
                context=ctx,
            )
        )
    return contacts
