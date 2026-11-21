"""backend/routers/collaboration.py
Enterprise Student Collaboration Spaces Router
Provides project group workspaces, collaborative scratchpad/whiteboards,
shared documents/code snippets, persistent chat discussions, and quick-join PIN codes.
"""

import secrets
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
    Course,
    Enrollment,
    CollaborationWorkspace,
    CollaborationWorkspaceMember,
    CollaborationWorkspaceAsset,
    CollaborationWorkspaceMessage,
)
from backend.schemas import (
    CollaborationWorkspaceCreate,
    CollaborationWorkspaceJoinPayload,
    CollaborationWorkspaceMemberOut,
    CollaborationWorkspaceAssetCreate,
    CollaborationWorkspaceAssetOut,
    CollaborationWorkspaceMessageCreate,
    CollaborationWorkspaceMessageOut,
    CollaborationWorkspaceWhiteboardUpdate,
    CollaborationWorkspaceOut,
    CollaborationWorkspaceDetailOut,
)
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/collaboration", tags=["Collaboration Spaces"])


def generate_join_code() -> str:
    return secrets.token_hex(4).upper()


def serialize_member(m: CollaborationWorkspaceMember) -> CollaborationWorkspaceMemberOut:
    name = m.student.user.full_name if (m.student and m.student.user) else "Student"
    reg_id = m.student.student_id if m.student else None
    return CollaborationWorkspaceMemberOut(
        id=m.id,
        student_id=m.student_id,
        student_name=name,
        student_reg_id=reg_id,
        role=m.role,
        joined_at=m.joined_at,
    )


def serialize_asset(a: CollaborationWorkspaceAsset) -> CollaborationWorkspaceAssetOut:
    author = a.created_by.user.full_name if (a.created_by and a.created_by.user) else "Student"
    return CollaborationWorkspaceAssetOut(
        id=a.id,
        workspace_id=a.workspace_id,
        created_by_student_id=a.created_by_student_id,
        author_name=author,
        title=a.title,
        asset_type=a.asset_type,
        content=a.content,
        version=a.version,
        created_at=a.created_at,
    )


def serialize_message(msg: CollaborationWorkspaceMessage) -> CollaborationWorkspaceMessageOut:
    sender = msg.sender.user.full_name if (msg.sender and msg.sender.user) else "Student"
    return CollaborationWorkspaceMessageOut(
        id=msg.id,
        workspace_id=msg.workspace_id,
        sender_student_id=msg.sender_student_id,
        sender_name=sender,
        content=msg.content,
        pinned=msg.pinned,
        created_at=msg.created_at,
    )


def serialize_workspace(
    w: CollaborationWorkspace,
    members_count: Optional[int] = None,
    assets_count: Optional[int] = None,
) -> CollaborationWorkspaceOut:
    course_code = w.course.course_code if w.course else None
    owner_name = w.owner.user.full_name if (w.owner and w.owner.user) else "Student"
    m_cnt = members_count if members_count is not None else (len(w.members) if getattr(w, "members", None) else 0)
    a_cnt = assets_count if assets_count is not None else (len(w.assets) if getattr(w, "assets", None) else 0)
    return CollaborationWorkspaceOut(
        id=w.id,
        course_id=w.course_id,
        course_code=course_code,
        name=w.name,
        description=w.description,
        topic=w.topic,
        visibility=w.visibility,
        owner_student_id=w.owner_student_id,
        owner_name=owner_name,
        join_code=w.join_code,
        shared_whiteboard_data=w.shared_whiteboard_data,
        meeting_link=w.meeting_link,
        status=w.status,
        members_count=m_cnt,
        assets_count=a_cnt,
        created_at=w.created_at,
    )


# ─── Workspace Endpoints ──────────────────────────────────────────────────────

