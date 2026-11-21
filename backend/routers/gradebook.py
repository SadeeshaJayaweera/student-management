"""
NSBM EduSphere — Gradebook and Calculation Engine Router
Provides enterprise gradebook calculation, customizable category weightings,
drop-lowest-score algorithms, letter grade and GPA scale mappings, instructor overrides,
and CSV/JSON gradebook exports.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    Assignment, AssignmentSubmission, AssignmentStatus,
    Quiz, QuizAttempt,
    GradebookCategory, GradeScale, GradebookOverride
)
from backend.schemas import (
    GradebookCategoryCreate, GradebookCategoryOut,
    GradeScaleCreate, GradeScaleOut,
    GradebookOverridePayload, GradebookOverrideOut,
    AssessmentScoreItem, CategoryScoreSummary, StudentGradeSummary,
    CourseGradebookOut, GradebookExportOut
)
from backend.utils.security import get_current_user
from backend.core.sanitization import sanitize_rich_content
from backend.routers.assignments import verify_course_assignment_access

router = APIRouter(tags=["Gradebook & Calculation Engine"])

DEFAULT_SCALE_BRACKETS = [
    {"letter_grade": "A+", "min_percentage": 90.0, "max_percentage": 100.0, "gpa_points": 4.0},
    {"letter_grade": "A",  "min_percentage": 85.0, "max_percentage": 89.99, "gpa_points": 4.0},
    {"letter_grade": "A-", "min_percentage": 80.0, "max_percentage": 84.99, "gpa_points": 3.7},
    {"letter_grade": "B+", "min_percentage": 75.0, "max_percentage": 79.99, "gpa_points": 3.3},
    {"letter_grade": "B",  "min_percentage": 70.0, "max_percentage": 74.99, "gpa_points": 3.0},
    {"letter_grade": "B-", "min_percentage": 65.0, "max_percentage": 69.99, "gpa_points": 2.7},
    {"letter_grade": "C+", "min_percentage": 60.0, "max_percentage": 64.99, "gpa_points": 2.3},
    {"letter_grade": "C",  "min_percentage": 55.0, "max_percentage": 59.99, "gpa_points": 2.0},
    {"letter_grade": "C-", "min_percentage": 50.0, "max_percentage": 54.99, "gpa_points": 1.7},
    {"letter_grade": "D",  "min_percentage": 40.0, "max_percentage": 49.99, "gpa_points": 1.0},
    {"letter_grade": "F",  "min_percentage": 0.0,  "max_percentage": 39.99, "gpa_points": 0.0},
]


def map_percentage_to_grade(pct: float, brackets: List[Dict[str, Any]]) -> tuple[str, float]:
    """Map percentage to letter grade and GPA points according to scale brackets"""
    for b in brackets:
        min_p = float(b["min_percentage"])
        max_p = float(b["max_percentage"])
        if min_p <= pct <= (max_p + 0.01):
            return b["letter_grade"], float(b["gpa_points"])
    if pct >= 100.0:
        return "A+", 4.0
    return "F", 0.0


async def get_effective_scale(course_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
    """Retrieve active course grade scale or default scale"""
    res = await db.execute(
        select(GradeScale).where(GradeScale.course_id == course_id)
    )
    scale = res.scalar_one_or_none()
    if scale and scale.scale_brackets:
        return scale.scale_brackets
    return DEFAULT_SCALE_BRACKETS


# ─── Category Configuration Endpoints ────────────────────────────────────────

@router.post("/api/courses/{course_id}/gradebook/categories", response_model=GradebookCategoryOut, status_code=201)
async def create_gradebook_category(
    course_id: int,
    payload: GradebookCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Configure a gradebook assessment category with custom weighting and drop policies (Instructors/Admins only)"""
    _, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can configure gradebook categories."
        )

    # Check cumulative weight percentage
    res_weights = await db.execute(
        select(func.sum(GradebookCategory.weight_percentage)).where(GradebookCategory.course_id == course_id)
    )
    curr_weight = res_weights.scalar() or 0.0
    if curr_weight + payload.weight_percentage > 100.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Total category weight cannot exceed 100%. Current: {curr_weight}%, adding: {payload.weight_percentage}%"
        )

    category = GradebookCategory(
        course_id=course_id,
        name=payload.name.strip(),
        weight_percentage=payload.weight_percentage,
        drop_lowest_count=payload.drop_lowest_count,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return GradebookCategoryOut(
        id=category.id,
        course_id=category.course_id,
        name=category.name,
        weight_percentage=category.weight_percentage,
        drop_lowest_count=category.drop_lowest_count,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.get("/api/courses/{course_id}/gradebook/categories", response_model=List[GradebookCategoryOut])
async def list_gradebook_categories(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List configured gradebook categories for a course"""
    res = await db.execute(
        select(GradebookCategory)
        .where(GradebookCategory.course_id == course_id)
        .order_by(GradebookCategory.id.asc())
    )
    cats = res.scalars().all()
    return [
        GradebookCategoryOut(
            id=c.id,
            course_id=c.course_id,
            name=c.name,
            weight_percentage=c.weight_percentage,
            drop_lowest_count=c.drop_lowest_count,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cats
    ]


# ─── Grade Scale Endpoints ───────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/gradebook/scales", response_model=GradeScaleOut, status_code=201)
async def configure_course_grade_scale(
    course_id: int,
    payload: GradeScaleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Configure custom letter grade scale and brackets for a course (Instructors/Admins only)"""
    _, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can configure grade scales."
        )

    res_exist = await db.execute(
        select(GradeScale).where(GradeScale.course_id == course_id)
    )
    scale = res_exist.scalar_one_or_none()
    if scale:
        scale.name = payload.name
        scale.scale_brackets = [b.model_dump() for b in payload.scale_brackets]
    else:
        scale = GradeScale(
            course_id=course_id,
            name=payload.name,
            is_default=payload.is_default,
            scale_brackets=[b.model_dump() for b in payload.scale_brackets],
        )
        db.add(scale)

    await db.commit()
    await db.refresh(scale)

    return GradeScaleOut(
        id=scale.id,
        course_id=scale.course_id,
        name=scale.name,
        is_default=scale.is_default,
        scale_brackets=scale.scale_brackets,
        created_at=scale.created_at,
        updated_at=scale.updated_at,
    )


@router.get("/api/courses/{course_id}/gradebook/scales")
async def get_course_grade_scale(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get active grade scale for course"""
    brackets = await get_effective_scale(course_id, db)
    return {"course_id": course_id, "brackets": brackets}


# ─── Grade Override Endpoints ─────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/gradebook/override", response_model=GradebookOverrideOut)
async def override_student_grade(
    course_id: int,
    payload: GradebookOverridePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply manual grade override with audit trail and justification (Instructors/Admins only)"""
    _, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can override grades."
        )

    res_exist = await db.execute(
        select(GradebookOverride).where(
            GradebookOverride.course_id == course_id,
            GradebookOverride.student_id == payload.student_id
        )
    )
    override = res_exist.scalar_one_or_none()
    if override:
        override.overridden_percentage = payload.overridden_percentage
        override.overridden_letter_grade = payload.overridden_letter_grade
        override.overridden_gpa_points = payload.overridden_gpa_points
        override.override_reason = sanitize_rich_content(payload.override_reason)
        override.overridden_by_id = current_user.id
    else:
        override = GradebookOverride(
            course_id=course_id,
            student_id=payload.student_id,
            overridden_percentage=payload.overridden_percentage,
            overridden_letter_grade=payload.overridden_letter_grade,
            overridden_gpa_points=payload.overridden_gpa_points,
            override_reason=sanitize_rich_content(payload.override_reason),
            overridden_by_id=current_user.id,
        )
        db.add(override)

    await db.commit()
    await db.refresh(override)

    return GradebookOverrideOut(
        id=override.id,
        course_id=override.course_id,
        student_id=override.student_id,
        overridden_percentage=override.overridden_percentage,
        overridden_letter_grade=override.overridden_letter_grade,
        overridden_gpa_points=override.overridden_gpa_points,
        override_reason=override.override_reason,
        overridden_by_id=override.overridden_by_id,
        created_at=override.created_at,
        updated_at=override.updated_at,
    )


# ─── Calculation Helper ───────────────────────────────────────────────────────

async def calculate_student_grade_summary(
    student: Student,
    course_id: int,
    categories: List[GradebookCategory],
    assignments: List[Assignment],
    quizzes: List[Quiz],
    scale_brackets: List[Dict[str, Any]],
    overrides_map: Dict[int, GradebookOverride],
    db: AsyncSession
) -> StudentGradeSummary:
    """Computes comprehensive score, category rollups, lowest score dropping, and overrides for one student"""
    # 1. Fetch all submissions for student in this course
    asg_ids = [a.id for a in assignments]
    submissions_by_asg = {}
    if asg_ids:
        res_subs = await db.execute(
            select(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id.in_(asg_ids),
                AssignmentSubmission.student_id == student.id
            )
        )
        for s in res_subs.scalars().all():
            submissions_by_asg[s.assignment_id] = s

    # 2. Fetch all completed quiz attempts for student in this course
    quiz_ids = [q.id for q in quizzes]
    attempts_by_quiz = {}
    if quiz_ids:
        res_atts = await db.execute(
            select(QuizAttempt).where(
                QuizAttempt.quiz_id.in_(quiz_ids),
                QuizAttempt.student_id == student.id
            ).order_by(QuizAttempt.attempt_number.desc())
        )
        for att in res_atts.scalars().all():
            if att.quiz_id not in attempts_by_quiz:
                attempts_by_quiz[att.quiz_id] = att

    # 3. Categorize items
    cat_items_map: Dict[Optional[int], List[AssessmentScoreItem]] = {}
    for cat in categories:
        cat_items_map[cat.id] = []
    cat_items_map[None] = []  # Uncategorized

    # Map assignments
    for asg in assignments:
        sub = submissions_by_asg.get(asg.id)
        score = sub.marks if (sub and sub.marks is not None) else None
        pct = (score / asg.max_marks * 100.0) if (score is not None and asg.max_marks > 0) else None
        item_status = sub.status.value if (sub and hasattr(sub.status, "value")) else (str(sub.status) if sub else "unsubmitted")

        target_cat_id = asg.category_id
        if target_cat_id not in cat_items_map:
            target_cat_id = None

        cat_items_map[target_cat_id].append(
            AssessmentScoreItem(
                item_id=asg.id,
                item_title=asg.title,
                item_type="assignment",
                category_id=target_cat_id,
                score=score,
                max_marks=asg.max_marks,
                percentage=round(pct, 2) if pct is not None else None,
                is_dropped=False,
                status=item_status,
            )
        )

    # Map quizzes
    for q in quizzes:
        att = attempts_by_quiz.get(q.id)
        score = att.total_score if (att and att.total_score is not None) else None
        pct = att.percentage if (att and att.percentage is not None) else ((score / q.total_points * 100.0) if (score is not None and q.total_points > 0) else None)
        item_status = att.status if att else "unsubmitted"

        target_cat_id = q.category_id
        if target_cat_id not in cat_items_map:
            target_cat_id = None

        cat_items_map[target_cat_id].append(
            AssessmentScoreItem(
                item_id=q.id,
                item_title=q.title,
                item_type="quiz",
                category_id=target_cat_id,
                score=score,
                max_marks=q.total_points,
                percentage=round(pct, 2) if pct is not None else None,
                is_dropped=False,
                status=item_status,
            )
        )

    # 4. Calculate Category Summaries with Drop-Lowest Policy
    category_summaries: List[CategoryScoreSummary] = []
    weighted_sum = 0.0
    active_weight_sum = 0.0

    for cat in categories:
        items = cat_items_map.get(cat.id, [])
        scored_items = [it for it in items if it.percentage is not None]

        # Apply drop lowest count
        if cat.drop_lowest_count > 0 and len(scored_items) > cat.drop_lowest_count:
            # Sort by percentage ascending
            scored_items.sort(key=lambda x: x.percentage if x.percentage is not None else 0.0)
            for dropped_idx in range(cat.drop_lowest_count):
                scored_items[dropped_idx].is_dropped = True

        remaining_items = [it for it in items if not it.is_dropped and it.percentage is not None]
        if remaining_items:
            cat_pct = sum(it.percentage for it in remaining_items) / len(remaining_items)
            contrib = cat_pct * (cat.weight_percentage / 100.0)
            weighted_sum += contrib
            active_weight_sum += cat.weight_percentage
        else:
            cat_pct = None
            contrib = None

        category_summaries.append(
            CategoryScoreSummary(
                category_id=cat.id,
                category_name=cat.name,
                weight_percentage=cat.weight_percentage,
                drop_lowest_count=cat.drop_lowest_count,
                earned_percentage=round(cat_pct, 2) if cat_pct is not None else None,
                weighted_contribution=round(contrib, 2) if contrib is not None else None,
                items=items,
            )
        )

    # Process uncategorized items if no categories configured
    if not categories:
        uncat_items = cat_items_map.get(None, [])
        scored = [it.percentage for it in uncat_items if it.percentage is not None]
        overall_pct = (sum(scored) / len(scored)) if scored else 0.0
        calculated_percentage = round(overall_pct, 2)
    else:
        if active_weight_sum > 0:
            normalized_pct = (weighted_sum / active_weight_sum) * 100.0
            calculated_percentage = round(normalized_pct, 2)
        else:
            calculated_percentage = 0.0

    letter_grade, gpa_points = map_percentage_to_grade(calculated_percentage, scale_brackets)

    # 5. Handle Grade Override
    override = overrides_map.get(student.id)
    is_overridden = override is not None
    override_out = None
    if is_overridden and override:
        override_out = GradebookOverrideOut(
            id=override.id,
            course_id=override.course_id,
            student_id=override.student_id,
            overridden_percentage=override.overridden_percentage,
            overridden_letter_grade=override.overridden_letter_grade,
            overridden_gpa_points=override.overridden_gpa_points,
            override_reason=override.override_reason,
            overridden_by_id=override.overridden_by_id,
            created_at=override.created_at,
            updated_at=override.updated_at,
        )
        final_pct = override.overridden_percentage if override.overridden_percentage is not None else calculated_percentage
        final_grade = override.overridden_letter_grade or letter_grade
        final_gpa = override.overridden_gpa_points if override.overridden_gpa_points is not None else gpa_points
    else:
        final_pct = calculated_percentage
        final_grade = letter_grade
        final_gpa = gpa_points

    full_name = f"{student.user.full_name}" if student.user and student.user.full_name else f"Student {student.student_id}"
    email = student.user.email if student.user else ""

    return StudentGradeSummary(
        student_id=student.id,
        student_number=student.student_id,
        full_name=full_name,
        email=email,
        category_scores=category_summaries,
        calculated_percentage=calculated_percentage,
        letter_grade=letter_grade,
        gpa_points=gpa_points,
        is_overridden=is_overridden,
        override_details=override_out,
        final_percentage=round(final_pct, 2),
        final_letter_grade=final_grade,
        final_gpa_points=round(final_gpa, 2),
    )


# ─── Course Gradebook View Endpoints ──────────────────────────────────────────

@router.get("/api/courses/{course_id}/gradebook", response_model=CourseGradebookOut)
async def get_course_gradebook(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full course gradebook matrix with student summaries, category aggregations, and statistics (Instructors/Admins only)"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can view the full course gradebook."
        )

    # 1. Fetch Categories, Scale, Assignments, Quizzes
    res_cats = await db.execute(
        select(GradebookCategory).where(GradebookCategory.course_id == course_id).order_by(GradebookCategory.id.asc())
    )
    categories = res_cats.scalars().all()

    scale_brackets = await get_effective_scale(course_id, db)

    res_asgs = await db.execute(
        select(Assignment).where(Assignment.course_id == course_id).order_by(Assignment.due_date.asc())
    )
    assignments = res_asgs.scalars().all()

    res_quizzes = await db.execute(
        select(Quiz).where(Quiz.course_id == course_id).order_by(Quiz.due_date.asc())
    )
    quizzes = res_quizzes.scalars().all()

    # 2. Fetch Overrides
    res_overrides = await db.execute(
        select(GradebookOverride).where(GradebookOverride.course_id == course_id)
    )
    overrides_map = {ov.student_id: ov for ov in res_overrides.scalars().all()}

    # 3. Fetch Enrolled Students
    res_enrollments = await db.execute(
        select(Enrollment)
        .where(Enrollment.course_id == course_id, Enrollment.status.in_(["enrolled", "active", "completed"]))
        .options(selectinload(Enrollment.student).selectinload(Student.user))
    )
    enrollments = res_enrollments.scalars().all()

    student_summaries: List[StudentGradeSummary] = []
    total_pct_sum = 0.0

    for enr in enrollments:
        if not enr.student:
            continue
        summary = await calculate_student_grade_summary(
            student=enr.student,
            course_id=course_id,
            categories=categories,
            assignments=assignments,
            quizzes=quizzes,
            scale_brackets=scale_brackets,
            overrides_map=overrides_map,
            db=db
        )
        student_summaries.append(summary)
        total_pct_sum += summary.final_percentage

    avg_pct = (total_pct_sum / len(student_summaries)) if student_summaries else 0.0

    return CourseGradebookOut(
        course_id=course.id,
        course_code=course.course_code,
        course_title=course.title,
        total_enrolled=len(student_summaries),
        average_percentage=round(avg_pct, 2),
        categories=[
            GradebookCategoryOut(
                id=c.id,
                course_id=c.course_id,
                name=c.name,
                weight_percentage=c.weight_percentage,
                drop_lowest_count=c.drop_lowest_count,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in categories
        ],
        grade_scale={"brackets": scale_brackets},
        students=student_summaries,
    )


@router.get("/api/courses/{course_id}/gradebook/student/{student_id}", response_model=StudentGradeSummary)
async def get_student_grade_summary(
    course_id: int,
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed grade calculation breakdown for a specific student (Student self-view or Instructors/Admins)"""
    course, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)

    # Check student self-view authorization
    res_student = await db.execute(
        select(Student).where(Student.id == student_id).options(selectinload(Student.user))
    )
    student = res_student.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    is_self = student.user_id == current_user.id
    if not (is_instructor_or_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot view grades for another student."
        )

    res_cats = await db.execute(
        select(GradebookCategory).where(GradebookCategory.course_id == course_id).order_by(GradebookCategory.id.asc())
    )
    categories = res_cats.scalars().all()
    scale_brackets = await get_effective_scale(course_id, db)

    res_asgs = await db.execute(
        select(Assignment).where(Assignment.course_id == course_id).order_by(Assignment.due_date.asc())
    )
    assignments = res_asgs.scalars().all()

    res_quizzes = await db.execute(
        select(Quiz).where(Quiz.course_id == course_id).order_by(Quiz.due_date.asc())
    )
    quizzes = res_quizzes.scalars().all()

    res_overrides = await db.execute(
        select(GradebookOverride).where(
            GradebookOverride.course_id == course_id,
            GradebookOverride.student_id == student_id
        )
    )
    override = res_overrides.scalar_one_or_none()
    overrides_map = {student_id: override} if override else {}

    return await calculate_student_grade_summary(
        student=student,
        course_id=course_id,
        categories=categories,
        assignments=assignments,
        quizzes=quizzes,
        scale_brackets=scale_brackets,
        overrides_map=overrides_map,
        db=db
    )


# ─── Gradebook Export Endpoint ────────────────────────────────────────────────

@router.get("/api/courses/{course_id}/gradebook/export")
async def export_course_gradebook(
    course_id: int,
    export_format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export course gradebook as structured JSON or downloadable CSV sheet (Instructors/Admins only)"""
    gradebook = await get_course_gradebook(course_id=course_id, current_user=current_user, db=db)

    flat_records = []
    for s in gradebook.students:
        rec = {
            "student_number": s.student_number,
            "full_name": s.full_name,
            "email": s.email,
            "calculated_percentage": s.calculated_percentage,
            "calculated_letter_grade": s.letter_grade,
            "calculated_gpa": s.gpa_points,
            "is_overridden": s.is_overridden,
            "final_percentage": s.final_percentage,
            "final_letter_grade": s.final_letter_grade,
            "final_gpa": s.final_gpa_points,
        }
        for cat in s.category_scores:
            rec[f"{cat.category_name}_pct"] = cat.earned_percentage if cat.earned_percentage is not None else "N/A"
        flat_records.append(rec)

    if export_format == "csv":
        output = io.StringIO()
        if flat_records:
            fieldnames = list(flat_records[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in flat_records:
                writer.writerow(row)
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=gradebook_{gradebook.course_code}.csv"}
        )

    return GradebookExportOut(
        course_code=gradebook.course_code,
        exported_at=datetime.utcnow(),
        format="json",
        records_count=len(flat_records),
        data=flat_records,
    )
