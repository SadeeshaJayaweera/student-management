"""
NSBM EduSphere — AI Automated Essay & Code Grading Assistance Router
Endpoints for submission evaluation, rubric breakdown, lecturer score moderation,
and grading audit analytics.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User
from backend.schemas import (
    AIGradingEvaluateRequest,
    AIAssistedGradingReviewOut,
    AIGradingApproveRequest,
    AIGradingAuditStatsOut,
)
from backend.services.ai_grading_assistant_service import ai_grading_assistant_service
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/ai/grading", tags=["AI Essay & Code Grading Assistance"])


def _check_faculty_role(user: User):
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    if role_str not in ["lecturer", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Access restricted: Only lecturers and academic administrators can access grading assistance"
        )


@router.post("/submissions/{submission_id}/evaluate", response_model=AIAssistedGradingReviewOut, status_code=status.HTTP_201_CREATED)
async def evaluate_student_submission(
    submission_id: int,
    payload: AIGradingEvaluateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run AI evaluation on essay or code submission generating draft score and rubric feedback"""
    _check_faculty_role(current_user)
    try:
        review = await ai_grading_assistant_service.evaluate_submission(
            db=db,
            submission_id=submission_id,
            submission_type=payload.submission_type,
            rubric_id=payload.rubric_id
        )
        return review
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/submissions/{submission_id}/review", response_model=AIAssistedGradingReviewOut)
async def get_submission_grading_review(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve existing AI draft grading evaluation for a submission"""
    _check_faculty_role(current_user)
    review = await ai_grading_assistant_service.get_review_by_submission(db, submission_id)
    if not review:
        raise HTTPException(status_code=404, detail="No grading review found for this submission")
    return review


@router.post("/reviews/{review_id}/approve", response_model=AIAssistedGradingReviewOut)
async def approve_and_finalize_grade(
    review_id: int,
    payload: AIGradingApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lecturer approves or overrides AI suggestions, setting official marks on student submission"""
    _check_faculty_role(current_user)
    try:
        review = await ai_grading_assistant_service.approve_and_finalize_review(
            db=db,
            review_id=review_id,
            lecturer=current_user,
            final_score=payload.final_score,
            lecturer_feedback=payload.lecturer_feedback,
            rubric_adjustments=payload.rubric_adjustments
        )
        return review
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/courses/{course_id}/audit", response_model=AIGradingAuditStatsOut)
async def get_course_grading_audit(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analytics on faculty agreement rate and average score delta vs AI suggested marks"""
    _check_faculty_role(current_user)
    stats = await ai_grading_assistant_service.get_course_grading_audit(db, course_id)
    return stats
