"""NSBM EduSphere — Lecturer and Staff Management Router"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Lecturer, Course, Student, Enrollment, Grade, Assignment,
    AssignmentSubmission, Attendance, CourseMaterial, Notification,
    Campus, Faculty, Department
)
from backend.schemas import (
    AssignmentCreate, GradeUpdate,
    LecturerCreate, LecturerUpdate, LecturerOut, LecturerWorkloadSummary
)
from backend.utils.security import require_roles, get_current_user

router = APIRouter(prefix="/api/lecturers", tags=["Lecturers"])


@router.get("", response_model=List[LecturerOut])
async def list_lecturers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    campus_id: Optional[int] = None,
    faculty_id: Optional[int] = None,
    department_id: Optional[int] = None,
    employment_status: Optional[str] = None,
    designation: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List academic staff and faculty members with filtering, search, and pagination.
    Accessible to all authenticated users.
    """
    query = select(Lecturer).options(selectinload(Lecturer.user))

    # Multi-tenant isolation
    if current_user.institution_id is not None:
        query = query.where(Lecturer.institution_id == current_user.institution_id)

    if campus_id is not None:
        query = query.where(Lecturer.campus_id == campus_id)
    if faculty_id is not None:
        query = query.where(Lecturer.faculty_id == faculty_id)
    if department_id is not None:
        query = query.where(Lecturer.department_id == department_id)
    if employment_status is not None:
        query = query.where(Lecturer.employment_status == employment_status)
    if designation is not None:
        query = query.where(Lecturer.designation == designation)

    if search:
        search_filter = f"%{search}%"
        query = query.join(Lecturer.user).where(
            or_(
                Lecturer.lecturer_id.ilike(search_filter),
                Lecturer.specialization.ilike(search_filter),
                User.full_name.ilike(search_filter),
                User.email.ilike(search_filter)
            )
        )

    query = query.offset(skip).limit(limit)
    res = await db.execute(query)
    return res.scalars().all()


