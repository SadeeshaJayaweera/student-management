"""
NSBM EduSphere — Automated Quiz and Assessment Engine Router
Handles quiz configuration, randomized question delivery, student attempt lifecycles,
autosave, objective auto-grading algorithms, and instant feedback computation.
"""
from typing import List, Optional
from datetime import datetime, timedelta
import random

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    QuestionBankItem, Quiz, QuizQuestion, QuizAttempt
)
from backend.schemas import (
    QuizCreate, QuizUpdate, QuizOut,
    QuizQuestionAdd, QuizQuestionOut,
    StudentQuizQuestionOut, QuizStartOut,
    QuizAutosavePayload, QuizSubmitPayload, QuizAttemptOut,
    QuestionBankItemOut
)
from backend.utils.security import get_current_user
from backend.core.sanitization import sanitize_rich_content
from backend.routers.assignments import verify_course_assignment_access

router = APIRouter(tags=["Automated Quiz & Assessment Engine"])


def serialize_quiz(quiz: Quiz, count: int = 0) -> QuizOut:
    return QuizOut(
        id=quiz.id,
        course_id=quiz.course_id,
        module_id=quiz.module_id,
        creator_id=quiz.creator_id,
        title=quiz.title,
        description=quiz.description,
        instructions=quiz.instructions,
        time_limit_minutes=quiz.time_limit_minutes,
        passing_score_percentage=quiz.passing_score_percentage or 50.0,
        max_attempts=quiz.max_attempts or 1,
        shuffle_questions=quiz.shuffle_questions,
        shuffle_options=quiz.shuffle_options,
        show_correct_answers=quiz.show_correct_answers,
        allow_backtracking=quiz.allow_backtracking,
        total_points=quiz.total_points or 0.0,
        status=quiz.status or "published",
        available_from=quiz.available_from,
        due_date=quiz.due_date,
        questions_count=count,
        created_at=quiz.created_at,
        updated_at=quiz.updated_at,
    )


def serialize_quiz_attempt(attempt: QuizAttempt, results: Optional[List[dict]] = None) -> QuizAttemptOut:
    return QuizAttemptOut(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        student_id=attempt.student_id,
        attempt_number=attempt.attempt_number or 1,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        total_score=attempt.total_score or 0.0,
        max_score=attempt.max_score or 0.0,
        percentage=attempt.percentage or 0.0,
        is_passed=attempt.is_passed,
        status=attempt.status or "in_progress",
        results=results if results is not None else (attempt.answers or []),
        created_at=attempt.created_at,
    )


# ─── Quiz Management Endpoints ────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/quizzes", response_model=QuizOut, status_code=201)
async def create_course_quiz(
    course_id: int,
    payload: QuizCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new automated quiz or assessment (Instructors/Admins only)"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can create quizzes."
        )

    quiz = Quiz(
        course_id=course_id,
        module_id=payload.module_id,
        creator_id=current_user.id,
        title=payload.title.strip(),
        description=sanitize_rich_content(payload.description) if payload.description else None,
        instructions=sanitize_rich_content(payload.instructions) if payload.instructions else None,
        time_limit_minutes=payload.time_limit_minutes,
        passing_score_percentage=payload.passing_score_percentage,
        max_attempts=payload.max_attempts,
        shuffle_questions=payload.shuffle_questions,
        shuffle_options=payload.shuffle_options,
        show_correct_answers=payload.show_correct_answers,
        allow_backtracking=payload.allow_backtracking,
        total_points=0.0,
        status=payload.status.lower().strip(),
        available_from=payload.available_from,
        due_date=payload.due_date,
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)

    return serialize_quiz(quiz, 0)


