"""
NSBM EduSphere — Assignment Lifecycle Architecture Router
Provides complete academic assignment authoring, scheduling, availability windows,
late submission policies, weighting, and state transitions with strict BOLA authorization.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Course, Lecturer, Student, Enrollment,
    Assignment, AssignmentSubmission
)
from backend.schemas import (
    AssignmentCreate, AssignmentUpdate, AssignmentOut
)
from backend.utils.security import get_current_user
from backend.core.sanitization import sanitize_rich_content

router = APIRouter(tags=["Assignment Lifecycle"])


async def verify_course_assignment_access(
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
            detail="Access denied: You must be enrolled in or teaching this course to access assignments."
        )

    return course, False


def serialize_assignment(assignment: Assignment, submissions_count: int = 0) -> AssignmentOut:
    """Helper to serialize assignment ORM model with computed timing attributes"""
    now = datetime.utcnow()
    is_available = True
    if assignment.available_from and assignment.available_from > now:
        is_available = False

    is_past_due = bool(assignment.due_date and assignment.due_date < now)
    is_past_cutoff = bool(assignment.cutoff_date and assignment.cutoff_date < now)

    return AssignmentOut(
        id=assignment.id,
        course_id=assignment.course_id,
        creator_id=assignment.creator_id,
        module_id=assignment.module_id,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date,
        available_from=assignment.available_from,
        cutoff_date=assignment.cutoff_date,
        max_marks=assignment.max_marks or 100.0,
        weightage_percentage=assignment.weightage_percentage or 10.0,
        assignment_type=assignment.assignment_type or "assignment",
        grading_type=assignment.grading_type or "points",
        status=assignment.status or "published",
        allow_late_submissions=assignment.allow_late_submissions,
        late_penalty_percentage_per_day=assignment.late_penalty_percentage_per_day or 0.0,
        submission_types=assignment.submission_types or ["file", "text"],
        allowed_file_extensions=assignment.allowed_file_extensions or [".pdf", ".zip", ".docx"],
        max_file_size_mb=assignment.max_file_size_mb or 50,
        max_attempts=assignment.max_attempts or 1,
        anonymous_grading=assignment.anonymous_grading,
        peer_review_enabled=assignment.peer_review_enabled,
        group_assignment=assignment.group_assignment,
        file_url=assignment.file_url,
        published_at=assignment.published_at,
        submissions_count=submissions_count,
        is_available=is_available,
        is_past_due=is_past_due,
        is_past_cutoff=is_past_cutoff,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


# ─── Assignment Endpoints ─────────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/assignments", response_model=AssignmentOut, status_code=201)
async def create_course_assignment(
    course_id: int,
    payload: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Author a new academic assignment in draft or published lifecycle state (Instructors/Admins only)"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can create assignments."
        )

    # Validate dates
    if payload.available_from and payload.due_date <= payload.available_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment due date must be after the available_from date."
        )

    if payload.cutoff_date and payload.cutoff_date < payload.due_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cutoff date cannot be earlier than due date."
        )

    cleaned_desc = sanitize_rich_content(payload.description) if payload.description else None
    assignment_status = payload.status.lower().strip()
    published_at = datetime.utcnow() if assignment_status == "published" else None

    assignment = Assignment(
        course_id=course_id,
        creator_id=current_user.id,
        module_id=payload.module_id,
        title=payload.title.strip(),
        description=cleaned_desc,
        due_date=payload.due_date,
        available_from=payload.available_from,
        cutoff_date=payload.cutoff_date,
        max_marks=payload.max_marks,
        weightage_percentage=payload.weightage_percentage,
        assignment_type=payload.assignment_type.lower().strip(),
        grading_type=payload.grading_type.lower().strip(),
        status=assignment_status,
        allow_late_submissions=payload.allow_late_submissions,
        late_penalty_percentage_per_day=payload.late_penalty_percentage_per_day,
        submission_types=payload.submission_types or ["file", "text"],
        allowed_file_extensions=payload.allowed_file_extensions or [".pdf", ".zip", ".docx"],
        max_file_size_mb=payload.max_file_size_mb,
        max_attempts=payload.max_attempts,
        anonymous_grading=payload.anonymous_grading,
        peer_review_enabled=payload.peer_review_enabled,
        group_assignment=payload.group_assignment,
        file_url=payload.file_url,
        published_at=published_at,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    return serialize_assignment(assignment, submissions_count=0)


@router.get("/api/courses/{course_id}/assignments", response_model=List[AssignmentOut])
async def list_course_assignments(
    course_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (e.g. published, draft, closed)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all assignments for a course with role-scoped lifecycle visibility"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)

    q = (
        select(
            Assignment,
            func.count(AssignmentSubmission.id).label("submissions_count")
        )
        .outerjoin(AssignmentSubmission, AssignmentSubmission.assignment_id == Assignment.id)
        .where(Assignment.course_id == course_id)
        .group_by(Assignment.id)
    )

    if not is_instructor_or_admin:
        # Students can only see published/closed assignments (never drafts or archived)
        q = q.where(Assignment.status.in_(["published", "open", "closed", "grading", "graded"]))

    if status_filter:
        q = q.where(Assignment.status == status_filter.lower().strip())

    q = q.order_by(Assignment.due_date.asc())
    res = await db.execute(q)
    rows = res.all()

    return [serialize_assignment(assignment, submissions_count=count or 0) for assignment, count in rows]


@router.get("/api/assignments/{assignment_id}", response_model=AssignmentOut)
async def get_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single assignment with availability window validation"""
    q = (
        select(
            Assignment,
            func.count(AssignmentSubmission.id).label("submissions_count")
        )
        .outerjoin(AssignmentSubmission, AssignmentSubmission.assignment_id == Assignment.id)
        .where(Assignment.id == assignment_id)
        .group_by(Assignment.id)
    )
    res = await db.execute(q)
    row = res.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    assignment, count = row
    course, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)

    if not is_instructor_or_admin:
        if assignment.status in {"draft", "archived"}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment is not currently published."
            )

    return serialize_assignment(assignment, submissions_count=count or 0)