@router.post("", response_model=LecturerOut, status_code=status.HTTP_201_CREATED)
async def create_lecturer_profile(
    payload: LecturerCreate,
    current_user: User = Depends(require_roles("admin", "dean", "registrar")),
    db: AsyncSession = Depends(get_db)
):
    """
    Provision an academic faculty / lecturer profile for an existing staff user.
    Restricted to Admins, Deans, and Registrars.
    """
    # Verify user exists and has faculty-capable role
    user_res = await db.execute(select(User).where(User.id == payload.user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Target user account not found")

    user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
    ALLOWED_FACULTY_ROLES = {UserRole.LECTURER.value, UserRole.DEAN.value, UserRole.ADMIN.value}
    if user_role not in ALLOWED_FACULTY_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lecturer profiles can only be provisioned for staff with roles: {sorted(list(ALLOWED_FACULTY_ROLES))}"
        )

    # Check for existing profile
    existing = await db.execute(
        select(Lecturer).where(or_(Lecturer.user_id == payload.user_id, Lecturer.lecturer_id == payload.lecturer_id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A lecturer profile already exists for this user or lecturer ID"
        )

    institution_id = current_user.institution_id or user.institution_id

    lecturer = Lecturer(
        user_id=payload.user_id,
        institution_id=institution_id,
        lecturer_id=payload.lecturer_id,
        faculty=payload.faculty,
        department=payload.department,
        specialization=payload.specialization,
        qualification=payload.qualification,
        designation=payload.designation,
        employment_status=payload.employment_status,
        campus_id=payload.campus_id,
        faculty_id=payload.faculty_id,
        department_id=payload.department_id,
        office_location=payload.office_location,
        office_hours=payload.office_hours,
        research_interests=payload.research_interests,
        bio=payload.bio,
        max_teaching_load_hours=payload.max_teaching_load_hours,
        current_teaching_load_hours=0,
        joined_date=payload.joined_date
    )
    db.add(lecturer)
    await db.commit()

    refreshed = await db.execute(
        select(Lecturer).where(Lecturer.id == lecturer.id).options(selectinload(Lecturer.user))
    )
    return refreshed.scalar_one()


@router.get("/dashboard")
async def lecturer_dashboard(
    current_user: User = Depends(require_roles("lecturer", "admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Lecturer).where(Lecturer.user_id == current_user.id)
        .options(selectinload(Lecturer.user))
    )
    lecturer = result.scalar_one_or_none()
    if not lecturer:
        raise HTTPException(404, "Lecturer profile not found")

    # Total courses
    courses_q = await db.execute(
        select(func.count(Course.id)).where(Course.lecturer_id == lecturer.id)
    )
    total_courses = courses_q.scalar() or 0

    # Total students
    course_ids_q = await db.execute(
        select(Course.id).where(Course.lecturer_id == lecturer.id)
    )
    course_ids = [r[0] for r in course_ids_q.all()]
    students_q = await db.execute(
        select(func.count(Enrollment.id)).where(
            and_(Enrollment.course_id.in_(course_ids), Enrollment.status == "active")
        )
    )
    total_students = students_q.scalar() or 0

    # Pending submissions to grade
    assignments_q = await db.execute(
        select(Assignment.id).where(Assignment.course_id.in_(course_ids))
    )
    assignment_ids = [r[0] for r in assignments_q.all()]
    pending_q = await db.execute(
        select(func.count(AssignmentSubmission.id)).where(
            and_(
                AssignmentSubmission.assignment_id.in_(assignment_ids),
                AssignmentSubmission.marks == None
            )
        )
    )
    pending_submissions = pending_q.scalar() or 0

    # Recent activity
    recent_submissions_q = await db.execute(
        select(AssignmentSubmission).where(AssignmentSubmission.assignment_id.in_(assignment_ids))
        .options(
            selectinload(AssignmentSubmission.student).selectinload(Student.user),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.course)
        )
        .order_by(AssignmentSubmission.submitted_at.desc())
        .limit(5)
    )
    recent_submissions = recent_submissions_q.scalars().all()

    return {
        "lecturer_id": lecturer.lecturer_id,
        "full_name": current_user.full_name,
        "faculty": lecturer.faculty,
        "department": lecturer.department,
        "specialization": lecturer.specialization,
        "office_location": lecturer.office_location,
        "office_hours": lecturer.office_hours,
        "total_courses": total_courses,
        "total_students": total_students,
        "pending_submissions": pending_submissions,
        "recent_submissions": [
            {
                "student": s.student.user.full_name,
                "assignment": s.assignment.title,
                "course": s.assignment.course.title,
                "submitted_at": s.submitted_at.isoformat(),
                "graded": s.marks is not None
            }
            for s in recent_submissions
        ]
    }


@router.get("/courses")
async def get_courses(
    current_user: User = Depends(require_roles("lecturer", "admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Lecturer).where(Lecturer.user_id == current_user.id))
    lecturer = result.scalar_one_or_none()
    if not lecturer:
        raise HTTPException(404, "Lecturer not found")

    courses_q = await db.execute(
        select(Course).where(Course.lecturer_id == lecturer.id)
        .options(selectinload(Course.enrollments))
    )
    courses = courses_q.scalars().all()
    return [
        {
            "id": c.id,
            "course_code": c.course_code,
            "title": c.title,
            "description": c.description,
            "credits": c.credits,
            "semester": c.semester,
            "year": c.year,
            "schedule": c.schedule,
            "enrolled_count": len([e for e in c.enrollments if e.status == "active"]),
            "max_students": c.max_students
        }
        for c in courses
    ]


@router.get("/courses/{course_id}/students")
async def get_course_students(
    course_id: int,
    current_user: User = Depends(require_roles("lecturer", "admin")),
    db: AsyncSession = Depends(get_db)
):
    enrollments_q = await db.execute(
        select(Enrollment).where(and_(Enrollment.course_id == course_id, Enrollment.status == "active"))
        .options(
            selectinload(Enrollment.student).selectinload(Student.user),
            selectinload(Enrollment.student).selectinload(Student.grades)
        )
    )
    enrollments = enrollments_q.scalars().all()

    result = []
    for e in enrollments:
        student = e.student
        grade = next((g for g in student.grades if g.course_id == course_id), None)
        result.append({
            "student_id": student.student_id,
            "full_name": student.user.full_name,
            "email": student.user.email,
            "year": student.year_of_study,
            "semester": student.semester,
            "grade": {
                "midterm": grade.midterm if grade else None,
                "final": grade.final if grade else None,
                "total": grade.total if grade else None,
                "letter": grade.letter_grade if grade else None
            }
        })
    return result


@router.post("/assignments")
async def create_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(require_roles("lecturer", "admin")),
    db: AsyncSession = Depends(get_db)
):
    assignment = Assignment(**payload.dict())
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return {"message": "Assignment created", "id": assignment.id}


@router.get("/assignments/{assignment_id}/submissions")
async def get_submissions(
    assignment_id: int,
    current_user: User = Depends(require_roles("lecturer", "admin")),
    db: AsyncSession = Depends(get_db)
):
    submissions_q = await db.execute(
        select(AssignmentSubmission).where(AssignmentSubmission.assignment_id == assignment_id)
        .options(selectinload(AssignmentSubmission.student).selectinload(Student.user))
    )
    submissions = submissions_q.scalars().all()
    return [
        {
            "id": s.id,
            "student": s.student.user.full_name,
            "student_id": s.student.student_id,
            "submitted_at": s.submitted_at.isoformat(),
            "text_content": s.text_content,
            "marks": s.marks,
            "feedback": s.feedback,
            "status": s.status.value
        }
        for s in submissions
    ]


@router.patch("/submissions/{submission_id}/grade")
async def grade_submission(
    submission_id: int,
    marks: float,
    feedback: Optional[str] = None,
    current_user: User = Depends(require_roles("lecturer", "admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AssignmentSubmission).where(AssignmentSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(404, "Submission not found")
    submission.marks = marks
    submission.feedback = feedback
    submission.status = "graded"
    await db.commit()
    return {"message": "Graded successfully"}


@router.post("/attendance")
async def record_attendance(
    course_id: int,
    records: List[dict],
    current_user: User = Depends(require_roles("lecturer", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """Record attendance for a class session"""
    from datetime import date
    for record in records:
        att = Attendance(
            student_id=record["student_id"],
            course_id=course_id,
            date=date.today(),
            status=record.get("status", "present")
        )
        db.add(att)
    await db.commit()
    return {"message": f"Attendance recorded for {len(records)} students"}


@router.get("/analytics")
async def get_analytics(
    current_user: User = Depends(require_roles("lecturer", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """Grade distribution and engagement analytics"""
    result = await db.execute(select(Lecturer).where(Lecturer.user_id == current_user.id))
    lecturer = result.scalar_one_or_none()
    if not lecturer:
        raise HTTPException(404, "Lecturer not found")

    course_ids_q = await db.execute(select(Course.id).where(Course.lecturer_id == lecturer.id))
    course_ids = [r[0] for r in course_ids_q.all()]

    grades_q = await db.execute(
        select(Grade).where(Grade.course_id.in_(course_ids))
        .options(selectinload(Grade.course))
    )
    grades = grades_q.scalars().all()

    dist = {"A+": 0, "A": 0, "B+": 0, "B": 0, "C+": 0, "C": 0, "D": 0, "F": 0}
    for g in grades:
        if g.letter_grade in dist:
            dist[g.letter_grade] += 1

    avg_total = sum(g.total for g in grades if g.total) / max(len(grades), 1)
    return {
        "grade_distribution": dist,
        "average_score": round(avg_total, 2),
        "total_students_graded": len(grades),
        "passing_rate": round(len([g for g in grades if g.total and g.total >= 50]) / max(len(grades), 1) * 100, 1)
    }


@router.get("/{lecturer_ref}", response_model=LecturerOut)
async def get_lecturer_by_id(
    lecturer_ref: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get lecturer profile by ID or Lecturer ID.
    Accessible to all authenticated users.
    """
    query = select(Lecturer).options(selectinload(Lecturer.user))
    if lecturer_ref.isdigit():
        query = query.where(or_(Lecturer.id == int(lecturer_ref), Lecturer.lecturer_id == lecturer_ref))
    else:
        query = query.where(Lecturer.lecturer_id == lecturer_ref)

    res = await db.execute(query)
    lecturer = res.scalar_one_or_none()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer profile not found")

    return lecturer


@router.put("/{lecturer_ref}", response_model=LecturerOut)
async def update_lecturer_profile(
    lecturer_ref: str,
    payload: LecturerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update lecturer details.
    Enforces authorization:
    - Admins and Deans can alter appointments, workloads, and department assignments.
    - Lecturers can update their own personal/office profile.
    - Privilege escalation defense: Lecturers cannot change their employment status or workload limits.
    """
    query = select(Lecturer).options(selectinload(Lecturer.user))
    if lecturer_ref.isdigit():
        query = query.where(or_(Lecturer.id == int(lecturer_ref), Lecturer.lecturer_id == lecturer_ref))
    else:
        query = query.where(Lecturer.lecturer_id == lecturer_ref)

    res = await db.execute(query)
    lecturer = res.scalar_one_or_none()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer profile not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin_or_dean = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_owner = current_user.id == lecturer.user_id

    if not (is_admin_or_dean or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to modify this lecturer profile."
        )

    # Check for privilege escalation attempts
    restricted_fields_attempted = any([
        payload.employment_status is not None,
        payload.designation is not None,
        payload.max_teaching_load_hours is not None,
        payload.campus_id is not None,
        payload.faculty_id is not None,
        payload.department_id is not None,
    ])

    if restricted_fields_attempted and not is_admin_or_dean:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and academic deans can alter academic appointments, employment status, or teaching load limits."
        )

    # Permitted self-updates
    if payload.specialization is not None:
        lecturer.specialization = payload.specialization
    if payload.qualification is not None:
        lecturer.qualification = payload.qualification
    if payload.office_location is not None:
        lecturer.office_location = payload.office_location
    if payload.office_hours is not None:
        lecturer.office_hours = payload.office_hours
    if payload.research_interests is not None:
        lecturer.research_interests = payload.research_interests
    if payload.bio is not None:
        lecturer.bio = payload.bio
    if payload.publications is not None:
        lecturer.publications = payload.publications

    # Privileged updates
    if is_admin_or_dean:
        if payload.faculty is not None:
            lecturer.faculty = payload.faculty
        if payload.department is not None:
            lecturer.department = payload.department
        if payload.campus_id is not None:
            lecturer.campus_id = payload.campus_id
        if payload.faculty_id is not None:
            lecturer.faculty_id = payload.faculty_id
        if payload.department_id is not None:
            lecturer.department_id = payload.department_id
        if payload.employment_status is not None:
            lecturer.employment_status = payload.employment_status
        if payload.designation is not None:
            lecturer.designation = payload.designation
        if payload.max_teaching_load_hours is not None:
            lecturer.max_teaching_load_hours = payload.max_teaching_load_hours

    await db.commit()
    await db.refresh(lecturer)
    return lecturer


@router.get("/{lecturer_ref}/workload", response_model=LecturerWorkloadSummary)
async def get_lecturer_workload(
    lecturer_ref: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed teaching workload analysis for a lecturer, including assigned courses,
    total contact hours, and enrollment figures.
    """
    query = select(Lecturer).options(
        selectinload(Lecturer.user),
        selectinload(Lecturer.courses).selectinload(Course.enrollments)
    )
    if lecturer_ref.isdigit():
        query = query.where(or_(Lecturer.id == int(lecturer_ref), Lecturer.lecturer_id == lecturer_ref))
    else:
        query = query.where(Lecturer.lecturer_id == lecturer_ref)

    res = await db.execute(query)
    lecturer = res.scalar_one_or_none()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer profile not found")

    courses_summary = []
    total_contact_hours = 0
    total_students = 0

    for c in lecturer.courses:
        active_enrollments = len([e for e in c.enrollments if e.status == "active"])
        total_students += active_enrollments
        total_contact_hours += c.credits  # credit hours equate to weekly teaching load
        courses_summary.append({
            "course_id": c.id,
            "course_code": c.course_code,
            "title": c.title,
            "credits": c.credits,
            "semester": c.semester,
            "year": c.year,
            "active_enrollments": active_enrollments,
            "max_students": c.max_students
        })

    # Update current teaching load on the model
    lecturer.current_teaching_load_hours = total_contact_hours
    await db.commit()

    return LecturerWorkloadSummary(
        lecturer_id=lecturer.lecturer_id,
        full_name=lecturer.user.full_name,
        designation=lecturer.designation,
        employment_status=lecturer.employment_status,
        max_teaching_load_hours=lecturer.max_teaching_load_hours,
        current_teaching_load_hours=total_contact_hours,
        assigned_courses_count=len(lecturer.courses),
        total_enrolled_students=total_students,
        courses=courses_summary
    )
