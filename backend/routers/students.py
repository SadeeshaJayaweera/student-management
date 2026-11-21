"""NSBM EduSphere — Student Portal Router"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Student, Enrollment, Grade, Attendance, Assignment,
    AssignmentSubmission, Notification, BorrowRecord, ClubMembership,
    ClubEvent, Course
)
from backend.schemas import (
    StudentOut, StudentUpdate, StudentCreate, StudentStatusUpdate,
    GradeOut, CourseOut, AssignmentOut, NotificationOut,
    SubmissionCreate, StudentDashboard
)
from backend.utils.security import get_current_user, require_roles
from backend.core.authorization import (
    StudentProfilePolicy, assert_can_read, assert_can_write
)
from backend.core.exceptions import ForbiddenException

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("/dashboard")
async def student_dashboard(
    current_user: User = Depends(require_roles("student", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """Get student's full dashboard data"""
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
        .options(selectinload(Student.user))
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Enrolled courses count
    enroll_count = await db.execute(
        select(func.count(Enrollment.id)).where(
            and_(Enrollment.student_id == student.id, Enrollment.status == "active")
        )
    )

    # Pending assignments
    submitted_ids_q = await db.execute(
        select(AssignmentSubmission.assignment_id).where(AssignmentSubmission.student_id == student.id)
    )
    submitted_ids = [r[0] for r in submitted_ids_q.all()]
    enrolled_course_ids_q = await db.execute(
        select(Enrollment.course_id).where(Enrollment.student_id == student.id)
    )
    enrolled_course_ids = [r[0] for r in enrolled_course_ids_q.all()]

    from datetime import datetime
    pending_q = await db.execute(
        select(func.count(Assignment.id)).where(
            and_(
                Assignment.course_id.in_(enrolled_course_ids),
                Assignment.id.notin_(submitted_ids),
                Assignment.due_date > datetime.utcnow()
            )
        )
    )
    pending_assignments = pending_q.scalar() or 0

    # Unread notifications
    notif_q = await db.execute(
        select(func.count(Notification.id)).where(
            and_(Notification.user_id == current_user.id, Notification.is_read == False)
        )
    )

    # Borrowed books
    borrow_q = await db.execute(
        select(func.count(BorrowRecord.id)).where(
            and_(BorrowRecord.student_id == student.id, BorrowRecord.status == "active")
        )
    )

    # Recent grades
    grades_q = await db.execute(
        select(Grade).where(Grade.student_id == student.id)
        .options(selectinload(Grade.course))
        .limit(5)
    )
    grades = grades_q.scalars().all()

    # Upcoming events
    events_q = await db.execute(
        select(ClubEvent).where(ClubEvent.event_date > datetime.utcnow()).limit(4)
    )
    events = events_q.scalars().all()

    # Attendance
    att_q = await db.execute(
        select(func.count(Attendance.id)).where(Attendance.student_id == student.id)
    )
    total_att = att_q.scalar() or 1
    present_q = await db.execute(
        select(func.count(Attendance.id)).where(
            and_(Attendance.student_id == student.id, Attendance.status == "present")
        )
    )
    present_att = present_q.scalar() or 0

    return {
        "student_id": student.student_id,
        "full_name": current_user.full_name,
        "faculty": student.faculty,
        "department": student.department,
        "program": student.program,
        "year_of_study": student.year_of_study,
        "semester": student.semester,
        "gpa": student.gpa,
        "credits_earned": student.credits_earned,
        "enrolled_courses": enroll_count.scalar() or 0,
        "pending_assignments": pending_assignments,
        "unread_notifications": notif_q.scalar() or 0,
        "borrowed_books": borrow_q.scalar() or 0,
        "attendance_rate": round((present_att / total_att) * 100, 1),
        "recent_grades": [
            {
                "course": g.course.title,
                "course_code": g.course.course_code,
                "total": g.total,
                "letter": g.letter_grade,
                "grade_points": g.grade_points
            } for g in grades
        ],
        "upcoming_events": [
            {
                "title": e.title,
                "date": e.event_date.isoformat(),
                "location": e.location
            } for e in events
        ]
    }


