"""
NSBM EduSphere — Rubric-Based Assessment Engine Router
Provides structured assessment rubrics, criteria, performance levels,
assignment binding, and multi-dimensional grading evaluation workflows.
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
    Assignment, AssignmentSubmission, AssignmentStatus,
    Rubric, RubricCriterion, RubricLevel, RubricEvaluation
)
from backend.schemas import (
    RubricCreate, RubricUpdate, RubricOut,
    RubricCriterionCreate, RubricCriterionOut,
    RubricLevelCreate, RubricLevelOut,
    RubricEvaluationCreate, RubricEvaluationOut,
    AssignmentOut
)
from backend.utils.security import get_current_user
from backend.core.sanitization import sanitize_rich_content
from backend.routers.assignments import verify_course_assignment_access, serialize_assignment

router = APIRouter(tags=["Rubric Assessment Engine"])


async def get_rubric_with_criteria(rubric_id: int, db: AsyncSession) -> Optional[Rubric]:
    """Retrieve rubric with full criteria and levels eager-loaded"""
    q = (
        select(Rubric)
        .where(Rubric.id == rubric_id)
        .options(
            selectinload(Rubric.criteria).selectinload(RubricCriterion.levels),
            selectinload(Rubric.course),
            selectinload(Rubric.creator)
        )
    )
    res = await db.execute(q)
    return res.scalar_one_or_none()


# ─── Course Rubric Management ─────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/rubrics", response_model=RubricOut, status_code=201)
async def create_course_rubric(
    course_id: int,
    payload: RubricCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a structured scoring rubric with criteria and performance levels (Instructors/Admins only)"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can create rubrics."
        )

    # Calculate total points from criteria if provided
    calculated_points = sum(c.max_points for c in (payload.criteria or []))
    total_points = calculated_points if calculated_points > 0 else payload.total_points

    rubric = Rubric(
        course_id=course_id,
        creator_id=current_user.id,
        title=payload.title.strip(),
        description=sanitize_rich_content(payload.description) if payload.description else None,
        scoring_strategy=payload.scoring_strategy.lower().strip(),
        is_template=payload.is_template,
        total_points=total_points,
    )
    db.add(rubric)
    await db.flush()

    for c_idx, crit_in in enumerate(payload.criteria or []):
        criterion = RubricCriterion(
            rubric_id=rubric.id,
            title=crit_in.title.strip(),
            description=sanitize_rich_content(crit_in.description) if crit_in.description else None,
            max_points=crit_in.max_points,
            weight=crit_in.weight,
            order_index=crit_in.order_index if crit_in.order_index is not None else c_idx,
        )
        db.add(criterion)
        await db.flush()

        for l_idx, lvl_in in enumerate(crit_in.levels or []):
            level = RubricLevel(
                criterion_id=criterion.id,
                title=lvl_in.title.strip(),
                description=sanitize_rich_content(lvl_in.description) if lvl_in.description else None,
                point_value=lvl_in.point_value,
                order_index=lvl_in.order_index if lvl_in.order_index is not None else l_idx,
            )
            db.add(level)

    await db.commit()
    full_rubric = await get_rubric_with_criteria(rubric.id, db)
    return full_rubric


@router.get("/api/courses/{course_id}/rubrics", response_model=List[RubricOut])
async def list_course_rubrics(
    course_id: int,
    include_templates: bool = Query(True, description="Include institutional template rubrics"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List rubrics available for a course, including course rubrics and institutional templates"""
    course, _ = await verify_course_assignment_access(course_id, current_user, db)

    conditions = [Rubric.course_id == course_id]
    if include_templates:
        conditions.append(Rubric.is_template == True)

    q = (
        select(Rubric)
        .where(or_(*conditions))
        .options(
            selectinload(Rubric.criteria).selectinload(RubricCriterion.levels)
        )
        .order_by(Rubric.created_at.desc())
    )
    res = await db.execute(q)
    return res.scalars().all()


