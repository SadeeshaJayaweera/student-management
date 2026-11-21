"""
NSBM EduSphere — Assignment Submission and Versioning Router
Handles multi-attempt student submissions, attachment metadata, deadline & late penalty calculations,
cryptographic submission receipts, and immutable version audit history.
"""
from typing import List, Optional
from datetime import datetime
import uuid
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    Assignment, AssignmentSubmission, AssignmentSubmissionVersion, AssignmentStatus
)
from backend.schemas import (
    SubmissionCreate, SubmissionOut, SubmissionReceiptOut, SubmissionVersionOut
)
from backend.utils.security import get_current_user
from backend.core.sanitization import sanitize_rich_content
from backend.routers.assignments import verify_course_assignment_access

router = APIRouter(tags=["Assignment Submissions & Versioning"])


def serialize_submission(
    submission: AssignmentSubmission,
    versions: Optional[List[AssignmentSubmissionVersion]] = None
) -> SubmissionOut:
    """Helper to serialize submission with version history"""
    source_versions = versions if versions is not None else (submission.versions or [])
    versions_out = [
        SubmissionVersionOut(
            id=v.id,
            submission_id=v.submission_id,
            version_number=v.version_number,
            file_url=v.file_url,
            text_content=v.text_content,
            attachments=v.attachments,
            submission_receipt=v.submission_receipt,
            is_late=v.is_late,
            days_late=v.days_late,
            submitted_at=v.submitted_at,
        )
        for v in source_versions
    ]

    status_str = submission.status.value if hasattr(submission.status, "value") else str(submission.status)

    return SubmissionOut(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        attempt_number=submission.attempt_number or 1,
        submission_receipt=submission.submission_receipt,
        file_url=submission.file_url,
        text_content=submission.text_content,
        attachments=submission.attachments,
        is_late=submission.is_late,
        days_late=submission.days_late or 0.0,
        late_penalty_applied=submission.late_penalty_applied or 0.0,
        originality_score=submission.originality_score,
        originality_report_url=submission.originality_report_url,
        marks=submission.marks,
        feedback=submission.feedback,
        status=status_str,
        graded_by_id=submission.graded_by_id,
        graded_at=submission.graded_at,
        submitted_at=submission.submitted_at,
        updated_at=submission.updated_at,
        versions=versions_out,
    )


# ─── Submission Endpoints ─────────────────────────────────────────────────────

@router.post("/api/assignments/{assignment_id}/submissions", response_model=SubmissionOut, status_code=201)
async def submit_assignment_attempt(
    assignment_id: int,
    payload: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a new or updated attempt for an assignment.
    Enforces availability dates, cutoff deadlines, max attempts, late policies,
    and captures an immutable version snapshot with a receipt token.
    """
    # 1. Resolve student profile
    res_student = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = res_student.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only registered students can submit assignments."
        )

    # 2. Resolve assignment and verify active enrollment
    q_asg = (
        select(Assignment)
        .where(Assignment.id == assignment_id)
        .options(selectinload(Assignment.course))
    )
    res_asg = await db.execute(q_asg)
    assignment = res_asg.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    await verify_course_assignment_access(assignment.course_id, current_user, db)

    # 3. Check assignment status
    if assignment.status not in {"published", "open"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Assignment is not currently accepting submissions (status: {assignment.status})."
        )

    now = datetime.utcnow()

    # 4. Check availability start date
    if assignment.available_from and now < assignment.available_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment is not yet open for student submissions."
        )

    # 5. Check cutoff date
    if assignment.cutoff_date and now > assignment.cutoff_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment submission cutoff deadline has expired. Submissions are closed."
        )

    # 6. Check due date and calculate late penalty
    is_late = False
    days_late = 0.0
    late_penalty_applied = 0.0

    if assignment.due_date and now > assignment.due_date:
        if not assignment.allow_late_submissions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The assignment deadline has passed, and late submissions are not permitted."
            )
        is_late = True
        seconds_late = (now - assignment.due_date).total_seconds()
        days_late = round(seconds_late / 86400.0, 2)
        late_penalty_applied = min(
            days_late * (assignment.late_penalty_percentage_per_day or 0.0),
            100.0
        )

    # 7. Check existing submission & attempt limit
    q_sub = (
        select(AssignmentSubmission)
        .where(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.student_id == student.id
        )
        .options(selectinload(AssignmentSubmission.versions))
    )
    res_sub = await db.execute(q_sub)
    existing_sub = res_sub.scalar_one_or_none()

    current_attempt = (existing_sub.attempt_number + 1) if existing_sub else 1

    if assignment.max_attempts and assignment.max_attempts > 0:
        if current_attempt > assignment.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum attempt limit ({assignment.max_attempts}) reached for this assignment."
            )

    receipt = f"NSBM-SUB-{uuid.uuid4().hex[:12].upper()}"
    cleaned_text = sanitize_rich_content(payload.text_content) if payload.text_content else None

    if existing_sub:
        existing_sub.attempt_number = current_attempt
        existing_sub.submission_receipt = receipt
        existing_sub.file_url = payload.file_url or existing_sub.file_url
        existing_sub.text_content = cleaned_text or existing_sub.text_content
        existing_sub.attachments = payload.attachments or existing_sub.attachments
        existing_sub.is_late = is_late
        existing_sub.days_late = days_late
        existing_sub.late_penalty_applied = late_penalty_applied
        existing_sub.status = AssignmentStatus.SUBMITTED
        existing_sub.submitted_at = now
        submission = existing_sub
    else:
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student.id,
            attempt_number=current_attempt,
            submission_receipt=receipt,
            file_url=payload.file_url,
            text_content=cleaned_text,
            attachments=payload.attachments,
            is_late=is_late,
            days_late=days_late,
            late_penalty_applied=late_penalty_applied,
            status=AssignmentStatus.SUBMITTED,
            submitted_at=now,
        )
        db.add(submission)
        await db.flush()

    # Create immutable version record for this attempt
    version = AssignmentSubmissionVersion(
        submission_id=submission.id,
        version_number=current_attempt,
        file_url=payload.file_url,
        text_content=cleaned_text,
        attachments=payload.attachments,
        submission_receipt=receipt,
        is_late=is_late,
        days_late=days_late,
        submitted_at=now,
    )
    db.add(version)

    await db.commit()
    await db.refresh(submission)

    # Query latest versions
    v_res = await db.execute(
        select(AssignmentSubmissionVersion)
        .where(AssignmentSubmissionVersion.submission_id == submission.id)
        .order_by(AssignmentSubmissionVersion.version_number.asc())
    )
    versions_list = v_res.scalars().all()

    return serialize_submission(submission, versions=versions_list)


@router.get("/api/assignments/{assignment_id}/submissions/my", response_model=SubmissionOut)
async def get_my_assignment_submission(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current student's submission and version history for an assignment"""
    res_student = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = res_student.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student profile required"
        )

    q = (
        select(AssignmentSubmission)
        .where(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.student_id == student.id
        )
        .options(selectinload(AssignmentSubmission.versions))
    )
    res = await db.execute(q)
    submission = res.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No submission found for this assignment."
        )

    return serialize_submission(submission)


