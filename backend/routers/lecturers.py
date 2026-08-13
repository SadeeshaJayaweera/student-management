"""NSBM EduSphere — Lecturer Portal Router"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, Lecturer, Course, Student, Enrollment, Grade, Assignment,
    AssignmentSubmission, Attendance, CourseMaterial, Notification
)
from backend.schemas import AssignmentCreate, GradeUpdate
from backend.utils.security import require_roles, get_current_user

router = APIRouter(prefix="/api/lecturers", tags=["Lecturers"])


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


from typing import Optional
