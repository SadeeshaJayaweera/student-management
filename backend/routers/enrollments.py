"""
NSBM EduSphere — Course Registration and Enrollment Router
Handles registration requests, prerequisite validation, calendar windows,
capacity limits, automated waitlisting, add/drop processing, and administrative approvals.
"""
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Student, Course, Semester, Enrollment, Grade,
    CoursePrerequisite, Institution
)
from backend.schemas import (
    EnrollmentRegisterRequest, EnrollmentStatusUpdate, EnrollmentOut
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/enrollments", tags=["Enrollments"])


@router.post("/register", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
async def register_course(
    payload: EnrollmentRegisterRequest,
    target_student_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a student for a course.
    - Validates student status and academic standing.
    - Enforces academic prerequisites and minimum grades.
    - Validates semester registration windows.
    - Checks course capacity; automatically waitlists if course is full.
    """
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.REGISTRAR.value, UserRole.DEAN.value}

    # 1. Resolve student
    if is_staff and target_student_id is not None:
        student_res = await db.execute(select(Student).where(Student.id == target_student_id))
        student = student_res.scalar_one_or_none()
    else:
        student_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        student = student_res.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found. Course registration is only permitted for registered students."
        )

    # 2. Check student academic standing
    if student.enrollment_status in {"suspended", "withdrawn", "expelled"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot register for courses. Current enrollment status is '{student.enrollment_status}'."
        )
    if student.academic_standing in {"suspended", "dismissed"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration blocked due to academic standing: '{student.academic_standing}'."
        )

    # 3. Resolve course
    course_res = await db.execute(
        select(Course).where(Course.id == payload.course_id)
        .options(
            selectinload(Course.prerequisites).selectinload(CoursePrerequisite.prerequisite_course),
            selectinload(Course.enrollments)
        )
    )
    course = course_res.scalar_one_or_none()
    if not course or not course.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target course not found or inactive")

    # 4. Resolve semester and registration calendar window
    semester = None
    if payload.semester_id:
        sem_res = await db.execute(select(Semester).where(Semester.id == payload.semester_id))
        semester = sem_res.scalar_one_or_none()
    else:
        # Pick current active semester for institution if exists
        sem_res = await db.execute(
            select(Semester).where(
                and_(Semester.institution_id == course.institution_id, Semester.is_current == True)
            )
        )
        semester = sem_res.scalar_one_or_none()

    today = date.today()
    if semester and not is_staff:
        if semester.registration_start_date and today < semester.registration_start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Course registration for term {semester.name} has not opened yet (Opens: {semester.registration_start_date})."
            )
        if semester.registration_end_date and today > semester.registration_end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Course registration window for term {semester.name} closed on {semester.registration_end_date}."
            )

    # 5. Check duplicate enrollment
    dup_query = select(Enrollment).where(
        and_(
            Enrollment.student_id == student.id,
            Enrollment.course_id == course.id,
            Enrollment.status.in_(["active", "requested", "waitlisted", "approved"])
        )
    )
    if semester:
        dup_query = dup_query.where(Enrollment.semester_id == semester.id)
    dup_res = await db.execute(dup_query)
    if dup_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student already has an active, requested, or waitlisted registration for this course."
        )

    # 6. Prerequisite Engine: check mandatory prerequisites
    for prereq in course.prerequisites:
        if prereq.is_mandatory:
            # Check student grades in prerequisite course
            grade_res = await db.execute(
                select(Grade).where(
                    and_(
                        Grade.student_id == student.id,
                        Grade.course_id == prereq.prerequisite_course_id
                    )
                )
            )
            grade = grade_res.scalar_one_or_none()
            has_passed = False
            if grade and grade.letter_grade not in {"F", "W", "I", None} and (grade.total is None or grade.total >= 50):
                has_passed = True

            if not has_passed and not is_staff:
                prereq_code = prereq.prerequisite_course.course_code if prereq.prerequisite_course else str(prereq.prerequisite_course_id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Prerequisite requirement failed: You must successfully complete {prereq_code} before registering for {course.course_code}."
                )

    # 7. Capacity & Waitlist Engine
    active_count_q = await db.execute(
        select(func.count(Enrollment.id)).where(
            and_(Enrollment.course_id == course.id, Enrollment.status == "active")
        )
    )
    active_count = active_count_q.scalar() or 0

    assigned_status = "active"
    assigned_waitlist_pos = None

    if active_count >= course.max_students:
        # Course is full -> assign waitlist
        waitlist_count_q = await db.execute(
            select(func.count(Enrollment.id)).where(
                and_(Enrollment.course_id == course.id, Enrollment.status == "waitlisted")
            )
        )
        waitlist_count = waitlist_count_q.scalar() or 0
        assigned_status = "waitlisted"
        assigned_waitlist_pos = waitlist_count + 1

    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        institution_id=course.institution_id,
        semester_id=semester.id if semester else None,
        status=assigned_status,
        waitlist_position=assigned_waitlist_pos,
        registration_type=payload.registration_type,
        remarks=payload.remarks,
        approved_by_id=current_user.id if is_staff else None,
        approved_at=datetime.utcnow() if is_staff else None
    )
    db.add(enrollment)
    await db.commit()

    refreshed = await db.execute(
        select(Enrollment).where(Enrollment.id == enrollment.id)
        .options(selectinload(Enrollment.course))
    )
    return refreshed.scalar_one()


@router.post("/{enrollment_id}/drop", response_model=EnrollmentOut)
async def drop_course(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Drop or withdraw from an enrolled course.
    - Validates ownership.
    - If dropped prior to add/drop deadline, marked as 'dropped'.
    - If dropped after deadline, marked as 'withdrawn'.
    - Automatically promotes the next waitlisted student to 'active'.
    """
    query = select(Enrollment).where(Enrollment.id == enrollment_id).options(
        selectinload(Enrollment.student),
        selectinload(Enrollment.course),
        selectinload(Enrollment.semester)
    )
    res = await db.execute(query)
    enrollment = res.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment record not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.REGISTRAR.value, UserRole.DEAN.value}
    is_owner = enrollment.student.user_id == current_user.id

    if not (is_staff or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot drop another student's course enrollment."
        )

    if enrollment.status in {"dropped", "withdrawn", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Enrollment is already in '{enrollment.status}' status."
        )

    previous_status = enrollment.status
    today = date.today()
    drop_status = "dropped"

    if enrollment.semester and enrollment.semester.add_drop_deadline:
        if today > enrollment.semester.add_drop_deadline:
            drop_status = "withdrawn"

    enrollment.status = drop_status
    enrollment.dropped_at = datetime.utcnow()
    enrollment.waitlist_position = None

    # Waitlist Promotion Engine
    if previous_status == "active":
        # Find next waitlisted student for this course
        next_waitlist_q = await db.execute(
            select(Enrollment).where(
                and_(Enrollment.course_id == enrollment.course_id, Enrollment.status == "waitlisted")
            )
            .order_by(Enrollment.waitlist_position.asc())
            .limit(1)
        )
        promoted = next_waitlist_q.scalar_one_or_none()
        if promoted:
            promoted.status = "active"
            promoted.waitlist_position = None
            promoted.approved_at = datetime.utcnow()

            # Shift remaining waitlist positions
            await db.execute(
                update(Enrollment).where(
                    and_(Enrollment.course_id == enrollment.course_id, Enrollment.status == "waitlisted")
                ).values(waitlist_position=Enrollment.waitlist_position - 1)
            )

    await db.commit()
    await db.refresh(enrollment)
    return enrollment


@router.get("", response_model=List[EnrollmentOut])
async def list_enrollments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    enrollment_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List course enrollments with filtering.
    Students may only view their own enrollments; staff can view all matching filters.
    """
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.REGISTRAR.value, UserRole.DEAN.value, UserRole.LECTURER.value}

    query = select(Enrollment).options(selectinload(Enrollment.course))

    # Multi-tenant isolation
    if current_user.institution_id is not None:
        query = query.where(Enrollment.institution_id == current_user.institution_id)

    if not is_staff:
        # Restrict to current student
        student_res = await db.execute(select(Student.id).where(Student.user_id == current_user.id))
        s_id = student_res.scalar_one_or_none()
        if not s_id:
            return []
        query = query.where(Enrollment.student_id == s_id)
    elif student_id is not None:
        query = query.where(Enrollment.student_id == student_id)

    if course_id is not None:
        query = query.where(Enrollment.course_id == course_id)
    if semester_id is not None:
        query = query.where(Enrollment.semester_id == semester_id)
    if enrollment_status is not None:
        query = query.where(Enrollment.status == enrollment_status)

    query = query.order_by(Enrollment.enrolled_at.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    return res.scalars().all()


@router.get("/my", response_model=List[EnrollmentOut])
async def get_my_enrollments(
    current_user: User = Depends(require_roles("student")),
    db: AsyncSession = Depends(get_db)
):
    """Get all current and past enrollments for the logged-in student."""
    student_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = student_res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    query = select(Enrollment).where(Enrollment.student_id == student.id).options(
        selectinload(Enrollment.course)
    ).order_by(Enrollment.enrolled_at.desc())

    res = await db.execute(query)
    return res.scalars().all()


@router.patch("/{enrollment_id}/status", response_model=EnrollmentOut)
async def update_enrollment_status(
    enrollment_id: int,
    payload: EnrollmentStatusUpdate,
    current_user: User = Depends(require_roles("admin", "registrar", "dean")),
    db: AsyncSession = Depends(get_db)
):
    """
    Administrative status update (Approve, Reject, Complete, etc.) for course enrollments.
    Restricted to Admins, Registrars, and Deans.
    """
    ALLOWED_STATUSES = {"active", "approved", "waitlisted", "dropped", "withdrawn", "rejected", "completed"}
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed values: {sorted(list(ALLOWED_STATUSES))}"
        )

    res = await db.execute(
        select(Enrollment).where(Enrollment.id == enrollment_id).options(selectinload(Enrollment.course))
    )
    enrollment = res.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment record not found")

    enrollment.status = payload.status
    if payload.status in {"active", "approved"}:
        enrollment.approved_by_id = current_user.id
        enrollment.approved_at = datetime.utcnow()
        enrollment.waitlist_position = None
    elif payload.status == "rejected":
        enrollment.rejection_reason = payload.rejection_reason
    if payload.remarks:
        enrollment.remarks = payload.remarks

    await db.commit()
    await db.refresh(enrollment)
    return enrollment