@router.post("/workspaces", response_model=CollaborationWorkspaceOut, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: CollaborationWorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student creates a new collaborative study circle or project workspace."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can create collaboration workspaces.")

    if payload.course_id:
        c_res = await db.execute(select(Course).where(Course.id == payload.course_id))
        if not c_res.scalars().first():
            raise HTTPException(status_code=404, detail="Course not found.")

    code = generate_join_code()
    workspace = CollaborationWorkspace(
        course_id=payload.course_id,
        name=payload.name,
        description=payload.description,
        topic=payload.topic,
        visibility=payload.visibility,
        owner_student_id=student.id,
        join_code=code,
        shared_whiteboard_data={"nodes": [], "notes": []},
        meeting_link=payload.meeting_link,
        status="active",
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    # Automatically add creator as owner member
    owner_member = CollaborationWorkspaceMember(
        workspace_id=workspace.id,
        student_id=student.id,
        role="owner",
    )
    db.add(owner_member)
    await db.commit()

    # Reload with relationships
    res = await db.execute(
        select(CollaborationWorkspace)
        .options(
            selectinload(CollaborationWorkspace.course),
            selectinload(CollaborationWorkspace.owner).selectinload(Student.user),
            selectinload(CollaborationWorkspace.members),
            selectinload(CollaborationWorkspace.assets),
        )
        .where(CollaborationWorkspace.id == workspace.id)
    )
    return serialize_workspace(res.scalars().first())


@router.get("/workspaces", response_model=List[CollaborationWorkspaceOut])
async def list_workspaces(
    course_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all workspaces where the current user is a member, plus discoverable public workspaces."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    student_id = student.id if student else -1

    # Find workspaces where student is a member
    mem_res = await db.execute(
        select(CollaborationWorkspaceMember.workspace_id).where(
            CollaborationWorkspaceMember.student_id == student_id
        )
    )
    my_workspace_ids = [r[0] for r in mem_res.all()]

    query = (
        select(CollaborationWorkspace)
        .options(
            selectinload(CollaborationWorkspace.course),
            selectinload(CollaborationWorkspace.owner).selectinload(Student.user),
            selectinload(CollaborationWorkspace.members),
            selectinload(CollaborationWorkspace.assets),
        )
        .where(
            or_(
                CollaborationWorkspace.id.in_(my_workspace_ids),
                and_(
                    CollaborationWorkspace.visibility == "course_public",
                    CollaborationWorkspace.status == "active",
                ),
            )
        )
    )

    if course_id:
        query = query.where(CollaborationWorkspace.course_id == course_id)

    query = query.order_by(desc(CollaborationWorkspace.created_at))
    res = await db.execute(query)
    workspaces = res.scalars().all()
    return [serialize_workspace(w) for w in workspaces]


@router.get("/workspaces/{workspace_id}", response_model=CollaborationWorkspaceDetailOut)
async def get_workspace_details(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full details of a collaboration space including members, assets, and discussion."""
    res = await db.execute(
        select(CollaborationWorkspace)
        .options(
            selectinload(CollaborationWorkspace.course),
            selectinload(CollaborationWorkspace.owner).selectinload(Student.user),
            selectinload(CollaborationWorkspace.members).selectinload(CollaborationWorkspaceMember.student).selectinload(Student.user),
            selectinload(CollaborationWorkspace.assets).selectinload(CollaborationWorkspaceAsset.created_by).selectinload(Student.user),
            selectinload(CollaborationWorkspace.messages).selectinload(CollaborationWorkspaceMessage.sender).selectinload(Student.user),
        )
        .where(CollaborationWorkspace.id == workspace_id)
    )
    w = res.scalars().first()
    if not w:
        raise HTTPException(status_code=404, detail="Collaboration workspace not found.")

    base_out = serialize_workspace(w)
    return CollaborationWorkspaceDetailOut(
        **base_out.model_dump(),
        members=[serialize_member(m) for m in w.members],
        assets=[serialize_asset(a) for a in w.assets],
        recent_messages=[serialize_message(msg) for msg in w.messages],
    )


@router.post("/workspaces/join", response_model=CollaborationWorkspaceOut)
async def join_workspace_by_code(
    payload: CollaborationWorkspaceJoinPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Join an active workspace via its unique 8-character invite code."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can join collaboration workspaces.")

    res = await db.execute(
        select(CollaborationWorkspace)
        .options(
            selectinload(CollaborationWorkspace.course),
            selectinload(CollaborationWorkspace.owner).selectinload(Student.user),
            selectinload(CollaborationWorkspace.members),
            selectinload(CollaborationWorkspace.assets),
        )
        .where(CollaborationWorkspace.join_code == payload.join_code.strip().upper())
    )
    workspace = res.scalars().first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Invalid workspace invite code.")

    # Check if already a member
    mem_check = await db.execute(
        select(CollaborationWorkspaceMember).where(
            CollaborationWorkspaceMember.workspace_id == workspace.id,
            CollaborationWorkspaceMember.student_id == student.id,
        )
    )
    if not mem_check.scalars().first():
        new_member = CollaborationWorkspaceMember(
            workspace_id=workspace.id,
            student_id=student.id,
            role="collaborator",
        )
        db.add(new_member)
        await db.commit()

    m_cnt = await db.scalar(
        select(func.count(CollaborationWorkspaceMember.id)).where(
            CollaborationWorkspaceMember.workspace_id == workspace.id
        )
    )
    a_cnt = await db.scalar(
        select(func.count(CollaborationWorkspaceAsset.id)).where(
            CollaborationWorkspaceAsset.workspace_id == workspace.id
        )
    )
    return serialize_workspace(workspace, members_count=m_cnt or 0, assets_count=a_cnt or 0)


# ─── Shared Workspace Assets & Whiteboard ────────────────────────────────────

@router.post("/workspaces/{workspace_id}/assets", response_model=CollaborationWorkspaceAssetOut, status_code=status.HTTP_201_CREATED)
async def create_workspace_asset(
    workspace_id: int,
    payload: CollaborationWorkspaceAssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a shared document, code snippet, note, or reference link to the workspace."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    student_id = student.id if student else None

    # Check workspace exists
    w_res = await db.execute(select(CollaborationWorkspace).where(CollaborationWorkspace.id == workspace_id))
    if not w_res.scalars().first():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    asset = CollaborationWorkspaceAsset(
        workspace_id=workspace_id,
        created_by_student_id=student_id,
        title=payload.title,
        asset_type=payload.asset_type,
        content=payload.content,
        version=1,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    a_res = await db.execute(
        select(CollaborationWorkspaceAsset)
        .options(selectinload(CollaborationWorkspaceAsset.created_by).selectinload(Student.user))
        .where(CollaborationWorkspaceAsset.id == asset.id)
    )
    return serialize_asset(a_res.scalars().first())


@router.put("/workspaces/{workspace_id}/whiteboard")
async def update_workspace_whiteboard(
    workspace_id: int,
    payload: CollaborationWorkspaceWhiteboardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update collaborative whiteboard/scratchpad canvas state."""
    w_res = await db.execute(select(CollaborationWorkspace).where(CollaborationWorkspace.id == workspace_id))
    workspace = w_res.scalars().first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    workspace.shared_whiteboard_data = payload.whiteboard_data
    workspace.updated_at = datetime.utcnow()
    await db.commit()
    return {"success": True, "message": "Whiteboard updated", "workspace_id": workspace_id}


# ─── Discussion Messages ─────────────────────────────────────────────────────

@router.post("/workspaces/{workspace_id}/messages", response_model=CollaborationWorkspaceMessageOut, status_code=status.HTTP_201_CREATED)
async def post_workspace_message(
    workspace_id: int,
    payload: CollaborationWorkspaceMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Post a team discussion message in the collaboration workspace."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can post in collaboration workspaces.")

    w_res = await db.execute(select(CollaborationWorkspace).where(CollaborationWorkspace.id == workspace_id))
    if not w_res.scalars().first():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    msg = CollaborationWorkspaceMessage(
        workspace_id=workspace_id,
        sender_student_id=student.id,
        content=payload.content,
        pinned=payload.pinned,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    m_res = await db.execute(
        select(CollaborationWorkspaceMessage)
        .options(selectinload(CollaborationWorkspaceMessage.sender).selectinload(Student.user))
        .where(CollaborationWorkspaceMessage.id == msg.id)
    )
    return serialize_message(m_res.scalars().first())
