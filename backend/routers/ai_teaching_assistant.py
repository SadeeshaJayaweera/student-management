"""
NSBM EduSphere — Conversational AI Teaching Assistant Router
Provides endpoints for Socratic AI tutoring sessions, multi-turn dialogs,
syllabus boundary guardrails, progressive hints, and session history.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import User, Student
from backend.schemas import (
    AITeachingSessionCreate,
    AITeachingSessionOut,
    AITeachingSessionDetailOut,
    AITeachingMessageCreate,
    AITeachingMessageOut,
)
from backend.services.ai_teaching_service import ai_teaching_service
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/ai/teaching", tags=["Conversational AI Teaching Assistant"])


async def _resolve_student_id(db: AsyncSession, current_user: User) -> int:
    """Resolve student ID for current user, with fallback for faculty/admin preview"""
    res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    stu = res.scalar_one_or_none()
    if stu:
        return stu.id
    if current_user.role in ["admin", "lecturer"]:
        any_stu_res = await db.execute(select(Student))
        first_stu = any_stu_res.scalars().first()
        if first_stu:
            return first_stu.id
    raise HTTPException(status_code=400, detail="Active student profile required for tutoring sessions")


@router.post("/sessions", response_model=AITeachingSessionOut, status_code=status.HTTP_201_CREATED)
async def create_teaching_session(
    payload: AITeachingSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversational teaching session with initial Socratic greeting"""
    student_id = await _resolve_student_id(db, current_user)
    try:
        session = await ai_teaching_service.create_session(
            db=db,
            student_id=student_id,
            course_id=payload.course_id,
            title=payload.title,
            teaching_mode=payload.teaching_mode
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=List[AITeachingSessionOut])
async def list_teaching_sessions(
    course_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List active teaching sessions for the current student"""
    student_id = await _resolve_student_id(db, current_user)
    sessions = await ai_teaching_service.get_student_sessions(db, student_id, course_id=course_id)
    return sessions


@router.get("/sessions/{session_id}", response_model=AITeachingSessionDetailOut)
async def get_teaching_session_details(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete chronological chat history and metadata for a session"""
    student_id = await _resolve_student_id(db, current_user)
    try:
        session = await ai_teaching_service.get_session_details(db, session_id, student_id)
        return session
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sessions/{session_id}/chat", response_model=AITeachingMessageOut)
async def chat_with_teaching_assistant(
    session_id: int,
    payload: AITeachingMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send student inquiry and receive Socratic response, scaffolding hints, or guardrail redirection"""
    student_id = await _resolve_student_id(db, current_user)
    try:
        res = await ai_teaching_service.process_student_turn(
            db=db,
            session_id=session_id,
            student_id=student_id,
            content=payload.content
        )
        return res["assistant_message"]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sessions/{session_id}/archive", response_model=AITeachingSessionOut)
async def archive_teaching_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive an existing tutoring session"""
    student_id = await _resolve_student_id(db, current_user)
    try:
        session = await ai_teaching_service.archive_session(db, session_id, student_id)
        return session
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