@router.get("/api/rubrics/{rubric_id}", response_model=RubricOut)
async def get_rubric(
    rubric_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed rubric specification with criteria and performance scale"""
    rubric = await get_rubric_with_criteria(rubric_id, db)
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rubric not found"
        )

    if rubric.course_id:
        await verify_course_assignment_access(rubric.course_id, current_user, db)

    return rubric


@router.patch("/api/rubrics/{rubric_id}", response_model=RubricOut)
async def update_rubric(
    rubric_id: int,
    payload: RubricUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update rubric metadata (Instructors/Admins only)"""
    rubric = await get_rubric_with_criteria(rubric_id, db)
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rubric not found"
        )

    if rubric.course_id:
        _, is_instructor_or_admin = await verify_course_assignment_access(rubric.course_id, current_user, db)
        if not is_instructor_or_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only course instructors and administrators can modify rubrics."
            )

    if payload.title is not None:
        rubric.title = payload.title.strip()
    if payload.description is not None:
        rubric.description = sanitize_rich_content(payload.description)
    if payload.scoring_strategy is not None:
        rubric.scoring_strategy = payload.scoring_strategy.lower().strip()
    if payload.is_template is not None:
        rubric.is_template = payload.is_template
    if payload.total_points is not None:
        rubric.total_points = payload.total_points

    await db.commit()
    return await get_rubric_with_criteria(rubric.id, db)


@router.delete("/api/rubrics/{rubric_id}", status_code=204)
async def delete_rubric(
    rubric_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a rubric if no student evaluations are bound to it (Instructors/Admins only)"""
    rubric = await get_rubric_with_criteria(rubric_id, db)
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rubric not found"
        )

    if rubric.course_id:
        _, is_instructor_or_admin = await verify_course_assignment_access(rubric.course_id, current_user, db)
        if not is_instructor_or_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only course instructors and administrators can delete rubrics."
            )

    # Check if evaluations exist
    eval_count_res = await db.execute(
        select(func.count(RubricEvaluation.id)).where(RubricEvaluation.rubric_id == rubric_id)
    )
    eval_count = eval_count_res.scalar() or 0
    if eval_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete rubric with {eval_count} existing student evaluation(s)."
        )

    await db.delete(rubric)
    await db.commit()


# ─── Assignment Rubric Binding ───────────────────────────────────────────────

@router.post("/api/assignments/{assignment_id}/rubric/{rubric_id}", response_model=AssignmentOut)
async def attach_rubric_to_assignment(
    assignment_id: int,
    rubric_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Attach a grading rubric to an assignment, synchronizing grading type (Instructors/Admins only)"""
    res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can attach rubrics."
        )

    rubric = await get_rubric_with_criteria(rubric_id, db)
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rubric not found"
        )

    if rubric.course_id and rubric.course_id != assignment.course_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rubric belongs to another course and is not an institutional template."
        )

    assignment.rubric_id = rubric.id
    assignment.grading_type = "rubric"
    if rubric.total_points and rubric.total_points > 0:
        assignment.max_marks = rubric.total_points

    await db.commit()
    await db.refresh(assignment)

    count_res = await db.execute(
        select(func.count(AssignmentSubmission.id)).where(AssignmentSubmission.assignment_id == assignment.id)
    )
    count = count_res.scalar() or 0
    return serialize_assignment(assignment, submissions_count=count)