@router.get("/api/courses/{course_id}/quizzes", response_model=List[QuizOut])
async def list_course_quizzes(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List quizzes for a course (Instructors see all, students see published/open)"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)

    q = (
        select(
            Quiz,
            func.count(QuizQuestion.id).label("questions_count")
        )
        .outerjoin(QuizQuestion, QuizQuestion.quiz_id == Quiz.id)
        .where(Quiz.course_id == course_id)
        .group_by(Quiz.id)
        .order_by(Quiz.due_date.asc())
    )

    if not is_instructor_or_admin:
        q = q.where(Quiz.status.in_(["published", "closed"]))

    res = await db.execute(q)
    rows = res.all()

    return [serialize_quiz(quiz, count or 0) for quiz, count in rows]


@router.get("/api/quizzes/{quiz_id}", response_model=QuizOut)
async def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve quiz metadata and parameters"""
    q = (
        select(
            Quiz,
            func.count(QuizQuestion.id).label("questions_count")
        )
        .outerjoin(QuizQuestion, QuizQuestion.quiz_id == Quiz.id)
        .where(Quiz.id == quiz_id)
        .group_by(Quiz.id)
    )
    res = await db.execute(q)
    row = res.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )

    quiz, count = row
    await verify_course_assignment_access(quiz.course_id, current_user, db)

    return serialize_quiz(quiz, count or 0)


@router.post("/api/quizzes/{quiz_id}/questions", response_model=QuizQuestionOut, status_code=201)
async def add_question_to_quiz(
    quiz_id: int,
    payload: QuizQuestionAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a question from question bank to a quiz and update total points (Instructors/Admins only)"""
    res_quiz = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = res_quiz.scalar_one_or_none()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(quiz.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can add questions to quizzes."
        )

    # Validate question item
    res_item = await db.execute(select(QuestionBankItem).where(QuestionBankItem.id == payload.question_item_id))
    item = res_item.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question bank item not found"
        )

    order_index = payload.order_index
    if order_index is None:
        count_res = await db.execute(select(func.count(QuizQuestion.id)).where(QuizQuestion.quiz_id == quiz_id))
        order_index = count_res.scalar() or 0

    quiz_q = QuizQuestion(
        quiz_id=quiz_id,
        question_item_id=payload.question_item_id,
        order_index=order_index,
        points=payload.points,
    )
    db.add(quiz_q)

    # Increment item usage count
    item.usage_count = (item.usage_count or 0) + 1

    # Recalculate total points
    await db.flush()
    points_res = await db.execute(
        select(func.sum(QuizQuestion.points)).where(QuizQuestion.quiz_id == quiz_id)
    )
    quiz.total_points = points_res.scalar() or 0.0

    await db.commit()
    await db.refresh(quiz_q)

    return QuizQuestionOut(
        id=quiz_q.id,
        quiz_id=quiz_q.quiz_id,
        question_item_id=quiz_q.question_item_id,
        order_index=quiz_q.order_index,
        points=quiz_q.points,
    )


# ─── Student Quiz Taking & Automated Grading ──────────────────────────────────

@router.post("/api/quizzes/{quiz_id}/start", response_model=QuizStartOut, status_code=201)
async def start_quiz_attempt(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new quiz attempt for an enrolled student.
    Enforces deadlines and attempt quotas, dynamically randomizes questions,
    and strips answers/keys for test integrity.
    """
    # 1. Resolve student profile
    res_student = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = res_student.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only registered students can take quizzes."
        )

    # 2. Resolve quiz
    q_quiz = (
        select(Quiz)
        .where(Quiz.id == quiz_id)
        .options(
            selectinload(Quiz.questions).selectinload(QuizQuestion.question_item)
        )
    )
    res_quiz = await db.execute(q_quiz)
    quiz = res_quiz.scalar_one_or_none()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )

    await verify_course_assignment_access(quiz.course_id, current_user, db)

    now = datetime.utcnow()
    if quiz.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quiz is not open for attempts (status: {quiz.status})."
        )

    if quiz.available_from and now < quiz.available_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz is not yet available."
        )

    if quiz.due_date and now > quiz.due_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz due date has expired."
        )

    # 3. Check attempt limit
    q_prev = await db.execute(
        select(func.count(QuizAttempt.id)).where(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.student_id == student.id
        )
    )
    prev_attempts = q_prev.scalar() or 0
    if quiz.max_attempts and quiz.max_attempts > 0:
        if prev_attempts >= quiz.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum attempt limit ({quiz.max_attempts}) reached for this quiz."
            )

    attempt_number = prev_attempts + 1

    # 4. Prepare question list
    raw_questions = list(quiz.questions)
    if quiz.shuffle_questions:
        random.shuffle(raw_questions)

    student_questions = []
    for idx, qq in enumerate(raw_questions):
        item = qq.question_item
        options_sanitized = None
        if item.options:
            opts = [
                {"id": opt["id"], "text": opt["text"]}
                for opt in item.options
            ]
            if quiz.shuffle_options:
                random.shuffle(opts)
            options_sanitized = opts

        student_questions.append(
            StudentQuizQuestionOut(
                id=item.id,
                order_index=idx,
                points=qq.points,
                title=item.title,
                prompt=item.prompt,
                question_type=item.question_type,
                options=options_sanitized,
            )
        )

    # 5. Create attempt record
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=student.id,
        attempt_number=attempt_number,
        started_at=now,
        max_score=quiz.total_points or sum(qq.points for qq in quiz.questions),
        status="in_progress",
        answers=[],
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    return QuizStartOut(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        attempt_number=attempt_number,
        time_limit_minutes=quiz.time_limit_minutes,
        started_at=attempt.started_at,
        questions=student_questions,
    )


@router.post("/api/quizzes/{quiz_id}/attempts/{attempt_id}/autosave")
async def autosave_quiz_attempt(
    quiz_id: int,
    attempt_id: int,
    payload: QuizAutosavePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Autosave intermediate student answers during quiz session"""
    res = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.id == attempt_id, QuizAttempt.quiz_id == quiz_id)
        .options(selectinload(QuizAttempt.student))
    )
    attempt = res.scalar_one_or_none()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found"
        )

    if not attempt.student or attempt.student.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own this attempt."
        )

    if attempt.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot autosave attempt in status '{attempt.status}'."
        )

    attempt.answers = [a.model_dump() for a in payload.answers]
    await db.commit()

    return {"status": "autosaved", "saved_answers_count": len(payload.answers)}