@router.get("/grades")
async def get_grades(
    current_user: User = Depends(require_roles("student", "admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    grades_q = await db.execute(
        select(Grade).where(Grade.student_id == student.id)
        .options(selectinload(Grade.course).selectinload(Course.lecturer).selectinload(Lecturer.user))
    )
    grades = grades_q.scalars().all()
    return [
        {
            "id": g.id,
            "course_code": g.course.course_code,
            "course_title": g.course.title,
            "credits": g.course.credits,
            "midterm": g.midterm,
            "final": g.final,
            "assignments_avg": g.assignments_avg,
            "total": g.total,
            "letter_grade": g.letter_grade,
            "grade_points": g.grade_points,
            "remarks": g.remarks
        }
        for g in grades
    ]


@router.get("/attendance")
async def get_attendance(
    course_id: Optional[int] = None,
    current_user: User = Depends(require_roles("student", "admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    query = select(Attendance).where(Attendance.student_id == student.id)
    if course_id:
        query = query.where(Attendance.course_id == course_id)
    query = query.options(selectinload(Attendance.course))

    att_q = await db.execute(query)
    attendance = att_q.scalars().all()
    return [
        {
            "id": a.id,
            "course": a.course.title,
            "course_code": a.course.course_code,
            "date": a.date.isoformat(),
            "status": a.status.value
        }
        for a in attendance
    ]


@router.get("/courses")
async def get_enrolled_courses(
    current_user: User = Depends(require_roles("student", "admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    enrollments_q = await db.execute(
        select(Enrollment).where(Enrollment.student_id == student.id)
        .options(selectinload(Enrollment.course).selectinload(Course.lecturer).selectinload(Lecturer.user))
    )
    enrollments = enrollments_q.scalars().all()
    return [
        {
            "id": e.course.id,
            "course_code": e.course.course_code,
            "title": e.course.title,
            "description": e.course.description,
            "credits": e.course.credits,
            "semester": e.course.semester,
            "year": e.course.year,
            "schedule": e.course.schedule,
            "lecturer": e.course.lecturer.user.full_name if e.course.lecturer else None,
            "enrollment_status": e.status
        }
        for e in enrollments
    ]


@router.get("/assignments")
async def get_assignments(
    current_user: User = Depends(require_roles("student", "admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    enrolled_q = await db.execute(
        select(Enrollment.course_id).where(Enrollment.student_id == student.id)
    )
    course_ids = [r[0] for r in enrolled_q.all()]

    assignments_q = await db.execute(
        select(Assignment).where(Assignment.course_id.in_(course_ids))
        .options(selectinload(Assignment.course))
        .order_by(Assignment.due_date.asc())
    )
    assignments = assignments_q.scalars().all()

    # Get submitted assignment IDs
    submitted_q = await db.execute(
        select(AssignmentSubmission).where(AssignmentSubmission.student_id == student.id)
    )
    submissions = {s.assignment_id: s for s in submitted_q.scalars().all()}

    from datetime import datetime
    return [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "course": a.course.title,
            "course_code": a.course.course_code,
            "due_date": a.due_date.isoformat(),
            "max_marks": a.max_marks,
            "type": a.assignment_type,
            "is_submitted": a.id in submissions,
            "submission": {
                "marks": submissions[a.id].marks,
                "feedback": submissions[a.id].feedback,
                "submitted_at": submissions[a.id].submitted_at.isoformat()
            } if a.id in submissions else None,
            "is_overdue": a.due_date < datetime.utcnow() and a.id not in submissions
        }
        for a in assignments
    ]


def _mask_student_pii(student: Student, current_user: User) -> StudentOut:
    out = StudentOut.model_validate(student)
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_privileged = role_val in {UserRole.ADMIN.value, UserRole.REGISTRAR.value} or current_user.id == student.user_id
    if not is_privileged:
        out.national_id = "REDACTED"
        out.date_of_birth = None
    return out


@router.get("", response_model=List[StudentOut])
async def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    campus_id: Optional[int] = None,
    program_id: Optional[int] = None,
    faculty_id: Optional[int] = None,
    department_id: Optional[int] = None,
    academic_standing: Optional[str] = None,
    enrollment_status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_roles("admin", "registrar", "dean", "lecturer")),
    db: AsyncSession = Depends(get_db)
):
    """
    List students with filtering, search, and pagination.
    Restricted to academic staff and administrators.
    """
    query = select(Student).options(selectinload(Student.user))

    # Multi-tenant isolation
    if current_user.institution_id is not None:
        query = query.where(Student.institution_id == current_user.institution_id)

    if campus_id is not None:
        query = query.where(Student.campus_id == campus_id)
    if program_id is not None:
        query = query.where(Student.program_id == program_id)
    if faculty_id is not None:
        query = query.where(Student.faculty_id == faculty_id)
    if department_id is not None:
        query = query.where(Student.department_id == department_id)
    if academic_standing is not None:
        query = query.where(Student.academic_standing == academic_standing)
    if enrollment_status is not None:
        query = query.where(Student.enrollment_status == enrollment_status)

    if search:
        search_filter = f"%{search}%"
        query = query.join(Student.user).where(
            or_(
                Student.student_id.ilike(search_filter),
                User.full_name.ilike(search_filter),
                User.email.ilike(search_filter)
            )
        )

    query = query.offset(skip).limit(limit)
    res = await db.execute(query)
    students = res.scalars().all()

    return [_mask_student_pii(s, current_user) for s in students]


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student_profile(
    payload: StudentCreate,
    current_user: User = Depends(require_roles("admin", "registrar")),
    db: AsyncSession = Depends(get_db)
):
    """
    Provision a new student profile for an existing student user.
    Restricted to Admins and Registrars.
    """
    # Verify user exists and has student role
    user_res = await db.execute(select(User).where(User.id == payload.user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Target user account not found")

    user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
    if user_role != UserRole.STUDENT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student profile can only be provisioned for users with 'student' role"
        )

    # Check for existing profile
    existing = await db.execute(
        select(Student).where(or_(Student.user_id == payload.user_id, Student.student_id == payload.student_id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student profile already exists for this user or student ID"
        )

    # Institution isolation
    institution_id = current_user.institution_id or user.institution_id

    student = Student(
        user_id=payload.user_id,
        institution_id=institution_id,
        student_id=payload.student_id,
        faculty=payload.faculty,
        department=payload.department,
        program=payload.program,
        year_of_study=payload.year_of_study,
        semester=payload.semester,
        campus_id=payload.campus_id,
        program_id=payload.program_id,
        faculty_id=payload.faculty_id,
        department_id=payload.department_id,
        enrollment_date=payload.enrollment_date,
        expected_graduation=payload.expected_graduation,
        address=payload.address,
        emergency_contact=payload.emergency_contact,
        national_id=payload.national_id,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        academic_standing=payload.academic_standing or "good_standing",
        enrollment_status=payload.enrollment_status or "enrolled",
        scholarship=payload.scholarship,
        gpa=0.0,
        credits_earned=0
    )
    db.add(student)
    await db.commit()

    refreshed = await db.execute(
        select(Student).where(Student.id == student.id).options(selectinload(Student.user))
    )
    return refreshed.scalar_one()


@router.get("/{student_ref}", response_model=StudentOut)
async def get_student_by_id(
    student_ref: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get student profile by ID or Student ID.
    Enforces resource-level authorization (BOLA defense):
    - Students can only view their own profile.
    - Staff / faculty can view student profiles (with PII masking for non-admin/registrar).
    """
    query = select(Student).options(selectinload(Student.user))
    if student_ref.isdigit():
        query = query.where(or_(Student.id == int(student_ref), Student.student_id == student_ref))
    else:
        query = query.where(Student.student_id == student_ref)

    res = await db.execute(query)
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    try:
        assert_can_read(current_user, StudentProfilePolicy(), student, "student profile")
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)

    return _mask_student_pii(student, current_user)


@router.put("/{student_ref}", response_model=StudentOut)
async def update_student_profile(
    student_ref: str,
    payload: StudentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update student profile details.
    Enforces resource-level authorization:
    - Students can only update their own emergency contact and address.
    - Academic fields (year, semester, campus, program, etc.) can only be altered by Admins or Registrars.
    """
    query = select(Student).options(selectinload(Student.user))
    if student_ref.isdigit():
        query = query.where(or_(Student.id == int(student_ref), Student.student_id == student_ref))
    else:
        query = query.where(Student.student_id == student_ref)

    res = await db.execute(query)
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    try:
        assert_can_write(current_user, StudentProfilePolicy(), student, "student profile")
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.REGISTRAR.value}

    if payload.address is not None:
        student.address = payload.address
    if payload.emergency_contact is not None:
        student.emergency_contact = payload.emergency_contact

    # Privilege escalation defense: students cannot alter academic status or assignments
    academic_fields_provided = any([
        payload.year_of_study is not None,
        payload.semester is not None,
        payload.campus_id is not None,
        payload.program_id is not None,
        payload.academic_standing is not None,
        payload.enrollment_status is not None,
        payload.expected_graduation is not None,
        payload.scholarship is not None
    ])

    if academic_fields_provided and not is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only academic staff (Admin/Registrar) can update academic standing, program, or semester details."
        )

    if is_staff:
        if payload.year_of_study is not None:
            student.year_of_study = payload.year_of_study
        if payload.semester is not None:
            student.semester = payload.semester
        if payload.campus_id is not None:
            student.campus_id = payload.campus_id
        if payload.program_id is not None:
            student.program_id = payload.program_id
        if payload.academic_standing is not None:
            student.academic_standing = payload.academic_standing
        if payload.enrollment_status is not None:
            student.enrollment_status = payload.enrollment_status
        if payload.expected_graduation is not None:
            student.expected_graduation = payload.expected_graduation
        if payload.scholarship is not None:
            student.scholarship = payload.scholarship

    await db.commit()
    await db.refresh(student)
    return _mask_student_pii(student, current_user)


@router.patch("/{student_ref}/status", response_model=StudentOut)
async def update_student_status(
    student_ref: str,
    payload: StudentStatusUpdate,
    current_user: User = Depends(require_roles("admin", "registrar")),
    db: AsyncSession = Depends(get_db)
):
    """
    Administrative transition of student enrollment status or academic standing.
    Restricted to Admins and Registrars.
    """
    ALLOWED_STATUSES = {"enrolled", "on_leave", "suspended", "graduated", "withdrawn", "deferred"}
    ALLOWED_STANDINGS = {"good_standing", "academic_probation", "deans_list", "suspended", "dismissed"}

    if payload.enrollment_status and payload.enrollment_status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid enrollment status. Allowed values: {sorted(list(ALLOWED_STATUSES))}"
        )

    if payload.academic_standing and payload.academic_standing not in ALLOWED_STANDINGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid academic standing. Allowed values: {sorted(list(ALLOWED_STANDINGS))}"
        )

    query = select(Student).options(selectinload(Student.user))
    if student_ref.isdigit():
        query = query.where(or_(Student.id == int(student_ref), Student.student_id == student_ref))
    else:
        query = query.where(Student.student_id == student_ref)

    res = await db.execute(query)
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    if payload.enrollment_status:
        student.enrollment_status = payload.enrollment_status
    if payload.academic_standing:
        student.academic_standing = payload.academic_standing

    await db.commit()
    await db.refresh(student)
    return _mask_student_pii(student, current_user)


@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    payload: SubmissionCreate,
    current_user: User = Depends(require_roles("student")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    # Verify assignment exists
    assignment_res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = assignment_res.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify student is actively enrolled in this course
    enroll_res = await db.execute(
        select(Enrollment).where(
            and_(
                Enrollment.student_id == student.id,
                Enrollment.course_id == assignment.course_id,
                Enrollment.status == "active",
            )
        )
    )
    if not enroll_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not actively enrolled in the course for this assignment."
        )

    # Check existing submission
    existing = await db.execute(
        select(AssignmentSubmission).where(
            and_(AssignmentSubmission.assignment_id == assignment_id,
                 AssignmentSubmission.student_id == student.id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already submitted")

    submission = AssignmentSubmission(
        assignment_id=assignment_id,
        student_id=student.id,
        text_content=payload.text_content,
        status="submitted"
    )
    db.add(submission)
    await db.commit()
    return {"message": "Assignment submitted successfully", "id": submission.id}


@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc()).limit(50)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/notifications/{notif_id}/read")
async def mark_notification_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification).where(
            and_(Notification.id == notif_id, Notification.user_id == current_user.id)
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(404, "Notification not found")
    notif.is_read = True
    await db.commit()
    return {"message": "Marked as read"}


# Import Lecturer model for selectinload
from backend.models import Lecturer
