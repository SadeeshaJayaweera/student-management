"""
NSBM EduSphere — AI Quiz & Question Generation Router
Endpoints for automated assessment generation, Bloom's taxonomy item authoring,
rubric extraction, Question Bank export, and Quiz publishing.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User
from backend.schemas import (
    AIQuizGenerateRequest,
    AIQuizGenerationJobOut,
    AIGeneratedQuestionOut,
    PublishQuizRequest,
)
from backend.services.ai_quiz_generator_service import ai_quiz_generator_service
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/ai/quiz-generation", tags=["AI Quiz & Question Generation"])


def _check_faculty_role(user: User):
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    if role_str not in ["lecturer", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only faculty members and administrators can generate and approve quiz items"
        )


@router.post("/generate", response_model=AIQuizGenerationJobOut, status_code=status.HTTP_201_CREATED)
async def generate_quiz_questions(
    payload: AIQuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate structured Bloom's taxonomy quiz items with rationales and rubrics from lecture notes"""
    _check_faculty_role(current_user)
    try:
        job = await ai_quiz_generator_service.generate_questions_job(
            db=db,
            course_id=payload.course_id,
            created_by_user_id=current_user.id,
            source_text=payload.source_text,
            title=payload.title or "Generated Quiz",
            blooms_level=payload.blooms_level,
            difficulty=payload.difficulty,
            question_count=payload.question_count,
            question_types=payload.question_types
        )
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs/{job_id}", response_model=AIQuizGenerationJobOut)
async def get_quiz_generation_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full generation job and its individual question items"""
    _check_faculty_role(current_user)
    try:
        job = await ai_quiz_generator_service.get_job_details(db, job_id)
        return job
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/courses/{course_id}/jobs", response_model=List[AIQuizGenerationJobOut])
async def list_course_generation_jobs(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List historical quiz generation jobs for a course"""
    _check_faculty_role(current_user)
    jobs = await ai_quiz_generator_service.list_course_jobs(db, course_id)
    return jobs


@router.post("/questions/{question_id}/approve")
async def approve_question_and_export(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve a generated question item and export it into the Course Question Bank"""
    _check_faculty_role(current_user)
    try:
        bank_item = await ai_quiz_generator_service.approve_and_export_question(
            db=db,
            question_id=question_id,
            creator=current_user
        )
        return {
            "question_id": question_id,
            "question_bank_item_id": bank_item.id,
            "status": "approved_and_exported"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/jobs/{job_id}/publish-quiz")
async def publish_job_as_quiz(
    job_id: int,
    payload: PublishQuizRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Publish the approved questions from a generation job into a live student-facing Quiz"""
    _check_faculty_role(current_user)
    try:
        quiz = await ai_quiz_generator_service.publish_job_as_live_quiz(
            db=db,
            job_id=job_id,
            creator=current_user,
            title=payload.title,
            time_limit_minutes=payload.time_limit_minutes
        )
        return {
            "quiz_id": quiz.id,
            "course_id": quiz.course_id,
            "title": quiz.title,
            "status": quiz.status,
            "due_date": quiz.due_date.isoformat(),
            "questions_count": len(quiz.questions)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