@router.post("/api/quizzes/{quiz_id}/attempts/{attempt_id}/submit", response_model=QuizAttemptOut)
async def submit_quiz_attempt(
    quiz_id: int,
    attempt_id: int,
    payload: QuizSubmitPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit completed quiz attempt for deterministic automated grading.
    Compares answers against single/multiple choice options, numerical tolerance,
    or key strings, and immediately records final score and pass/fail standing.
    """
    res = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.id == attempt_id, QuizAttempt.quiz_id == quiz_id)
        .options(
            selectinload(QuizAttempt.student),
            selectinload(QuizAttempt.quiz).selectinload(Quiz.questions).selectinload(QuizQuestion.question_item)
        )
    )
    attempt = res.scalar_one_or_none()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found"
        )

    if not attempt.student or attempt.student.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own this attempt."
        )

    if attempt.status == "graded":
        return serialize_quiz_attempt(attempt)

    quiz = attempt.quiz
    now = datetime.utcnow()

    # Map quiz questions for point lookups
    qq_map = {qq.question_item_id: qq for qq in quiz.questions}
    student_answers_map = {a.question_id: a for a in payload.answers}

    total_score = 0.0
    results = []

    for qq in quiz.questions:
        item = qq.question_item
        ans = student_answers_map.get(item.id)
        points_awarded = 0.0
        is_correct = False
        explanation = item.explanation

        if ans:
            if item.question_type in {"single_choice", "true_false"}:
                selected_ids = ans.selected_option_ids or []
                correct_opt = next((o for o in (item.options or []) if o.get("is_correct")), None)
                if correct_opt and selected_ids and selected_ids[0] == correct_opt.get("id"):
                    points_awarded = qq.points
                    is_correct = True

            elif item.question_type == "multiple_choice":
                selected_ids = set(ans.selected_option_ids or [])
                correct_ids = {o["id"] for o in (item.options or []) if o.get("is_correct")}
                if selected_ids == correct_ids:
                    points_awarded = qq.points
                    is_correct = True

            elif item.question_type == "numerical":
                if ans.numerical_answer is not None and item.answer_key:
                    target = float(item.answer_key.get("target_value", 0.0))
                    tolerance = float(item.answer_key.get("tolerance", 0.0))
                    if abs(ans.numerical_answer - target) <= tolerance:
                        points_awarded = qq.points
                        is_correct = True

            elif item.question_type == "short_answer":
                if ans.text_answer and item.answer_key:
                    exp = str(item.answer_key.get("expected_text", "")).strip().lower()
                    if ans.text_answer.strip().lower() == exp:
                        points_awarded = qq.points
                        is_correct = True

        total_score += points_awarded
        results.append({
            "question_id": item.id,
            "title": item.title,
            "points_awarded": points_awarded,
            "max_points": qq.points,
            "is_correct": is_correct,
            "explanation": explanation if quiz.show_correct_answers else None,
        })

    max_possible = sum(qq.points for qq in quiz.questions)
    percentage = round((total_score / max_possible) * 100.0, 2) if max_possible > 0 else 0.0
    is_passed = percentage >= (quiz.passing_score_percentage or 50.0)

    attempt.submitted_at = now
    attempt.total_score = total_score
    attempt.max_score = max_possible
    attempt.percentage = percentage
    attempt.is_passed = is_passed
    attempt.status = "graded"
    attempt.answers = results

    await db.commit()
    await db.refresh(attempt)

    return serialize_quiz_attempt(attempt, results=results)


@router.get("/api/quizzes/{quiz_id}/attempts/{attempt_id}", response_model=QuizAttemptOut)
async def get_quiz_attempt(
    quiz_id: int,
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve quiz attempt score and question breakdown"""
    res = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.id == attempt_id, QuizAttempt.quiz_id == quiz_id)
        .options(selectinload(QuizAttempt.student), selectinload(QuizAttempt.quiz))
    )
    attempt = res.scalar_one_or_none()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_owner = bool(attempt.student and attempt.student.user_id == current_user.id)

    if not (is_admin or is_owner):
        # Check course lecturer
        res_course = await db.execute(
            select(Course).where(Course.id == attempt.quiz.course_id).options(selectinload(Course.lecturer))
        )
        course = res_course.scalar_one_or_none()
        is_instructor = bool(course and course.lecturer and course.lecturer.user_id == current_user.id)
        if not is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot view this attempt."
            )

    return serialize_quiz_attempt(attempt)


@router.get("/api/quizzes/{quiz_id}/attempts", response_model=List[QuizAttemptOut])
async def list_quiz_attempts(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all student attempts for a quiz (Instructors/Admins only)"""
    res_quiz = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = res_quiz.scalar_one_or_none()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(quiz.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can list all attempts."
        )

    q = (
        select(QuizAttempt)
        .where(QuizAttempt.quiz_id == quiz_id)
        .order_by(QuizAttempt.submitted_at.desc())
    )
    res = await db.execute(q)
    attempts = res.scalars().all()

    return [serialize_quiz_attempt(att) for att in attempts]