@router.patch("/api/assignments/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update assignment parameters, deadlines, and policies (Instructors/Admins only)"""
    res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    course, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can edit assignments."
        )

    if payload.title is not None:
        assignment.title = payload.title.strip()
    if payload.description is not None:
        assignment.description = sanitize_rich_content(payload.description)
    if payload.module_id is not None:
        assignment.module_id = payload.module_id
    if payload.due_date is not None:
        assignment.due_date = payload.due_date
    if payload.available_from is not None:
        assignment.available_from = payload.available_from
    if payload.cutoff_date is not None:
        assignment.cutoff_date = payload.cutoff_date
    if payload.max_marks is not None:
        assignment.max_marks = payload.max_marks
    if payload.weightage_percentage is not None:
        assignment.weightage_percentage = payload.weightage_percentage
    if payload.assignment_type is not None:
        assignment.assignment_type = payload.assignment_type.lower().strip()
    if payload.grading_type is not None:
        assignment.grading_type = payload.grading_type.lower().strip()
    if payload.status is not None:
        new_status = payload.status.lower().strip()
        if new_status == "published" and assignment.status == "draft":
            assignment.published_at = datetime.utcnow()
        assignment.status = new_status
    if payload.allow_late_submissions is not None:
        assignment.allow_late_submissions = payload.allow_late_submissions
    if payload.late_penalty_percentage_per_day is not None:
        assignment.late_penalty_percentage_per_day = payload.late_penalty_percentage_per_day
    if payload.submission_types is not None:
        assignment.submission_types = payload.submission_types
    if payload.allowed_file_extensions is not None:
        assignment.allowed_file_extensions = payload.allowed_file_extensions
    if payload.max_file_size_mb is not None:
        assignment.max_file_size_mb = payload.max_file_size_mb
    if payload.max_attempts is not None:
        assignment.max_attempts = payload.max_attempts
    if payload.anonymous_grading is not None:
        assignment.anonymous_grading = payload.anonymous_grading
    if payload.peer_review_enabled is not None:
        assignment.peer_review_enabled = payload.peer_review_enabled
    if payload.group_assignment is not None:
        assignment.group_assignment = payload.group_assignment
    if payload.file_url is not None:
        assignment.file_url = payload.file_url

    await db.commit()
    await db.refresh(assignment)

    count_res = await db.execute(
        select(func.count(AssignmentSubmission.id)).where(AssignmentSubmission.assignment_id == assignment.id)
    )
    count = count_res.scalar() or 0

    return serialize_assignment(assignment, submissions_count=count)


@router.post("/api/assignments/{assignment_id}/publish", response_model=AssignmentOut)
async def publish_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish an assignment draft, transitioning it to the active published lifecycle state"""
    res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    course, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can publish assignments."
        )

    assignment.status = "published"
    assignment.published_at = datetime.utcnow()
    await db.commit()
    await db.refresh(assignment)

    return serialize_assignment(assignment, submissions_count=0)


@router.post("/api/assignments/{assignment_id}/close", response_model=AssignmentOut)
async def close_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Close an assignment for student submissions (Instructors/Admins only)"""
    res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    course, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can close assignments."
        )

    assignment.status = "closed"
    await db.commit()
    await db.refresh(assignment)

    count_res = await db.execute(
        select(func.count(AssignmentSubmission.id)).where(AssignmentSubmission.assignment_id == assignment.id)
    )
    count = count_res.scalar() or 0

    return serialize_assignment(assignment, submissions_count=count)


@router.delete("/api/assignments/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an assignment if no student submissions exist (Instructors/Admins only)"""
    res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    course, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can delete assignments."
        )

    # Check for existing submissions
    sub_res = await db.execute(
        select(func.count(AssignmentSubmission.id)).where(AssignmentSubmission.assignment_id == assignment.id)
    )
    count = sub_res.scalar() or 0
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete assignment with {count} student submission(s). Archive or close it instead."
        )

    await db.delete(assignment)
    await db.commit()
