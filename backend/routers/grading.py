"""
NSBM EduSphere — Grading Workflows and Feedback Delivery Router
Provides speed-grading endpoints, inline submission annotations, rubric synchronization,
grade publishing lifecycle release, and student grade dispute/appeal workflows.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Course, Student, Lecturer,
    Assignment, AssignmentSubmission, AssignmentSubmissionVersion, AssignmentStatus,
    SubmissionAnnotation, GradeAppeal, RubricEvaluation
)
from backend.schemas import (
    SubmissionGradePayload, SubmissionOut,
    SubmissionAnnotationCreate, SubmissionAnnotationOut,
    GradeAppealCreate, GradeAppealResolve, GradeAppealOut,
    AssignmentGradeReleaseOut
)
from backend.utils.security import get_current_user
from backend.core.sanitization import sanitize_rich_content
from backend.routers.assignments import verify_course_assignment_access
from backend.routers.submissions import serialize_submission

router = APIRouter(tags=["Grading Workflows & Feedback Delivery"])


def serialize_annotation(annotation: SubmissionAnnotation) -> SubmissionAnnotationOut:
    return SubmissionAnnotationOut(
        id=annotation.id,
        submission_id=annotation.submission_id,
        page_number=annotation.page_number,
        coordinates=annotation.coordinates,
        comment_text=annotation.comment_text,
        author_id=annotation.author_id,
        created_at=annotation.created_at,
        updated_at=annotation.updated_at,
    )


def serialize_appeal(appeal: GradeAppeal) -> GradeAppealOut:
    return GradeAppealOut(
        id=appeal.id,
        assignment_id=appeal.assignment_id,
        submission_id=appeal.submission_id,
        student_id=appeal.student_id,
        reason=appeal.reason,
        requested_marks=appeal.requested_marks,
        status=appeal.status,
        resolution_notes=appeal.resolution_notes,
        resolved_by_id=appeal.resolved_by_id,
        resolved_at=appeal.resolved_at,
        created_at=appeal.created_at,
        updated_at=appeal.updated_at,
    )


# ─── Grading Endpoints ────────────────────────────────────────────────────────

@router.post("/api/submissions/{submission_id}/grade", response_model=SubmissionOut)
async def grade_student_submission(
    submission_id: int,
    payload: SubmissionGradePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grade student submission with points, qualitative feedback, and audit metadata (Instructors/Admins only)"""
    res_sub = await db.execute(
        select(AssignmentSubmission)
        .where(AssignmentSubmission.id == submission_id)
        .options(
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.course),
            selectinload(AssignmentSubmission.versions)
        )
    )
    submission = res_sub.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    assignment = submission.assignment
    _, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can grade submissions."
        )

    if payload.marks > assignment.max_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Marks ({payload.marks}) exceed maximum allowable score ({assignment.max_marks})."
        )

    submission.marks = payload.marks
    submission.feedback = sanitize_rich_content(payload.feedback) if payload.feedback else None
    submission.status = AssignmentStatus.GRADED
    submission.graded_by_id = current_user.id
    submission.graded_at = datetime.utcnow()

    await db.commit()
    await db.refresh(submission)

    res_versions = await db.execute(
        select(AssignmentSubmissionVersion)
        .where(AssignmentSubmissionVersion.submission_id == submission_id)
        .order_by(AssignmentSubmissionVersion.version_number.asc())
    )
    versions = res_versions.scalars().all()

    return serialize_submission(submission, versions=versions)


@router.post("/api/assignments/{assignment_id}/release-grades", response_model=AssignmentGradeReleaseOut)
async def release_assignment_grades(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Release all graded evaluations for an assignment to students (Instructors/Admins only)"""
    res_asg = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res_asg.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can publish grade releases."
        )

    now = datetime.utcnow()
    assignment.grades_released = True
    assignment.grades_released_at = now

    graded_count_res = await db.execute(
        select(func.count(AssignmentSubmission.id)).where(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.status == AssignmentStatus.GRADED
        )
    )
    graded_count = graded_count_res.scalar() or 0

    await db.commit()

    return AssignmentGradeReleaseOut(
        assignment_id=assignment.id,
        grades_released=True,
        grades_released_at=now,
        submissions_graded_count=graded_count,
    )


# ─── Submission Annotations ───────────────────────────────────────────────────

@router.post("/api/submissions/{submission_id}/annotations", response_model=SubmissionAnnotationOut, status_code=201)
async def add_submission_annotation(
    submission_id: int,
    payload: SubmissionAnnotationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add inline document annotation or contextual comment (Instructors/Admins only)"""
    res_sub = await db.execute(
        select(AssignmentSubmission)
        .where(AssignmentSubmission.id == submission_id)
        .options(selectinload(AssignmentSubmission.assignment))
    )
    submission = res_sub.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(submission.assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can add inline annotations."
        )

    annotation = SubmissionAnnotation(
        submission_id=submission_id,
        page_number=payload.page_number,
        coordinates=payload.coordinates,
        comment_text=sanitize_rich_content(payload.comment_text),
        author_id=current_user.id,
    )
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)

    return serialize_annotation(annotation)