@router.delete("/api/assignments/{assignment_id}/rubric", response_model=AssignmentOut)
async def detach_rubric_from_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Detach rubric from assignment (Instructors/Admins only)"""
    res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can detach rubrics."
        )

    assignment.rubric_id = None
    assignment.grading_type = "points"
    await db.commit()
    await db.refresh(assignment)

    count_res = await db.execute(
        select(func.count(AssignmentSubmission.id)).where(AssignmentSubmission.assignment_id == assignment.id)
    )
    count = count_res.scalar() or 0
    return serialize_assignment(assignment, submissions_count=count)


# ─── Rubric Evaluations and Multi-Dimensional Grading ────────────────────────

@router.post("/api/assignments/{assignment_id}/rubric-evaluations", response_model=RubricEvaluationOut, status_code=201)
async def evaluate_submission_with_rubric(
    assignment_id: int,
    payload: RubricEvaluationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Score a student assignment submission against rubric criteria dimensions.
    Computes total score, percentage, validates score boundaries, and records feedback.
    (Instructors/Admins only)
    """
    res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can evaluate rubrics."
        )

    if not assignment.rubric_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment does not have an attached rubric."
        )

    rubric = await get_rubric_with_criteria(assignment.rubric_id, db)
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attached rubric not found"
        )

    criteria_map = {c.id: c for c in rubric.criteria}
    total_score = 0.0
    criteria_score_records = []

    for item in payload.criteria_scores:
        crit = criteria_map.get(item.criterion_id)
        if not crit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Criterion with ID {item.criterion_id} does not belong to this rubric."
            )
        if item.points > crit.max_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Awarded points ({item.points}) exceed maximum points ({crit.max_points}) for criterion '{crit.title}'."
            )

        total_score += item.points
        criteria_score_records.append({
            "criterion_id": item.criterion_id,
            "level_id": item.level_id,
            "points": item.points,
            "comment": sanitize_rich_content(item.comment) if item.comment else None
        })

    max_possible = rubric.total_points if rubric.total_points > 0 else 100.0
    percentage = round((total_score / max_possible) * 100.0, 2)

    cleaned_feedback = sanitize_rich_content(payload.feedback) if payload.feedback else None

    # Check for existing evaluation for this submission or create new
    existing_eval = None
    if payload.submission_id:
        eval_res = await db.execute(
            select(RubricEvaluation).where(
                RubricEvaluation.assignment_id == assignment_id,
                RubricEvaluation.submission_id == payload.submission_id
            )
        )
        existing_eval = eval_res.scalar_one_or_none()

    if existing_eval:
        evaluation = existing_eval
        evaluation.rubric_id = rubric.id
        evaluation.grader_id = current_user.id
        evaluation.total_score = total_score
        evaluation.max_possible_score = max_possible
        evaluation.percentage = percentage
        evaluation.feedback = cleaned_feedback
        evaluation.criteria_scores = criteria_score_records
    else:
        evaluation = RubricEvaluation(
            rubric_id=rubric.id,
            assignment_id=assignment_id,
            submission_id=payload.submission_id,
            grader_id=current_user.id,
            total_score=total_score,
            max_possible_score=max_possible,
            percentage=percentage,
            feedback=cleaned_feedback,
            criteria_scores=criteria_score_records,
        )
        db.add(evaluation)

    # Sync back to submission marks if submission_id provided
    if payload.submission_id:
        sub_res = await db.execute(
            select(AssignmentSubmission).where(AssignmentSubmission.id == payload.submission_id)
        )
        sub = sub_res.scalar_one_or_none()
        if sub:
            sub.marks = total_score
            sub.feedback = cleaned_feedback
            sub.status = AssignmentStatus.GRADED

    await db.commit()
    await db.refresh(evaluation)

    return evaluation


@router.get("/api/assignments/{assignment_id}/rubric-evaluations/{submission_id}", response_model=RubricEvaluationOut)
async def get_rubric_evaluation(
    assignment_id: int,
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve rubric scoring evaluation for a specific submission"""
    eval_res = await db.execute(
        select(RubricEvaluation)
        .where(
            RubricEvaluation.assignment_id == assignment_id,
            RubricEvaluation.submission_id == submission_id
        )
    )
    evaluation = eval_res.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rubric evaluation not found for this submission."
        )

    # Authorization: Grader/Instructor/Admin or the Student who submitted
    sub_res = await db.execute(
        select(AssignmentSubmission)
        .where(AssignmentSubmission.id == submission_id)
        .options(selectinload(AssignmentSubmission.student))
    )
    submission = sub_res.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_owner_student = bool(submission.student and submission.student.user_id == current_user.id)

    if not (is_admin or is_owner_student):
        # Check course lecturer
        res_course = await db.execute(
            select(Assignment).where(Assignment.id == assignment_id).options(selectinload(Assignment.course).selectinload(Course.lecturer))
        )
        asg = res_course.scalar_one_or_none()
        is_instructor = bool(asg and asg.course and asg.course.lecturer and asg.course.lecturer.user_id == current_user.id)
        if not is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot view this rubric evaluation."
            )

    return evaluation
