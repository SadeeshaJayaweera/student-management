"""
NSBM EduSphere — Timed Examinations and Proctoring Controls Router
Provides countdown enforcement, heartbeat keep-alive, client browser integrity monitoring,
tab-switch / fullscreen violation tracking, and real-time live instructor invigilation.
"""
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Course, Student, Lecturer,
    Quiz, QuizAttempt, ExamProctoringSession, ExamProctoringEvent
)
from backend.schemas import (
    ProctoringSessionStart, ProctoringSessionOut,
    ProctoringEventCreate, ProctoringEventOut, ProctoringHeartbeatOut
)
from backend.utils.security import get_current_user
from backend.routers.assignments import verify_course_assignment_access

router = APIRouter(tags=["Timed Examinations & Proctoring"])


def serialize_proctoring_session(
    session: ExamProctoringSession,
    events: Optional[List[ExamProctoringEvent]] = None
) -> ProctoringSessionOut:
    now = datetime.utcnow()
    remaining = max(0.0, (session.expires_at - now).total_seconds())

    source_events = events if events is not None else (session.events or [])
    events_out = [
        ProctoringEventOut(
            id=ev.id,
            session_id=ev.session_id,
            event_type=ev.event_type,
            severity=ev.severity,
            details=ev.details,
            timestamp=ev.timestamp,
        )
        for ev in source_events
    ]

    return ProctoringSessionOut(
        id=session.id,
        quiz_id=session.quiz_id,
        student_id=session.student_id,
        attempt_id=session.attempt_id,
        session_token=session.session_token,
        started_at=session.started_at,
        expires_at=session.expires_at,
        last_heartbeat_at=session.last_heartbeat_at,
        status=session.status,
        tab_switch_count=session.tab_switch_count,
        fullscreen_exit_count=session.fullscreen_exit_count,
        copy_paste_attempt_count=session.copy_paste_attempt_count,
        is_flagged=session.is_flagged,
        flag_reason=session.flag_reason,
        remaining_seconds=remaining,
        created_at=session.created_at,
        events=events_out,
    )


# ─── Student Proctoring Session Endpoints ─────────────────────────────────────

