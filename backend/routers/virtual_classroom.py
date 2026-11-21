"""
NSBM EduSphere — Virtual Classroom and Live Sessions Router
Provides real-time synchronized virtual lectures, webinar scheduling,
attendance duration analytics, and secure meeting provider integrations
(Zoom, Teams, Google Meet, BigBlueButton) with strict BOLA authorization.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc, update
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Course, Lecturer, Student, Enrollment,
    VirtualClassroomSession, VirtualClassroomAttendance
)
from backend.schemas import (
    VirtualClassroomSessionCreate, VirtualClassroomSessionUpdate,
    VirtualClassroomSessionOut, VirtualClassroomAttendanceRecord,
    VirtualClassroomJoinResponse
)
from backend.utils.security import get_current_user
from backend.core.sanitization import sanitize_rich_content

router = APIRouter(tags=["Virtual Classrooms & Live Sessions"])


async def verify_course_live_session_access(
    course_id: int,
    current_user: User,
    db: AsyncSession
) -> tuple[Course, bool]:
    """
    Validates course existence and confirms that current_user has legitimate
    academic authorization (actively enrolled student, course instructor, or administrator).
    Returns (Course, is_instructor_or_admin).
    """
    q = select(Course).where(Course.id == course_id).options(
        selectinload(Course.lecturer),
        selectinload(Course.enrollments).selectinload(Enrollment.student)
    )
    res = await db.execute(q)
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_instructor = bool(course.lecturer and course.lecturer.user_id == current_user.id)
    is_instructor_or_admin = is_admin or is_instructor

    if is_instructor_or_admin:
        return course, True

    # Validate active student enrollment
    is_enrolled_student = False
    if role_val == UserRole.STUDENT.value:
        for enr in course.enrollments:
            if enr.student and enr.student.user_id == current_user.id:
                if enr.status in {"active", "completed"}:
                    is_enrolled_student = True
                break

    if not is_enrolled_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You must be enrolled in or teaching this course to access virtual classrooms."
        )

    return course, False


# ─── Live Session Endpoints ───────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/live-sessions", response_model=VirtualClassroomSessionOut, status_code=201)
async def create_live_session(
    course_id: int,
    payload: VirtualClassroomSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Schedule a new virtual classroom live session (Instructors & Administrators only)"""
    course, is_instructor_or_admin = await verify_course_live_session_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can schedule live virtual sessions."
        )

    if payload.end_time <= payload.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session end time must be after start time."
        )

    session = VirtualClassroomSession(
        course_id=course_id,
        host_id=current_user.id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        provider=payload.provider.lower().strip(),
        meeting_id=payload.meeting_id.strip() if payload.meeting_id else None,
        join_url=payload.join_url.strip(),
        host_url=payload.host_url.strip() if payload.host_url else None,
        passcode=payload.passcode.strip() if payload.passcode else None,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status="scheduled",
        is_recorded=payload.is_recorded,
        max_participants=payload.max_participants or 100,
        session_settings=payload.session_settings,
    )
    db.add(session)
    await db.commit()

    q = (
        select(VirtualClassroomSession)
        .where(VirtualClassroomSession.id == session.id)
        .options(selectinload(VirtualClassroomSession.host))
    )
    res = await db.execute(q)
    fresh_session = res.scalar_one()

    host_name = fresh_session.host.full_name if fresh_session.host else "Unknown"

    return VirtualClassroomSessionOut(
        id=fresh_session.id,
        course_id=fresh_session.course_id,
        host_id=fresh_session.host_id,
        host_name=host_name,
        title=fresh_session.title,
        description=fresh_session.description,
        provider=fresh_session.provider,
        meeting_id=fresh_session.meeting_id,
        join_url=fresh_session.join_url,
        host_url=fresh_session.host_url,
        passcode=fresh_session.passcode,
        start_time=fresh_session.start_time,
        end_time=fresh_session.end_time,
        status=fresh_session.status,
        recording_url=fresh_session.recording_url,
        recording_duration_minutes=fresh_session.recording_duration_minutes,
        is_recorded=fresh_session.is_recorded,
        max_participants=fresh_session.max_participants,
        session_settings=fresh_session.session_settings,
        participants_count=0,
        created_at=fresh_session.created_at,
        updated_at=fresh_session.updated_at,
    )


