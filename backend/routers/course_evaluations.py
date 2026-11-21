"""backend/routers/course_evaluations.py
Enterprise Student Feedback and Course Evaluation Router
Supports anonymous/identified multi-dimensional course feedback,
instructor effectiveness rating scales, automated duplicate prevention,
and faculty analytics aggregation.
"""

import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    Student,
    Lecturer,
    Course,
    Enrollment,
    CourseEvaluationSurvey,
    SurveyQuestion,
    SurveyResponse,
    SurveyAnswer,
)
from backend.schemas import (
    CourseEvaluationSurveyCreate,
    CourseEvaluationSurveyOut,
    CourseEvaluationSurveyDetailOut,
    SurveySubmissionPayload,
    SurveyAnalyticsOut,
    QuestionAnalyticsOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/evaluations", tags=["Student Feedback & Course Evaluations"])

SALT_PREFIX = "NSBM_EVAL_SECURE_SALT_v1"


def compute_student_hash(survey_id: int, student_id: int) -> str:
    """Generate a one-way deterministic hash for duplicate detection while keeping response anonymous."""
    raw = f"{SALT_PREFIX}:{survey_id}:{student_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ─── Student Evaluation Flow ──────────────────────────────────────────────────

@router.get("/student/pending", response_model=List[CourseEvaluationSurveyOut])
async def list_pending_student_evaluations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List open course evaluation surveys for courses in which the student is currently enrolled."""
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if not student:
        return []

    # Get student's active course IDs
    enr_res = await db.execute(
        select(Enrollment.course_id).where(
            Enrollment.student_id == student.id,
            Enrollment.status == "active",
        )
    )
    course_ids = enr_res.scalars().all()
    if not course_ids:
        return []

    # Query published surveys for these courses
    surveys_res = await db.execute(
        select(CourseEvaluationSurvey)
        .options(
            selectinload(CourseEvaluationSurvey.course),
            selectinload(CourseEvaluationSurvey.questions),
            selectinload(CourseEvaluationSurvey.responses),
        )
        .where(
            CourseEvaluationSurvey.course_id.in_(course_ids),
            CourseEvaluationSurvey.is_published == True,
        )
        .order_by(CourseEvaluationSurvey.end_date.asc())
    )
    surveys = surveys_res.scalars().all()

    out: List[CourseEvaluationSurveyOut] = []
    for s in surveys:
        s_hash = compute_student_hash(s.id, student.id)
        has_sub = any(r.student_hash == s_hash for r in s.responses)

        out.append(
            CourseEvaluationSurveyOut(
                id=s.id,
                institution_id=s.institution_id,
                course_id=s.course_id,
                course_code=s.course.course_code if s.course else None,
                course_title=s.course.title if s.course else None,
                title=s.title,
                description=s.description,
                start_date=s.start_date,
                end_date=s.end_date,
                is_published=s.is_published,
                is_anonymous=s.is_anonymous,
                created_at=s.created_at,
                questions_count=len(s.questions),
                responses_count=len(s.responses),
                has_submitted=has_sub,
            )
        )
    return out


@router.get("/surveys/{survey_id}", response_model=CourseEvaluationSurveyDetailOut)
async def get_survey_detail(
    survey_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full survey with questionnaire items and submission status."""
    res = await db.execute(
        select(CourseEvaluationSurvey)
        .options(
            selectinload(CourseEvaluationSurvey.course),
            selectinload(CourseEvaluationSurvey.questions),
            selectinload(CourseEvaluationSurvey.responses),
        )
        .where(CourseEvaluationSurvey.id == survey_id)
    )
    survey = res.scalars().first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    has_sub = False
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if student:
        s_hash = compute_student_hash(survey.id, student.id)
        has_sub = any(r.student_hash == s_hash for r in survey.responses)

    return CourseEvaluationSurveyDetailOut(
        id=survey.id,
        institution_id=survey.institution_id,
        course_id=survey.course_id,
        course_code=survey.course.course_code if survey.course else None,
        course_title=survey.course.title if survey.course else None,
        title=survey.title,
        description=survey.description,
        start_date=survey.start_date,
        end_date=survey.end_date,
        is_published=survey.is_published,
        is_anonymous=survey.is_anonymous,
        created_at=survey.created_at,
        questions=survey.questions,
        has_submitted=has_sub,
    )


@router.post("/surveys/{survey_id}/submit", status_code=status.HTTP_201_CREATED)
async def submit_survey_response(
    survey_id: int,
    payload: SurveySubmissionPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit confidential/anonymous evaluation answers for an active course survey."""
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Only enrolled students can evaluate courses.")

    # Load survey
    s_res = await db.execute(
        select(CourseEvaluationSurvey)
        .options(selectinload(CourseEvaluationSurvey.questions))
        .where(CourseEvaluationSurvey.id == survey_id)
    )
    survey = s_res.scalars().first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    if not survey.is_published:
        raise HTTPException(status_code=400, detail="This evaluation survey is not currently published.")

    # Check student enrollment in the course
    enr_res = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.course_id == survey.course_id,
        )
    )
    if not enr_res.scalars().first():
        raise HTTPException(status_code=403, detail="You are not enrolled in this course.")

    # Check for duplicate submission using the secure hash
    s_hash = compute_student_hash(survey.id, student.id)
    existing_res = await db.execute(
        select(SurveyResponse).where(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.student_hash == s_hash,
        )
    )
    if existing_res.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="You have already submitted an evaluation for this course.",
        )

    now = datetime.utcnow()
    response = SurveyResponse(
        survey_id=survey_id,
        student_id=None if survey.is_anonymous else student.id,
        student_hash=s_hash,
        submitted_at=now,
    )
    db.add(response)
    await db.commit()
    await db.refresh(response)

    # Insert answers
    valid_q_ids = {q.id for q in survey.questions}
    answers_to_add = []
    for a in payload.answers:
        if a.question_id in valid_q_ids:
            answers_to_add.append(
                SurveyAnswer(
                    response_id=response.id,
                    question_id=a.question_id,
                    numeric_rating=a.numeric_rating,
                    text_response=a.text_response,
                    selected_options_json=a.selected_options_json,
                )
            )
    if answers_to_add:
        db.add_all(answers_to_add)
        await db.commit()

    return {
        "status": "submitted",
        "survey_id": survey_id,
        "submitted_at": now.isoformat(),
        "answers_count": len(answers_to_add),
    }


# ─── Faculty & Admin Survey Management & Analytics ───────────────────────────

@router.post("/surveys", response_model=CourseEvaluationSurveyOut, status_code=status.HTTP_201_CREATED)
async def create_survey(
    payload: CourseEvaluationSurveyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Faculty or Admin creates a new course evaluation survey with questionnaire."""
    # Verify course exists
    c_res = await db.execute(select(Course).where(Course.id == payload.course_id))
    course = c_res.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    survey = CourseEvaluationSurvey(
        course_id=payload.course_id,
        title=payload.title,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_published=payload.is_published,
        is_anonymous=payload.is_anonymous,
        created_by_id=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(survey)
    await db.commit()
    await db.refresh(survey)

    # Add questions if provided, otherwise populate default standard pedagogical questions
    default_questions = [
        {"text": "The instructor effectively communicated concepts and course objectives.", "category": "instructor_effectiveness", "type": "rating_scale_5", "order": 1},
        {"text": "The course materials and lecture notes were comprehensive and up-to-date.", "category": "course_content", "type": "rating_scale_5", "order": 2},
        {"text": "Assessments, assignments, and exams were graded fairly and transparently.", "category": "assessment_fairness", "type": "rating_scale_5", "order": 3},
        {"text": "Laboratory facilities and digital learning resources supported my studies.", "category": "facilities", "type": "rating_scale_5", "order": 4},
        {"text": "Overall rating of this course module.", "category": "overall", "type": "rating_scale_5", "order": 5},
        {"text": "What aspects of the module could be improved for future semesters?", "category": "overall", "type": "text", "order": 6},
    ]

    questions_to_add = []
    if payload.questions:
        for q in payload.questions:
            questions_to_add.append(
                SurveyQuestion(
                    survey_id=survey.id,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    category=q.category,
                    is_required=q.is_required,
                    options_json=q.options_json,
                    display_order=q.display_order,
                )
            )
    else:
        for dq in default_questions:
            questions_to_add.append(
                SurveyQuestion(
                    survey_id=survey.id,
                    question_text=dq["text"],
                    question_type=dq["type"],
                    category=dq["category"],
                    is_required=True,
                    display_order=dq["order"],
                )
            )

    db.add_all(questions_to_add)
    await db.commit()

    return CourseEvaluationSurveyOut(
        id=survey.id,
        institution_id=survey.institution_id,
        course_id=survey.course_id,
        course_code=course.course_code,
        course_title=course.title,
        title=survey.title,
        description=survey.description,
        start_date=survey.start_date,
        end_date=survey.end_date,
        is_published=survey.is_published,
        is_anonymous=survey.is_anonymous,
        created_at=survey.created_at,
        questions_count=len(questions_to_add),
        responses_count=0,
        has_submitted=False,
    )


@router.put("/surveys/{survey_id}/publish")
async def toggle_survey_publish(
    survey_id: int,
    publish: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Publish or unpublish an evaluation survey."""
    s_res = await db.execute(select(CourseEvaluationSurvey).where(CourseEvaluationSurvey.id == survey_id))
    survey = s_res.scalars().first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    survey.is_published = publish
    await db.commit()
    return {"status": "success", "survey_id": survey_id, "is_published": survey.is_published}


@router.get("/surveys/{survey_id}/analytics", response_model=SurveyAnalyticsOut)
async def get_survey_analytics(
    survey_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Aggregated evaluation analytics and performance breakdown."""
    res = await db.execute(
        select(CourseEvaluationSurvey)
        .options(
            selectinload(CourseEvaluationSurvey.course),
            selectinload(CourseEvaluationSurvey.questions).selectinload(SurveyQuestion.answers),
            selectinload(CourseEvaluationSurvey.responses),
        )
        .where(CourseEvaluationSurvey.id == survey_id)
    )
    survey = res.scalars().first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    total_resp = len(survey.responses)
    q_analytics: List[QuestionAnalyticsOut] = []
    cat_scores: Dict[str, List[float]] = {}
    all_scores: List[float] = []

    for q in survey.questions:
        num_ratings = [a.numeric_rating for a in q.answers if a.numeric_rating is not None]
        avg_rating = round(sum(num_ratings) / len(num_ratings), 2) if num_ratings else None

        if avg_rating is not None:
            cat_scores.setdefault(q.category, []).append(avg_rating)
            all_scores.append(avg_rating)

        # Rating distribution
        dist: Dict[str, int] = {}
        for r in num_ratings:
            dist[str(int(r))] = dist.get(str(int(r)), 0) + 1

        # Text feedback comments
        text_comments = [a.text_response for a in q.answers if a.text_response and a.text_response.strip()]

        q_analytics.append(
            QuestionAnalyticsOut(
                question_id=q.id,
                question_text=q.question_text,
                category=q.category,
                question_type=q.question_type,
                average_rating=avg_rating,
                response_count=len(q.answers),
                rating_distribution=dist,
                text_feedback=text_comments,
            )
        )

    cat_averages = {cat: round(sum(scores) / len(scores), 2) for cat, scores in cat_scores.items()}
    overall_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else None

    return SurveyAnalyticsOut(
        survey_id=survey.id,
        title=survey.title,
        course_code=survey.course.course_code if survey.course else "",
        course_title=survey.course.title if survey.course else "",
        total_responses=total_resp,
        category_averages=cat_averages,
        overall_average=overall_avg,
        question_analytics=q_analytics,
    )
