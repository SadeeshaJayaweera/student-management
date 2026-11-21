"""backend/routers/attendance_management.py
Enterprise Attendance and Participation Management Router
Features session generation, self-check-in PIN codes, batch roster marking,
participation scoring, student excuse/correction workflows, and threshold policy tracking.
"""

import random
import string
from datetime import datetime, date, timedelta
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
    Enrollment,
    Attendance,
    AttendanceStatus,
    AttendanceSession,
    AttendanceCorrectionRequest,
    TimetableSlot,
)
from backend.schemas import (
    AttendanceSessionCreate,
    AttendanceSessionOut,
    AttendanceCheckinPayload,
    AttendanceBatchRosterPayload,
    AttendanceRecordDetail,
    AttendanceCorrectionCreate,
    AttendanceCorrectionResolve,
    AttendanceCorrectionOut,
    CourseAttendanceSummary,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/attendance", tags=["Attendance & Participation"])


def generate_checkin_code(length: int = 6) -> str:
    """Generate a clean numeric check-in PIN code."""
    return "".join(random.choices(string.digits, k=length))


# ─── Attendance Session Endpoints ─────────────────────────────────────────────

@router.post("/sessions", response_model=AttendanceSessionOut, status_code=status.HTTP_201_CREATED)
async def create_attendance_session(
    payload: AttendanceSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer", "admin")),
):
    """Lecturer or Admin creates a new class attendance session with auto-generated checkin code."""
    c_res = await db.execute(select(Course).where(Course.id == payload.course_id))
    course = c_res.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    checkin_code = None
    code_expires_at = None
    if payload.allow_self_checkin:
        checkin_code = generate_checkin_code(6)
        code_expires_at = datetime.utcnow() + timedelta(minutes=payload.code_valid_minutes)

    session = AttendanceSession(
        course_id=payload.course_id,
        timetable_slot_id=payload.timetable_slot_id,
        session_title=payload.session_title,
        session_date=payload.session_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        checkin_code=checkin_code,
        code_expires_at=code_expires_at,
        status="open",
        allow_self_checkin=payload.allow_self_checkin,
        created_by_id=current_user.id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return AttendanceSessionOut(
        id=session.id,
        course_id=course.id,
        course_code=course.course_code,
        course_title=course.title,
        session_title=session.session_title,
        session_date=session.session_date,
        start_time=session.start_time,
        end_time=session.end_time,
        checkin_code=session.checkin_code,
        code_expires_at=session.code_expires_at,
        status=session.status,
        allow_self_checkin=session.allow_self_checkin,
        attendances_count=0,
        created_at=session.created_at,
    )


@router.get("/sessions/{course_id}", response_model=List[AttendanceSessionOut])
async def list_course_attendance_sessions(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List attendance sessions for a course."""
    c_res = await db.execute(select(Course).where(Course.id == course_id))
    course = c_res.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    res = await db.execute(
        select(AttendanceSession)
        .options(selectinload(AttendanceSession.attendances))
        .where(AttendanceSession.course_id == course_id)
        .order_by(desc(AttendanceSession.session_date), desc(AttendanceSession.start_time))
    )
    sessions = res.scalars().all()

    out: List[AttendanceSessionOut] = []
    for s in sessions:
        out.append(
            AttendanceSessionOut(
                id=s.id,
                course_id=course.id,
                course_code=course.course_code,
                course_title=course.title,
                session_title=s.session_title,
                session_date=s.session_date,
                start_time=s.start_time,
                end_time=s.end_time,
                checkin_code=s.checkin_code if current_user.role != "student" else None,
                code_expires_at=s.code_expires_at,
                status=s.status,
                allow_self_checkin=s.allow_self_checkin,
                attendances_count=len(s.attendances),
                created_at=s.created_at,
            )
        )
    return out


@router.post("/sessions/{session_id}/checkin")
async def student_self_checkin(
    session_id: int,
    payload: AttendanceCheckinPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enrolled student verifies 6-digit session PIN and checks in for class."""
    # Find student profile
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can check in to attendance sessions.")

    # Find session
    sess_res = await db.execute(select(AttendanceSession).where(AttendanceSession.id == session_id))
    session = sess_res.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Attendance session not found.")

    if session.status != "open":
        raise HTTPException(status_code=400, detail="This attendance session is closed.")

    if not session.allow_self_checkin or not session.checkin_code:
        raise HTTPException(status_code=400, detail="Self check-in is not enabled for this session.")

    # Verify code
    if session.checkin_code.strip() != payload.checkin_code.strip():
        raise HTTPException(status_code=400, detail="Invalid check-in code. Please verify with instructor.")

    # Verify code expiry
    if session.code_expires_at and datetime.utcnow() > session.code_expires_at:
        raise HTTPException(status_code=400, detail="The check-in code for this session has expired.")

    # Verify enrollment in course
    enr_res = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.course_id == session.course_id,
            Enrollment.status.in_(["enrolled", "active", "completed"]),
        )
    )
    if not enr_res.scalars().first():
        raise HTTPException(status_code=403, detail="You are not enrolled in this course.")

    # Check if attendance already logged for this session
    att_res = await db.execute(
        select(Attendance).where(
            Attendance.student_id == student.id,
            Attendance.course_id == session.course_id,
            Attendance.session_id == session.id,
        )
    )
    existing_att = att_res.scalars().first()
    if existing_att:
        existing_att.status = AttendanceStatus.PRESENT
        existing_att.checkin_method = "code"
        existing_att.checked_in_at = datetime.utcnow()
        existing_att.participation_score = max(existing_att.participation_score, 10.0)
    else:
        new_att = Attendance(
            student_id=student.id,
            course_id=session.course_id,
            session_id=session.id,
            date=session.session_date,
            status=AttendanceStatus.PRESENT,
            checkin_method="code",
            checked_in_at=datetime.utcnow(),
            participation_score=10.0,
            notes="Student self-checked in with PIN",
        )
        db.add(new_att)

    await db.commit()
    return {
        "success": True,
        "message": f"Successfully checked in for '{session.session_title}'",
        "session_id": session.id,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─── Lecturer Batch Roster & Participation Scoring ───────────────────────────

@router.post("/sessions/{session_id}/roster")
async def batch_mark_roster(
    session_id: int,
    payload: AttendanceBatchRosterPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer", "admin")),
):
    """Lecturer batch records or updates attendance and participation scores for all students."""
    sess_res = await db.execute(select(AttendanceSession).where(AttendanceSession.id == session_id))
    session = sess_res.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Attendance session not found.")

    status_map = {
        "present": AttendanceStatus.PRESENT,
        "absent": AttendanceStatus.ABSENT,
        "late": AttendanceStatus.LATE,
        "excused": AttendanceStatus.EXCUSED,
    }

    count = 0
    for item in payload.items:
        stat_enum = status_map.get(item.status.lower(), AttendanceStatus.PRESENT)
        # Check existing record for this student and session
        att_res = await db.execute(
            select(Attendance).where(
                Attendance.student_id == item.student_id,
                Attendance.course_id == session.course_id,
                Attendance.session_id == session.id,
            )
        )
        existing = att_res.scalars().first()
        if existing:
            existing.status = stat_enum
            existing.participation_score = item.participation_score
            if item.notes:
                existing.notes = item.notes
        else:
            rec = Attendance(
                student_id=item.student_id,
                course_id=session.course_id,
                session_id=session.id,
                date=session.session_date,
                status=stat_enum,
                checkin_method="manual",
                checked_in_at=datetime.utcnow(),
                participation_score=item.participation_score,
                notes=item.notes or "Instructor marked",
            )
            db.add(rec)
        count += 1

    await db.commit()
    return {"success": True, "updated_count": count, "session_id": session_id}


@router.get("/sessions/{session_id}/roster", response_model=List[AttendanceRecordDetail])
async def get_session_roster(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer", "admin")),
):
    """Retrieve all enrolled students with their check-in and participation records for a session."""
    sess_res = await db.execute(select(AttendanceSession).where(AttendanceSession.id == session_id))
    session = sess_res.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Attendance session not found.")

    # Fetch all enrolled students
    enr_res = await db.execute(
        select(Enrollment)
        .options(selectinload(Enrollment.student).selectinload(Student.user))
        .where(
            Enrollment.course_id == session.course_id,
            Enrollment.status.in_(["enrolled", "active", "completed"]),
        )
    )
    enrollments = enr_res.scalars().all()

    # Fetch recorded attendances
    att_res = await db.execute(
        select(Attendance).where(
            Attendance.course_id == session.course_id,
            Attendance.session_id == session.id,
        )
    )
    attendances_by_student = {a.student_id: a for a in att_res.scalars().all()}

    roster: List[AttendanceRecordDetail] = []
    for enr in enrollments:
        stu = enr.student
        if not stu:
            continue
        rec = attendances_by_student.get(stu.id)
        if rec:
            stat_str = rec.status.value if hasattr(rec.status, "value") else str(rec.status)
            roster.append(
                AttendanceRecordDetail(
                    id=rec.id,
                    student_id=stu.id,
                    student_reg_id=stu.student_id,
                    student_name=stu.user.full_name if stu.user else "Student",
                    session_id=session.id,
                    date=rec.date,
                    status=stat_str,
                    checkin_method=rec.checkin_method,
                    checked_in_at=rec.checked_in_at,
                    participation_score=rec.participation_score,
                    notes=rec.notes,
                    remarks=rec.remarks,
                )
            )
        else:
            roster.append(
                AttendanceRecordDetail(
                    id=0,
                    student_id=stu.id,
                    student_reg_id=stu.student_id,
                    student_name=stu.user.full_name if stu.user else "Student",
                    session_id=session.id,
                    date=session.session_date,
                    status="unmarked",
                    checkin_method="none",
                    checked_in_at=None,
                    participation_score=0.0,
                    notes=None,
                    remarks=None,
                )
            )

    return roster


# ─── Attendance Correction & Excuse Workflows ─────────────────────────────────

@router.post("/corrections", response_model=AttendanceCorrectionOut, status_code=status.HTTP_201_CREATED)
async def submit_attendance_correction(
    payload: AttendanceCorrectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student submits an absence excuse or attendance correction request with supporting evidence."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can submit attendance correction requests.")

    c_res = await db.execute(select(Course).where(Course.id == payload.course_id))
    course = c_res.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    corr = AttendanceCorrectionRequest(
        student_id=student.id,
        course_id=payload.course_id,
        session_id=payload.session_id,
        attendance_date=payload.attendance_date,
        requested_status=payload.requested_status,
        reason=payload.reason,
        supporting_document_url=payload.supporting_document_url,
        status="pending",
    )
    db.add(corr)
    await db.commit()
    await db.refresh(corr)

    return AttendanceCorrectionOut(
        id=corr.id,
        student_id=student.id,
        student_reg_id=student.student_id,
        student_name=current_user.full_name,
        course_id=course.id,
        course_code=course.course_code,
        course_title=course.title,
        session_id=corr.session_id,
        attendance_date=corr.attendance_date,
        requested_status=corr.requested_status,
        reason=corr.reason,
        supporting_document_url=corr.supporting_document_url,
        status=corr.status,
        review_comment=corr.review_comment,
        reviewed_at=corr.reviewed_at,
        created_at=corr.created_at,
    )


@router.get("/corrections", response_model=List[AttendanceCorrectionOut])
async def list_attendance_corrections(
    course_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List attendance correction requests."""
    query = (
        select(AttendanceCorrectionRequest)
        .options(
            selectinload(AttendanceCorrectionRequest.student).selectinload(Student.user),
            selectinload(AttendanceCorrectionRequest.course),
        )
        .order_by(desc(AttendanceCorrectionRequest.created_at))
    )

    if current_user.role == "student":
        s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        student = s_res.scalars().first()
        if not student:
            return []
        query = query.where(AttendanceCorrectionRequest.student_id == student.id)
    elif course_id:
        query = query.where(AttendanceCorrectionRequest.course_id == course_id)

    res = await db.execute(query)
    requests = res.scalars().all()

    out: List[AttendanceCorrectionOut] = []
    for r in requests:
        stu_name = r.student.user.full_name if (r.student and r.student.user) else "Student"
        reg_id = r.student.student_id if r.student else None
        out.append(
            AttendanceCorrectionOut(
                id=r.id,
                student_id=r.student_id,
                student_reg_id=reg_id,
                student_name=stu_name,
                course_id=r.course_id,
                course_code=r.course.course_code if r.course else "",
                course_title=r.course.title if r.course else "",
                session_id=r.session_id,
                attendance_date=r.attendance_date,
                requested_status=r.requested_status,
                reason=r.reason,
                supporting_document_url=r.supporting_document_url,
                status=r.status,
                review_comment=r.review_comment,
                reviewed_at=r.reviewed_at,
                created_at=r.created_at,
            )
        )
    return out


@router.put("/corrections/{request_id}/resolve", response_model=AttendanceCorrectionOut)
async def resolve_attendance_correction(
    request_id: int,
    payload: AttendanceCorrectionResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer", "admin")),
):
    """Lecturer approves or rejects an attendance excuse; automatically updates Attendance record on approval."""
    res = await db.execute(
        select(AttendanceCorrectionRequest)
        .options(
            selectinload(AttendanceCorrectionRequest.student).selectinload(Student.user),
            selectinload(AttendanceCorrectionRequest.course),
        )
        .where(AttendanceCorrectionRequest.id == request_id)
    )
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Attendance correction request not found.")

    req.status = payload.status
    req.review_comment = payload.review_comment
    req.reviewed_by_id = current_user.id
    req.reviewed_at = datetime.utcnow()

    # If approved, update or insert Attendance record
    if payload.status.lower() == "approved":
        target_status = AttendanceStatus.EXCUSED
        if req.requested_status.lower() == "present":
            target_status = AttendanceStatus.PRESENT

        # Find existing record
        att_query = select(Attendance).where(
            Attendance.student_id == req.student_id,
            Attendance.course_id == req.course_id,
            Attendance.date == req.attendance_date,
        )
        att_res = await db.execute(att_query)
        existing_att = att_res.scalars().first()
        if existing_att:
            existing_att.status = target_status
            existing_att.notes = f"Excuse approved: {req.reason[:50]}"
        else:
            new_att = Attendance(
                student_id=req.student_id,
                course_id=req.course_id,
                session_id=req.session_id,
                date=req.attendance_date,
                status=target_status,
                checkin_method="correction_request",
                checked_in_at=datetime.utcnow(),
                participation_score=10.0,
                notes=f"Excuse approved: {req.reason[:50]}",
            )
            db.add(new_att)

    await db.commit()
    await db.refresh(req)

    stu_name = req.student.user.full_name if (req.student and req.student.user) else "Student"
    reg_id = req.student.student_id if req.student else None
    return AttendanceCorrectionOut(
        id=req.id,
        student_id=req.student_id,
        student_reg_id=reg_id,
        student_name=stu_name,
        course_id=req.course_id,
        course_code=req.course.course_code if req.course else "",
        course_title=req.course.title if req.course else "",
        session_id=req.session_id,
        attendance_date=req.attendance_date,
        requested_status=req.requested_status,
        reason=req.reason,
        supporting_document_url=req.supporting_document_url,
        status=req.status,
        review_comment=req.review_comment,
        reviewed_at=req.reviewed_at,
        created_at=req.created_at,
    )


# ─── Course Attendance & Participation Analytics Summary ─────────────────────

@router.get("/courses/{course_id}/summary", response_model=CourseAttendanceSummary)
async def get_course_attendance_summary(
    course_id: int,
    student_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve institutional threshold policy summary and participation rate for a student in a course."""
    c_res = await db.execute(select(Course).where(Course.id == course_id))
    course = c_res.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    target_student_id = student_id
    if current_user.role == "student":
        s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        stu = s_res.scalars().first()
        if not stu:
            raise HTTPException(status_code=404, detail="Student profile not found.")
        target_student_id = stu.id

    if not target_student_id:
        raise HTTPException(status_code=400, detail="student_id is required for staff query.")

    # Total recorded attendance rows for this student in this course
    att_res = await db.execute(
        select(Attendance).where(
            Attendance.student_id == target_student_id,
            Attendance.course_id == course_id,
        )
    )
    records = att_res.scalars().all()

    total_sessions = len(records)
    present_cnt = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    late_cnt = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    absent_cnt = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    excused_cnt = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)

    attended_sessions = present_cnt + late_cnt + excused_cnt
    if total_sessions > 0:
        weighted_val = present_cnt + (late_cnt * 0.5) + excused_cnt
        att_rate = round((weighted_val / total_sessions) * 100, 1)
        avg_part = round(sum(r.participation_score for r in records) / total_sessions, 1)
    else:
        att_rate = 100.0
        avg_part = 0.0

    if att_rate >= 80.0:
        status_lvl = "good"
    elif att_rate >= 70.0:
        status_lvl = "warning"
    else:
        status_lvl = "critical"

    return CourseAttendanceSummary(
        course_id=course.id,
        course_code=course.course_code,
        course_title=course.title,
        total_sessions=total_sessions,
        attended_sessions=attended_sessions,
        present_count=present_cnt,
        late_count=late_cnt,
        absent_count=absent_cnt,
        excused_count=excused_cnt,
        attendance_rate=att_rate,
        policy_threshold=80.0,
        status_level=status_lvl,
        avg_participation_score=avg_part,
    )
