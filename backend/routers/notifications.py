"""backend/routers/notifications.py
Advanced Enterprise Notification Center Router
Supports category filtering, multi-priority queues, quiet hours,
channel preferences, batch operations, real-time unread statistics,
and role-targeted broadcasts.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func, desc, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User, Notification, NotificationPreference
from backend.schemas import (
    NotificationCreate,
    NotificationBroadcastPayload,
    NotificationBatchAction,
    NotificationOut,
    NotificationPreferenceUpdate,
    NotificationPreferenceOut,
    NotificationStatsOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/notifications", tags=["Notification Center"])


async def get_or_create_preferences(user_id: int, db: AsyncSession) -> NotificationPreference:
    pref_res = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    pref = pref_res.scalars().first()
    if not pref:
        pref = NotificationPreference(
            user_id=user_id,
            email_enabled=True,
            in_app_enabled=True,
            push_enabled=True,
            sms_enabled=False,
            notify_academic=True,
            notify_deadlines=True,
            notify_announcements=True,
            notify_messages=True,
            notify_grades=True,
            quiet_hours_enabled=False,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00",
        )
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return pref


# ─── List & Stats Endpoints ──────────────────────────────────────────────────

@router.get("", response_model=List[NotificationOut])
async def list_notifications(
    category: Optional[str] = Query(None, description="Filter by category (academic, deadline, announcement, system, etc.)"),
    priority: Optional[str] = Query(None, description="Filter by priority (urgent, high, normal, low)"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List authenticated user's notifications with multi-dimensional filtering."""
    filters = [Notification.user_id == current_user.id]

    if category and category.lower() != "all":
        filters.append(Notification.category == category.lower())
    if priority and priority.lower() != "all":
        filters.append(Notification.priority == priority.lower())
    if is_read is not None:
        filters.append(Notification.is_read == is_read)

    query = (
        select(Notification)
        .where(and_(*filters))
        .order_by(
            # Sort urgent first, then date descending
            desc(Notification.priority == "urgent"),
            desc(Notification.created_at),
        )
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    notifications = result.scalars().all()
    return notifications


@router.get("/stats", response_model=NotificationStatsOut)
async def get_notification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve unread notification statistics broken down by category and urgency."""
    # Total count
    tot_res = await db.execute(
        select(func.count(Notification.id)).where(Notification.user_id == current_user.id)
    )
    total_count = tot_res.scalar() or 0

    # Total unread
    unr_res = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    total_unread = unr_res.scalar() or 0

    # Unread breakdown by category
    cat_res = await db.execute(
        select(Notification.category, func.count(Notification.id))
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .group_by(Notification.category)
    )
    unread_by_cat: Dict[str, int] = {cat: count for cat, count in cat_res.all()}

    # Unread breakdown by priority
    prio_res = await db.execute(
        select(Notification.priority, func.count(Notification.id))
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .group_by(Notification.priority)
    )
    unread_by_prio: Dict[str, int] = {prio: count for prio, count in prio_res.all()}

    return NotificationStatsOut(
        total_unread=total_unread,
        total_count=total_count,
        unread_by_category=unread_by_cat,
        unread_by_priority=unread_by_prio,
    )


# ─── Batch & Item Actions ────────────────────────────────────────────────────

@router.post("/batch-action")
async def batch_action(
    payload: NotificationBatchAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perform batch read or deletion on notifications."""
    filters = [Notification.user_id == current_user.id]
    if payload.notification_ids:
        filters.append(Notification.id.in_(payload.notification_ids))

    if payload.action == "mark_read":
        now = datetime.utcnow()
        await db.execute(
            update(Notification)
            .where(and_(*filters))
            .values(is_read=True, read_at=now)
        )
        await db.commit()
        return {"status": "success", "action": "mark_read"}

    elif payload.action == "delete":
        await db.execute(
            delete(Notification).where(and_(*filters))
        )
        await db.commit()
        return {"status": "success", "action": "delete"}

    raise HTTPException(status_code=400, detail="Unsupported batch action.")


@router.post("/batch-read")
async def batch_mark_read(
    payload: Optional[NotificationBatchAction] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all or specific notifications as read."""
    ids = payload.notification_ids if payload else None
    filters = [Notification.user_id == current_user.id, Notification.is_read == False]
    if ids:
        filters.append(Notification.id.in_(ids))

    now = datetime.utcnow()
    await db.execute(
        update(Notification)
        .where(and_(*filters))
        .values(is_read=True, read_at=now)
    )
    await db.commit()
    return {"status": "success", "message": "Notifications marked as read."}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss or delete an individual notification."""
    res = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = res.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    await db.delete(notif)
    await db.commit()
    return {"status": "success", "deleted_id": notification_id}


# ─── Preferences Endpoints ───────────────────────────────────────────────────

@router.get("/preferences", response_model=NotificationPreferenceOut)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve user channel and category preferences."""
    return await get_or_create_preferences(current_user.id, db)


@router.put("/preferences", response_model=NotificationPreferenceOut)
async def update_preferences(
    payload: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user notification delivery channels and category subscriptions."""
    pref = await get_or_create_preferences(current_user.id, db)
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(pref, field, value)

    pref.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(pref)
    return pref


# ─── Creation & Broadcast Endpoints ──────────────────────────────────────────

@router.post("", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a targeted notification for a recipient."""
    # Check recipient exists
    rec_res = await db.execute(select(User).where(User.id == payload.user_id))
    recipient = rec_res.scalars().first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Target user not found.")

    notif = Notification(
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
        notification_type=payload.notification_type,
        category=payload.category,
        priority=payload.priority,
        link=payload.link,
        extra_data=payload.extra_data,
        expires_at=payload.expires_at,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


@router.post("/broadcast", status_code=status.HTTP_201_CREATED)
async def broadcast_notification(
    payload: NotificationBroadcastPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Staff/Admin broadcast announcement to campus members or target role groups."""
    user_query = select(User).where(User.is_active == True)
    if payload.target_role:
        user_query = user_query.where(User.role == payload.target_role)

    users_res = await db.execute(user_query)
    target_users = users_res.scalars().all()

    now = datetime.utcnow()
    new_notifs = [
        Notification(
            user_id=u.id,
            title=payload.title,
            message=payload.message,
            notification_type=payload.notification_type,
            category=payload.category,
            priority=payload.priority,
            link=payload.link,
            is_read=False,
            created_at=now,
        )
        for u in target_users
    ]

    db.add_all(new_notifs)
    await db.commit()

    return {
        "status": "broadcast_sent",
        "recipients_count": len(new_notifs),
        "target_role": payload.target_role or "all",
    }