@router.get("/api/assignments/{assignment_id}/submissions", response_model=List[SubmissionOut])
async def list_assignment_submissions(
    assignment_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    is_late_filter: Optional[bool] = Query(None, alias="is_late"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all student submissions for an assignment with audit versioning (Instructors/Admins only)"""
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
            detail="Only instructors and administrators can list all submissions."
        )

    q = (
        select(AssignmentSubmission)
        .where(AssignmentSubmission.assignment_id == assignment_id)
        .options(selectinload(AssignmentSubmission.versions))
        .order_by(AssignmentSubmission.submitted_at.desc())
    )

    if status_filter:
        q = q.where(AssignmentSubmission.status == status_filter.lower().strip())
    if is_late_filter is not None:
        q = q.where(AssignmentSubmission.is_late == is_late_filter)

    res = await db.execute(q)
    submissions = res.scalars().all()

    return [serialize_submission(sub) for sub in submissions]


@router.get("/api/assignments/{assignment_id}/submissions/{submission_id}", response_model=SubmissionOut)
async def get_submission(
    assignment_id: int,
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve submission details by ID with version history (Owner or Instructor/Admin)"""
    q = (
        select(AssignmentSubmission)
        .where(
            AssignmentSubmission.id == submission_id,
            AssignmentSubmission.assignment_id == assignment_id
        )
        .options(
            selectinload(AssignmentSubmission.versions),
            selectinload(AssignmentSubmission.student)
        )
    )
    res = await db.execute(q)
    submission = res.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_owner = bool(submission.student and submission.student.user_id == current_user.id)

    if not (is_admin or is_owner):
        res_asg = await db.execute(
            select(Assignment).where(Assignment.id == assignment_id).options(selectinload(Assignment.course).selectinload(Course.lecturer))
        )
        asg = res_asg.scalar_one_or_none()
        is_instructor = bool(asg and asg.course and asg.course.lecturer and asg.course.lecturer.user_id == current_user.id)
        if not is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot view this submission."
            )

    return serialize_submission(submission)


@router.get("/api/submissions/{submission_id}/receipt", response_model=SubmissionReceiptOut)
async def get_submission_receipt(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and verify digital submission receipt with SHA256 integrity hash"""
    q = (
        select(AssignmentSubmission)
        .where(AssignmentSubmission.id == submission_id)
        .options(
            selectinload(AssignmentSubmission.student).selectinload(Student.user),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.course)
        )
    )
    res = await db.execute(q)
    submission = res.scalar_one_or_none()
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
            submission.assignment.course.lecturer_id and
            getattr(current_user, "lecturer", None) and
            submission.assignment.course.lecturer_id == current_user.lecturer.id
        )
        if not is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot view this receipt."
            )

    asg = submission.assignment
    course = asg.course
    student = submission.student
    student_user = student.user if student else None

    raw_hash_data = f"{submission.submission_receipt}:{submission.assignment_id}:{submission.student_id}:{submission.submitted_at.isoformat()}"
    verification_hash = hashlib.sha256(raw_hash_data.encode()).hexdigest()

    return SubmissionReceiptOut(
        submission_receipt=submission.submission_receipt or f"NSBM-SUB-{submission.id:06d}",
        submission_id=submission.id,
        assignment_id=asg.id,
        assignment_title=asg.title,
        course_code=course.course_code if course else "",
        course_title=course.title if course else "",
        student_id=student.id if student else 0,
        student_name=student_user.full_name if student_user else "Enrolled Student",
        attempt_number=submission.attempt_number or 1,
        is_late=submission.is_late,
        days_late=submission.days_late or 0.0,
        submitted_at=submission.submitted_at,
        verification_hash=verification_hash,
    )
