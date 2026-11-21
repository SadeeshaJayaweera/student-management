"""
NSBM EduSphere — Question Bank and Question Types Router
Provides multi-type question authoring, taxonomical categorization, difficulty calibration,
and secure storage for objective and subjective assessment items.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Course, Lecturer,
    QuestionCategory, QuestionBankItem, Rubric
)
from backend.schemas import (
    QuestionCategoryCreate, QuestionCategoryOut,
    QuestionBankItemCreate, QuestionBankItemUpdate, QuestionBankItemOut
)
from backend.utils.security import get_current_user
from backend.core.sanitization import sanitize_rich_content
from backend.routers.assignments import verify_course_assignment_access

router = APIRouter(tags=["Question Bank & Item Management"])

VALID_QUESTION_TYPES = {
    "single_choice",
    "multiple_choice",
    "true_false",
    "short_answer",
    "essay",
    "code_snippet",
    "numerical"
}

VALID_DIFFICULTY_LEVELS = {
    "beginner",
    "intermediate",
    "advanced",
    "expert"
}


def serialize_question_category(cat: QuestionCategory, count: int = 0) -> QuestionCategoryOut:
    return QuestionCategoryOut(
        id=cat.id,
        course_id=cat.course_id,
        parent_id=cat.parent_id,
        name=cat.name,
        description=cat.description,
        display_order=cat.display_order,
        questions_count=count,
        created_at=cat.created_at,
        updated_at=cat.updated_at,
    )


def serialize_question_bank_item(item: QuestionBankItem) -> QuestionBankItemOut:
    return QuestionBankItemOut(
        id=item.id,
        course_id=item.course_id,
        category_id=item.category_id,
        creator_id=item.creator_id,
        rubric_id=item.rubric_id,
        title=item.title,
        prompt=item.prompt,
        question_type=item.question_type,
        difficulty_level=item.difficulty_level,
        default_points=item.default_points,
        explanation=item.explanation,
        tags=item.tags,
        options=item.options,
        answer_key=item.answer_key,
        is_active=item.is_active,
        usage_count=item.usage_count,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


# ─── Category Endpoints ───────────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/question-categories", response_model=QuestionCategoryOut, status_code=201)
async def create_question_category(
    course_id: int,
    payload: QuestionCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new taxonomy category in the question bank (Instructors/Admins only)"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can manage question categories."
        )

    cat = QuestionCategory(
        course_id=course_id,
        parent_id=payload.parent_id,
        name=payload.name.strip(),
        description=sanitize_rich_content(payload.description) if payload.description else None,
        display_order=payload.display_order,
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)

    return serialize_question_category(cat, 0)


@router.get("/api/courses/{course_id}/question-categories", response_model=List[QuestionCategoryOut])
async def list_question_categories(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all question bank categories for a course with item counts"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students cannot browse question categories."
        )

    q = (
        select(
            QuestionCategory,
            func.count(QuestionBankItem.id).label("questions_count")
        )
        .outerjoin(QuestionBankItem, QuestionBankItem.category_id == QuestionCategory.id)
        .where(QuestionCategory.course_id == course_id)
        .group_by(QuestionCategory.id)
        .order_by(QuestionCategory.display_order.asc(), QuestionCategory.name.asc())
    )
    res = await db.execute(q)
    rows = res.all()

    return [serialize_question_category(cat, count or 0) for cat, count in rows]


# ─── Question Bank Items ──────────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/questions", response_model=QuestionBankItemOut, status_code=201)
async def create_question_bank_item(
    course_id: int,
    payload: QuestionBankItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a validated question bank item across supported assessment types (Instructors/Admins only)"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can author questions in the bank."
        )

    q_type = payload.question_type.lower().strip()
    if q_type not in VALID_QUESTION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid question type '{payload.question_type}'. Supported types: {list(VALID_QUESTION_TYPES)}"
        )

    difficulty = payload.difficulty_level.lower().strip()
    if difficulty not in VALID_DIFFICULTY_LEVELS:
        difficulty = "intermediate"

    # Type-specific validation
    options_data = None
    if q_type in {"single_choice", "multiple_choice", "true_false"}:
        if not payload.options or len(payload.options) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question type '{q_type}' requires at least two options."
            )
        has_correct = any(opt.is_correct for opt in payload.options)
        if not has_correct:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question type '{q_type}' requires at least one correct option."
            )
        options_data = [
            {
                "id": opt.id,
                "text": sanitize_rich_content(opt.text),
                "is_correct": opt.is_correct,
                "feedback": sanitize_rich_content(opt.feedback) if opt.feedback else None,
            }
            for opt in payload.options
        ]
    elif payload.options:
        options_data = [
            {
                "id": opt.id,
                "text": sanitize_rich_content(opt.text),
                "is_correct": opt.is_correct,
                "feedback": sanitize_rich_content(opt.feedback) if opt.feedback else None,
            }
            for opt in payload.options
        ]

    item = QuestionBankItem(
        course_id=course_id,
        category_id=payload.category_id,
        creator_id=current_user.id,
        rubric_id=payload.rubric_id,
        title=payload.title.strip(),
        prompt=sanitize_rich_content(payload.prompt),
        question_type=q_type,
        difficulty_level=difficulty,
        default_points=payload.default_points,
        explanation=sanitize_rich_content(payload.explanation) if payload.explanation else None,
        tags=payload.tags or [],
        options=options_data,
        answer_key=payload.answer_key,
        is_active=payload.is_active,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return serialize_question_bank_item(item)


@router.get("/api/courses/{course_id}/questions", response_model=List[QuestionBankItemOut])
async def list_question_bank_items(
    course_id: int,
    category_id: Optional[int] = Query(None),
    question_type: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query question bank items with granular search, type, and difficulty filtering (Instructors/Admins only)"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students cannot browse the question bank."
        )

    q = select(QuestionBankItem).where(QuestionBankItem.course_id == course_id)

    if category_id is not None:
        q = q.where(QuestionBankItem.category_id == category_id)
    if question_type:
        q = q.where(QuestionBankItem.question_type == question_type.lower().strip())
    if difficulty:
        q = q.where(QuestionBankItem.difficulty_level == difficulty.lower().strip())
    if search:
        search_pattern = f"%{search.strip()}%"
        q = q.where(
            or_(
                QuestionBankItem.title.ilike(search_pattern),
                QuestionBankItem.prompt.ilike(search_pattern)
            )
        )

    q = q.order_by(QuestionBankItem.created_at.desc())
    res = await db.execute(q)
    items = res.scalars().all()

    if tag:
        tag_lower = tag.lower().strip()
        items = [item for item in items if item.tags and any(t.lower() == tag_lower for t in item.tags)]

    return [serialize_question_bank_item(item) for item in items]


@router.get("/api/questions/{question_id}", response_model=QuestionBankItemOut)
async def get_question_bank_item(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full specification for an individual question bank item"""
    res = await db.execute(select(QuestionBankItem).where(QuestionBankItem.id == question_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    if item.course_id:
        _, is_instructor_or_admin = await verify_course_assignment_access(item.course_id, current_user, db)
        if not is_instructor_or_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Question bank items are restricted to instructors."
            )

    return serialize_question_bank_item(item)


@router.patch("/api/questions/{question_id}", response_model=QuestionBankItemOut)
async def update_question_bank_item(
    question_id: int,
    payload: QuestionBankItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update question bank item prompt, options, answer key, or difficulty (Instructors/Admins only)"""
    res = await db.execute(select(QuestionBankItem).where(QuestionBankItem.id == question_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    if item.course_id:
        _, is_instructor_or_admin = await verify_course_assignment_access(item.course_id, current_user, db)
        if not is_instructor_or_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors and administrators can edit questions."
            )

    if payload.title is not None:
        item.title = payload.title.strip()
    if payload.prompt is not None:
        item.prompt = sanitize_rich_content(payload.prompt)
    if payload.category_id is not None:
        item.category_id = payload.category_id
    if payload.rubric_id is not None:
        item.rubric_id = payload.rubric_id
    if payload.question_type is not None:
        q_type = payload.question_type.lower().strip()
        if q_type in VALID_QUESTION_TYPES:
            item.question_type = q_type
    if payload.difficulty_level is not None:
        diff = payload.difficulty_level.lower().strip()
        if diff in VALID_DIFFICULTY_LEVELS:
            item.difficulty_level = diff
    if payload.default_points is not None:
        item.default_points = payload.default_points
    if payload.explanation is not None:
        item.explanation = sanitize_rich_content(payload.explanation)
    if payload.tags is not None:
        item.tags = payload.tags
    if payload.options is not None:
        item.options = [
            {
                "id": opt.id,
                "text": sanitize_rich_content(opt.text),
                "is_correct": opt.is_correct,
                "feedback": sanitize_rich_content(opt.feedback) if opt.feedback else None,
            }
            for opt in payload.options
        ]
    if payload.answer_key is not None:
        item.answer_key = payload.answer_key
    if payload.is_active is not None:
        item.is_active = payload.is_active

    await db.commit()
    await db.refresh(item)
    return serialize_question_bank_item(item)


@router.delete("/api/questions/{question_id}", status_code=204)
async def delete_question_bank_item(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a question from the question bank (Instructors/Admins only)"""
    res = await db.execute(select(QuestionBankItem).where(QuestionBankItem.id == question_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    if item.course_id:
        _, is_instructor_or_admin = await verify_course_assignment_access(item.course_id, current_user, db)
        if not is_instructor_or_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors and administrators can delete questions."
            )

    await db.delete(item)
    await db.commit()


@router.post("/api/courses/{course_id}/questions/bulk-import", response_model=List[QuestionBankItemOut], status_code=201)
async def bulk_import_questions(
    course_id: int,
    questions: List[QuestionBankItemCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bulk import multiple questions into the course question bank (Instructors/Admins only)"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can bulk-import questions."
        )

    created_items = []
    for q_in in questions:
        q_type = q_in.question_type.lower().strip()
        diff = q_in.difficulty_level.lower().strip()
        if diff not in VALID_DIFFICULTY_LEVELS:
            diff = "intermediate"

        options_data = None
        if q_in.options:
            options_data = [
                {
                    "id": opt.id,
                    "text": sanitize_rich_content(opt.text),
                    "is_correct": opt.is_correct,
                    "feedback": sanitize_rich_content(opt.feedback) if opt.feedback else None,
                }
                for opt in q_in.options
            ]

        item = QuestionBankItem(
            course_id=course_id,
            category_id=q_in.category_id,
            creator_id=current_user.id,
            rubric_id=q_in.rubric_id,
            title=q_in.title.strip(),
            prompt=sanitize_rich_content(q_in.prompt),
            question_type=q_type,
            difficulty_level=diff,
            default_points=q_in.default_points,
            explanation=sanitize_rich_content(q_in.explanation) if q_in.explanation else None,
            tags=q_in.tags or [],
            options=options_data,
            answer_key=q_in.answer_key,
            is_active=q_in.is_active,
        )
        db.add(item)
        created_items.append(item)

    await db.commit()
    for it in created_items:
        await db.refresh(it)

    return [serialize_question_bank_item(it) for it in created_items]