@router.get("/api/courses/{course_id}/live-sessions", response_model=List[VirtualClassroomSessionOut])
async def list_course_live_sessions(
    course_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: scheduled, live, concluded, cancelled"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List scheduled and historical virtual sessions for a course"""
    course, is_instructor_or_admin = await verify_course_live_session_access(course_id, current_user, db)

    q = (
        select(VirtualClassroomSession)
        .where(VirtualClassroomSession.course_id == course_id)
        .options(
            selectinload(VirtualClassroomSession.host),
            selectinload(VirtualClassroomSession.attendances),
        )
    )

    if status_filter:
        q = q.where(VirtualClassroomSession.status == status_filter.lower().strip())

    q = q.order_by(VirtualClassroomSession.start_time.asc())
    res = await db.execute(q)
    sessions = res.scalars().all()

    items = []
    for s in sessions:
        host_name = s.host.full_name if s.host else "Unknown"
        items.append(
            VirtualClassroomSessionOut(
                id=s.id,
                course_id=s.course_id,
                host_id=s.host_id,
                host_name=host_name,
                title=s.title,
                description=s.description,
                provider=s.provider,
                meeting_id=s.meeting_id,
                join_url=s.join_url,
                host_url=s.host_url if is_instructor_or_admin else None,
                passcode=s.passcode,
                start_time=s.start_time,
                end_time=s.end_time,
                status=s.status,
                recording_url=s.recording_url,
                recording_duration_minutes=s.recording_duration_minutes,
                is_recorded=s.is_recorded,
                max_participants=s.max_participants,
                session_settings=s.session_settings,
                participants_count=len(s.attendances),
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )
    return items


@router.get("/api/live-sessions/{session_id}", response_model=VirtualClassroomSessionOut)
async def get_live_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a specific live session"""
    q = (
        select(VirtualClassroomSession)
        .where(VirtualClassroomSession.id == session_id)
        .options(
            selectinload(VirtualClassroomSession.host),
            selectinload(VirtualClassroomSession.attendances),
        )
    )
    res = await db.execute(q)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Virtual classroom session not found"
        )

    course, is_instructor_or_admin = await verify_course_live_session_access(session.course_id, current_user, db)
    host_name = session.host.full_name if session.host else "Unknown"

    return VirtualClassroomSessionOut(
        id=session.id,
        course_id=session.course_id,
        host_id=session.host_id,
        host_name=host_name,
        title=session.title,
        description=session.description,
        provider=session.provider,
        meeting_id=session.meeting_id,
        join_url=session.join_url,
        host_url=session.host_url if is_instructor_or_admin else None,
        passcode=session.passcode,
        start_time=session.start_time,
        end_time=session.end_time,
        status=session.status,
        recording_url=session.recording_url,
        recording_duration_minutes=session.recording_duration_minutes,
        is_recorded=session.is_recorded,
        max_participants=session.max_participants,
        session_settings=session.session_settings,
        participants_count=len(session.attendances),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.patch("/api/live-sessions/{session_id}", response_model=VirtualClassroomSessionOut)
async def update_live_session(
    session_id: int,
    payload: VirtualClassroomSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update virtual classroom session details, status, or recording links (Instructors/Admins only)"""
    q = (
        select(VirtualClassroomSession)
        .where(VirtualClassroomSession.id == session_id)
        .options(selectinload(VirtualClassroomSession.host))
    )
    res = await db.execute(q)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Virtual classroom session not found"
        )

    course, is_instructor_or_admin = await verify_course_live_session_access(session.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can modify virtual classroom sessions."
        )

    if payload.title is not None:
        session.title = payload.title.strip()
    if payload.description is not None:
        session.description = payload.description.strip()
    if payload.provider is not None:
        session.provider = payload.provider.lower().strip()
    if payload.meeting_id is not None:
        session.meeting_id = payload.meeting_id.strip()
    if payload.join_url is not None:
        session.join_url = payload.join_url.strip()
    if payload.host_url is not None:
        session.host_url = payload.host_url.strip()
    if payload.passcode is not None:
        session.passcode = payload.passcode.strip()
    if payload.start_time is not None:
        session.start_time = payload.start_time
    if payload.end_time is not None:
        session.end_time = payload.end_time
    if payload.status is not None:
        valid_statuses = {"scheduled", "live", "concluded", "cancelled"}
        if payload.status.lower() not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        session.status = payload.status.lower().strip()
    if payload.recording_url is not None:
        session.recording_url = payload.recording_url.strip()
    if payload.recording_duration_minutes is not None:
        session.recording_duration_minutes = payload.recording_duration_minutes
    if payload.is_recorded is not None:
        session.is_recorded = payload.is_recorded
    if payload.max_participants is not None:
        session.max_participants = payload.max_participants
    if payload.session_settings is not None:
        session.session_settings = payload.session_settings

    await db.commit()

    reload_q = (
        select(VirtualClassroomSession)
        .where(VirtualClassroomSession.id == session_id)
        .options(
            selectinload(VirtualClassroomSession.host),
            selectinload(VirtualClassroomSession.attendances),
        )
    )
    res = await db.execute(reload_q)
    fresh_session = res.scalar_one()

    host_name = fresh_session.host.full_name if fresh_session.host else "Unknown"

    return VirtualClassroomSessionOut(
        id=fresh_session.id,
        course_id=fresh_session.course_id,
        host_id=fresh_session.host_id,
        host_name=host_name,
        title=fresh_session.title,
        description=fresh_session.description,
        provider=fresh_session.provider,
        meeting_id=fresh_session.meeting_id,
        join_url=fresh_session.join_url,
        host_url=fresh_session.host_url,
        passcode=fresh_session.passcode,
        start_time=fresh_session.start_time,
        end_time=fresh_session.end_time,
        status=fresh_session.status,
        recording_url=fresh_session.recording_url,
        recording_duration_minutes=fresh_session.recording_duration_minutes,
        is_recorded=fresh_session.is_recorded,
        max_participants=fresh_session.max_participants,
        session_settings=fresh_session.session_settings,
        participants_count=len(fresh_session.attendances),
        created_at=fresh_session.created_at,
        updated_at=fresh_session.updated_at,
    )


@router.delete("/api/live-sessions/{session_id}", status_code=204)
async def delete_live_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel and remove a virtual classroom session (Instructors/Admins only)"""
    res = await db.execute(select(VirtualClassroomSession).where(VirtualClassroomSession.id == session_id))
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Virtual classroom session not found"
        )

    course, is_instructor_or_admin = await verify_course_live_session_access(session.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can delete virtual classroom sessions."
        )

    await db.delete(session)
    await db.commit()


# ─── Attendance & Participation Tracking ──────────────────────────────────────

@router.post("/api/live-sessions/{session_id}/join", response_model=VirtualClassroomJoinResponse)
async def join_live_session(
    session_id: int,
    device_type: Optional[str] = Query("browser", description="User client device type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record student or instructor entry into the virtual classroom and return connection payload"""
    q = select(VirtualClassroomSession).where(VirtualClassroomSession.id == session_id)
    res = await db.execute(q)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Virtual classroom session not found"
        )

    await verify_course_live_session_access(session.course_id, current_user, db)

    if session.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This virtual classroom session has been cancelled."
        )

    # Find associated student record if applicable
    student_res = await db.execute(select(Student.id).where(Student.user_id == current_user.id))
    student_id = student_res.scalar_one_or_none()

    # Check for existing attendance record
    att_res = await db.execute(
        select(VirtualClassroomAttendance).where(
            VirtualClassroomAttendance.session_id == session_id,
            VirtualClassroomAttendance.user_id == current_user.id,
        )
    )
    attendance = att_res.scalar_one_or_none()

    if not attendance:
        attendance = VirtualClassroomAttendance(
            session_id=session_id,
            user_id=current_user.id,
            student_id=student_id,
            joined_at=datetime.utcnow(),
            left_at=None,
            duration_minutes=0,
            device_type=device_type or "browser",
            attendance_status="present",
        )
        db.add(attendance)
        await db.commit()
        await db.refresh(attendance)
    else:
        # Re-joining: reset left_at if previously left
        attendance.left_at = None
        await db.commit()

    return VirtualClassroomJoinResponse(
        session_id=session.id,
        join_url=session.join_url,
        passcode=session.passcode,
        provider=session.provider,
        status=session.status,
        attendance_id=attendance.id,
        joined_at=attendance.joined_at,
    )