@router.post("/api/exams/{quiz_id}/proctoring/start", response_model=ProctoringSessionOut, status_code=201)
async def start_proctoring_session(
    quiz_id: int,
    payload: ProctoringSessionStart,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initialize a secure timed exam proctoring session with browser telemetry tracking"""
    res_student = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = res_student.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only registered students can initiate proctoring sessions."
        )

    res_quiz = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = res_quiz.scalar_one_or_none()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz/Exam not found"
        )

    await verify_course_assignment_access(quiz.course_id, current_user, db)

    now = datetime.utcnow()
    duration_minutes = quiz.time_limit_minutes or 60
    expires_at = now + timedelta(minutes=duration_minutes)

    token = f"NSBM-PROC-{uuid.uuid4().hex}"

    session = ExamProctoringSession(
        quiz_id=quiz_id,
        student_id=student.id,
        attempt_id=payload.attempt_id,
        session_token=token,
        ip_address=payload.ip_address,
        user_agent=payload.user_agent,
        started_at=now,
        expires_at=expires_at,
        last_heartbeat_at=now,
        status="active",
        tab_switch_count=0,
        fullscreen_exit_count=0,
        copy_paste_attempt_count=0,
        is_flagged=False,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return serialize_proctoring_session(session, events=[])


@router.post("/api/proctoring/{session_token}/heartbeat", response_model=ProctoringHeartbeatOut)
async def send_proctoring_heartbeat(
    session_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Keep-alive heartbeat validating examination countdown and detecting session expiry"""
    res = await db.execute(
        select(ExamProctoringSession).where(ExamProctoringSession.session_token == session_token)
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found"
        )

    now = datetime.utcnow()
    remaining = (session.expires_at - now).total_seconds()

    if remaining <= 0:
        session.status = "auto_submitted"
        remaining = 0.0
    else:
        session.last_heartbeat_at = now

    await db.commit()

    return ProctoringHeartbeatOut(
        status=session.status,
        remaining_seconds=remaining,
        is_flagged=session.is_flagged,
        tab_switch_count=session.tab_switch_count,
        fullscreen_exit_count=session.fullscreen_exit_count,
        server_time=now,
    )


@router.post("/api/proctoring/{session_token}/events", response_model=ProctoringEventOut, status_code=201)
async def record_proctoring_event(
    session_token: str,
    payload: ProctoringEventCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Log client-side security event (tab switch, fullscreen loss, copy-paste, devtools).
    Evaluates violation thresholds and flags the session automatically.
    """
    res = await db.execute(
        select(ExamProctoringSession).where(ExamProctoringSession.session_token == session_token)
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found"
        )

    event_type = payload.event_type.lower().strip()
    if event_type == "tab_switch":
        session.tab_switch_count += 1
    elif event_type == "fullscreen_exit":
        session.fullscreen_exit_count += 1
    elif event_type == "copy_paste_blocked":
        session.copy_paste_attempt_count += 1

    # Security Threshold Evaluation
    if session.tab_switch_count >= 3 or session.fullscreen_exit_count >= 2:
        session.is_flagged = True
        session.flag_reason = (
            f"Suspicious activity threshold exceeded: {session.tab_switch_count} tab switches, "
            f"{session.fullscreen_exit_count} fullscreen exits."
        )

    event = ExamProctoringEvent(
        session_id=session.id,
        event_type=event_type,
        severity=payload.severity,
        details=payload.details,
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return ProctoringEventOut(
        id=event.id,
        session_id=event.session_id,
        event_type=event.event_type,
        severity=event.severity,
        details=event.details,
        timestamp=event.timestamp,
    )


@router.get("/api/proctoring/{session_token}/status", response_model=ProctoringSessionOut)
async def get_proctoring_session_status(
    session_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve proctoring session countdown, telemetry flags, and logged events"""
    res = await db.execute(
        select(ExamProctoringSession)
        .where(ExamProctoringSession.session_token == session_token)
        .options(selectinload(ExamProctoringSession.events))
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found"
        )

    return serialize_proctoring_session(session)


# ─── Instructor Live Monitoring & Invigilation Endpoints ──────────────────────

@router.get("/api/exams/{quiz_id}/proctoring/live", response_model=List[ProctoringSessionOut])
async def live_proctoring_dashboard(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Real-time live monitoring dashboard of all active examinees (Instructors/Admins only)"""
    res_quiz = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = res_quiz.scalar_one_or_none()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz/Exam not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(quiz.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can access live proctoring."
        )

    q = (
        select(ExamProctoringSession)
        .where(ExamProctoringSession.quiz_id == quiz_id)
        .options(selectinload(ExamProctoringSession.events))
        .order_by(desc(ExamProctoringSession.is_flagged), ExamProctoringSession.started_at.desc())
    )
    res = await db.execute(q)
    sessions = res.scalars().all()

    return [serialize_proctoring_session(s) for s in sessions]


@router.post("/api/exams/{quiz_id}/proctoring/{session_id}/terminate", response_model=ProctoringSessionOut)
async def terminate_exam_session(
    quiz_id: int,
    session_id: int,
    reason: str = Query("Forced termination by instructor due to proctoring policy violation"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Forcibly terminate a student's examination session (Instructors/Admins only)"""
    res_quiz = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = res_quiz.scalar_one_or_none()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz/Exam not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(quiz.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can terminate exam sessions."
        )

    res_session = await db.execute(
        select(ExamProctoringSession)
        .where(ExamProctoringSession.id == session_id, ExamProctoringSession.quiz_id == quiz_id)
        .options(selectinload(ExamProctoringSession.events))
    )
    session = res_session.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found"
        )

    session.status = "terminated"
    session.is_flagged = True
    session.flag_reason = reason

    # Log termination event
    event = ExamProctoringEvent(
        session_id=session.id,
        event_type="instructor_terminated",
        severity="critical",
        details={"terminated_by": current_user.email, "reason": reason},
        timestamp=datetime.utcnow(),
    )
    db.add(event)

    await db.commit()
    await db.refresh(session)

    ev_res = await db.execute(
        select(ExamProctoringEvent)
        .where(ExamProctoringEvent.session_id == session.id)
        .order_by(desc(ExamProctoringEvent.timestamp))
    )
    events_list = ev_res.scalars().all()

    return serialize_proctoring_session(session, events=events_list)