@router.get("/api/submissions/{submission_id}/annotations", response_model=List[SubmissionAnnotationOut])
async def list_submission_annotations(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List inline annotations for a submission (Instructor/Admin or Student owner)"""
    res_sub = await db.execute(
        select(AssignmentSubmission)
        .where(AssignmentSubmission.id == submission_id)
        .options(
            selectinload(AssignmentSubmission.student),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.course)
        )
    )
    submission = res_sub.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_owner = bool(submission.student and submission.student.user_id == current_user.id)

    if not (is_admin or is_owner):
        is_instructor = bool(
            submission.assignment and submission.assignment.course and
            getattr(current_user, "lecturer", None) and
            submission.assignment.course.lecturer_id == current_user.lecturer.id
        )
        if not is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot view annotations for this submission."
            )

    res_ann = await db.execute(
        select(SubmissionAnnotation)
        .where(SubmissionAnnotation.submission_id == submission_id)
        .order_by(SubmissionAnnotation.created_at.asc())
    )
    annotations = res_ann.scalars().all()

    return [serialize_annotation(ann) for ann in annotations]


@router.delete("/api/submissions/{submission_id}/annotations/{annotation_id}", status_code=204)
async def delete_submission_annotation(
    submission_id: int,
    annotation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an inline annotation (Author or Admin only)"""
    res = await db.execute(
        select(SubmissionAnnotation).where(
            SubmissionAnnotation.id == annotation_id,
            SubmissionAnnotation.submission_id == submission_id
        )
    )
    annotation = res.scalar_one_or_none()
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_author = annotation.author_id == current_user.id

    if not (is_admin or is_author):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author or an administrator can delete this annotation."
        )

    await db.delete(annotation)
    await db.commit()


# ─── Grade Appeals ────────────────────────────────────────────────────────────

@router.post("/api/submissions/{submission_id}/appeals", response_model=GradeAppealOut, status_code=201)
async def submit_grade_appeal(
    submission_id: int,
    payload: GradeAppealCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a formal grade appeal / regrade request for a graded submission"""
    res_student = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = res_student.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit grade appeals."
        )

    res_sub = await db.execute(
        select(AssignmentSubmission).where(
            AssignmentSubmission.id == submission_id,
            AssignmentSubmission.student_id == student.id
        )
    )
    submission = res_sub.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found or does not belong to you."
        )

    if submission.marks is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit grade appeal for an ungraded submission."
        )

    appeal = GradeAppeal(
        assignment_id=submission.assignment_id,
        submission_id=submission.id,
        student_id=student.id,
        reason=sanitize_rich_content(payload.reason),
        requested_marks=payload.requested_marks,
        status="pending",
    )
    db.add(appeal)
    await db.commit()
    await db.refresh(appeal)

    return serialize_appeal(appeal)


@router.get("/api/assignments/{assignment_id}/appeals", response_model=List[GradeAppealOut])
async def list_assignment_grade_appeals(
    assignment_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List student grade appeals for an assignment (Instructors/Admins only)"""
    res_asg = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res_asg.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can list grade appeals."
        )

    q = select(GradeAppeal).where(GradeAppeal.assignment_id == assignment_id)
    if status_filter:
        q = q.where(GradeAppeal.status == status_filter.lower().strip())

    q = q.order_by(GradeAppeal.created_at.desc())
    res = await db.execute(q)
    appeals = res.scalars().all()

    return [serialize_appeal(app) for app in appeals]


@router.post("/api/appeals/{appeal_id}/resolve", response_model=GradeAppealOut)
async def resolve_grade_appeal(
    appeal_id: int,
    payload: GradeAppealResolve,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve student grade appeal with resolution notes and optional mark adjustment (Instructors/Admins only)"""
    res_app = await db.execute(
        select(GradeAppeal)
        .where(GradeAppeal.id == appeal_id)
        .options(
            selectinload(GradeAppeal.assignment),
            selectinload(GradeAppeal.submission)
        )
    )
    appeal = res_app.scalar_one_or_none()
    if not appeal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade appeal not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(appeal.assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can resolve grade appeals."
        )

    resolution_status = payload.status.lower().strip()
    appeal.status = resolution_status
    appeal.resolution_notes = sanitize_rich_content(payload.resolution_notes)
    appeal.resolved_by_id = current_user.id
    appeal.resolved_at = datetime.utcnow()

    # Adjust marks if appeal is approved and adjusted_marks provided
    if resolution_status == "approved" and payload.adjusted_marks is not None:
        if payload.adjusted_marks > appeal.assignment.max_marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Adjusted marks ({payload.adjusted_marks}) exceed maximum marks ({appeal.assignment.max_marks})."
            )
        appeal.submission.marks = payload.adjusted_marks
        appeal.submission.feedback = (
            f"{appeal.submission.feedback or ''}\n\n[Regrade Resolution: {appeal.resolution_notes}]"
        ).strip()

    await db.commit()
    await db.refresh(appeal)

    return serialize_appeal(appeal)