@router.post("/api/live-sessions/{session_id}/leave", response_model=VirtualClassroomAttendanceRecord)
async def leave_live_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record student departure from virtual session and compute participation duration"""
    q = (
        select(VirtualClassroomAttendance)
        .where(
            VirtualClassroomAttendance.session_id == session_id,
            VirtualClassroomAttendance.user_id == current_user.id,
        )
        .options(selectinload(VirtualClassroomAttendance.user))
    )
    res = await db.execute(q)
    attendance = res.scalar_one_or_none()
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active attendance record found for this session."
        )

    leave_time = datetime.utcnow()
    attendance.left_at = leave_time

    # Calculate duration
    if attendance.joined_at:
        delta = leave_time - attendance.joined_at
        attendance.duration_minutes = max(1, int(delta.total_seconds() // 60))

    await db.commit()

    participant_name = attendance.user.full_name if attendance.user else "Unknown"

    return VirtualClassroomAttendanceRecord(
        id=attendance.id,
        session_id=attendance.session_id,
        user_id=attendance.user_id,
        student_id=attendance.student_id,
        participant_name=participant_name,
        joined_at=attendance.joined_at,
        left_at=attendance.left_at,
        duration_minutes=attendance.duration_minutes,
        device_type=attendance.device_type,
        attendance_status=attendance.attendance_status,
        created_at=attendance.created_at,
    )


@router.get("/api/live-sessions/{session_id}/attendance", response_model=List[VirtualClassroomAttendanceRecord])
async def get_live_session_attendance(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full attendance and engagement roster for a virtual session (Instructors/Admins only)"""
    q = select(VirtualClassroomSession.course_id).where(VirtualClassroomSession.id == session_id)
    res = await db.execute(q)
    course_id = res.scalar_one_or_none()
    if course_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Virtual classroom session not found"
        )

    course, is_instructor_or_admin = await verify_course_live_session_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can inspect session attendance."
        )

    att_q = (
        select(VirtualClassroomAttendance)
        .where(VirtualClassroomAttendance.session_id == session_id)
        .options(selectinload(VirtualClassroomAttendance.user))
        .order_by(VirtualClassroomAttendance.joined_at.asc())
    )
    att_res = await db.execute(att_q)
    records = att_res.scalars().all()

    return [
        VirtualClassroomAttendanceRecord(
            id=r.id,
            session_id=r.session_id,
            user_id=r.user_id,
            student_id=r.student_id,
            participant_name=r.user.full_name if r.user else "Unknown",
            joined_at=r.joined_at,
            left_at=r.left_at,
            duration_minutes=r.duration_minutes,
            device_type=r.device_type,
            attendance_status=r.attendance_status,
            created_at=r.created_at,
        )
        for r in records
    ]
