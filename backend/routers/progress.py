"""
NSBM EduSphere — Student Progress & Completion Tracking Router
Manages lesson-level completion telemetry, module-level aggregations, dynamic prerequisite
unlocking, and comprehensive course progress reports for students and instructors.
"""
from datetime import datetime
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    Course, CourseModule, CourseLesson, StudentLessonProgress, StudentModuleProgress,
    Enrollment, User, UserRole, Student
)
from backend.schemas import (
    LessonProgressUpdate, LessonProgressOut, CourseProgressReport,
    ModuleProgressSummary, StudentProgressRosterItem
)
from backend.core.dependencies import get_current_user

router = APIRouter(tags=["Student Progress & Completion Tracking"])


def check_course_admin_or_faculty_access(current_user: User, course: Optional[Course] = None):
    """Allows Admins or assigned Lecturers to inspect class progress"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}:
        return
    if course and hasattr(current_user, "lecturer_profile") and current_user.lecturer_profile:
        if course.lecturer_id == current_user.lecturer_profile.id:
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Administrative or assigned faculty permissions required."
    )


async def get_enrolled_student(current_user: User, course_id: int, db: AsyncSession) -> Tuple[Course, Student]:
    """Ensures current user is an active student enrolled in the course"""
    res = await db.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.enrollments).selectinload(Enrollment.student))
    )
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.STUDENT.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can track personal progress")

    for enr in course.enrollments:
        if enr.student and enr.student.user_id == current_user.id and enr.status in {"active", "completed"}:
            return course, enr.student

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You are not actively enrolled in this course."
    )


async def recalculate_module_progress(module_id: int, student_id: int, db: AsyncSession) -> StudentModuleProgress:
    """Calculates completion percentage of a module for a student"""
    now = datetime.utcnow()
    # Count total published lessons in module
    l_res = await db.execute(
        select(CourseLesson).where(CourseLesson.module_id == module_id, CourseLesson.is_published == True)
    )
    lessons = list(l_res.scalars().all())
    total_count = len(lessons)

    if total_count == 0:
        pct = 100.0
        completed_count = 0
    else:
        lesson_ids = [l.id for l in lessons]
        p_res = await db.execute(
            select(StudentLessonProgress).where(
                StudentLessonProgress.lesson_id.in_(lesson_ids),
                StudentLessonProgress.student_id == student_id,
                StudentLessonProgress.status == "completed"
            )
        )
        completed_records = list(p_res.scalars().all())
        completed_count = len(completed_records)
        pct = round((completed_count / total_count) * 100.0, 1)

    m_res = await db.execute(
        select(StudentModuleProgress).where(
            StudentModuleProgress.module_id == module_id,
            StudentModuleProgress.student_id == student_id
        )
    )
    mod_prog = m_res.scalar_one_or_none()
    if not mod_prog:
        mod_prog = StudentModuleProgress(
            module_id=module_id,
            student_id=student_id,
            status="completed" if pct >= 100.0 else "in_progress",
            completed_items_count=completed_count,
            total_items_count=total_count,
            progress_percentage=pct,
            completed_at=now if pct >= 100.0 else None,
        )
        db.add(mod_prog)
    else:
        mod_prog.completed_items_count = completed_count
        mod_prog.total_items_count = total_count
        mod_prog.progress_percentage = pct
        if pct >= 100.0:
            mod_prog.status = "completed"
            if not mod_prog.completed_at:
                mod_prog.completed_at = now
        else:
            mod_prog.status = "in_progress"

    await db.commit()
    await db.refresh(mod_prog)
    return mod_prog


async def build_course_progress_report(course: Course, student: Student, db: AsyncSession) -> CourseProgressReport:
    """Builds comprehensive progress report for a student in a course"""
    now = datetime.utcnow()
    # Load all modules and lessons
    m_res = await db.execute(
        select(CourseModule)
        .where(CourseModule.course_id == course.id, CourseModule.is_active == True, CourseModule.status == "published")
        .options(selectinload(CourseModule.lessons))
        .order_by(CourseModule.order_index)
    )
    modules = list(m_res.scalars().all())

    # Load student module progress
    mod_ids = [m.id for m in modules]
    mp_res = await db.execute(
        select(StudentModuleProgress).where(
            StudentModuleProgress.module_id.in_(mod_ids),
            StudentModuleProgress.student_id == student.id
        )
    )
    mod_progress_map = {p.module_id: p for p in mp_res.scalars().all()}

    # Load student lesson progress
    all_lessons = [l for m in modules for l in m.lessons if l.is_published]
    lesson_ids = [l.id for l in all_lessons]
    lp_res = await db.execute(
        select(StudentLessonProgress).where(
            StudentLessonProgress.lesson_id.in_(lesson_ids),
            StudentLessonProgress.student_id == student.id
        )
    )
    lesson_progress_records = list(lp_res.scalars().all())
    completed_lessons = [lp for lp in lesson_progress_records if lp.status == "completed"]
    total_time_spent = sum(lp.time_spent_seconds for lp in lesson_progress_records)

    total_lessons_count = len(all_lessons)
    completed_lessons_count = len(completed_lessons)
    overall_pct = (
        round((completed_lessons_count / total_lessons_count) * 100.0, 1)
        if total_lessons_count > 0 else 0.0
    )

    # Build module summaries with dynamic prerequisite check
    module_summaries = []
    completed_module_ids = {
        m_id for m_id, p in mod_progress_map.items() if p.status == "completed"
    }

    for mod in modules:
        mp = mod_progress_map.get(mod.id)
        # Check prerequisite lock
        is_locked = False
        if mod.unlock_at and mod.unlock_at > now:
            is_locked = True
        elif mod.prerequisite_module_id and mod.prerequisite_module_id not in completed_module_ids:
            is_locked = True

        pub_lessons = [l for l in mod.lessons if l.is_published]
        summary = ModuleProgressSummary(
            module_id=mod.id,
            module_title=mod.title,
            status=mp.status if mp else "in_progress",
            completed_items_count=mp.completed_items_count if mp else 0,
            total_items_count=len(pub_lessons),
            progress_percentage=mp.progress_percentage if mp else 0.0,
            is_locked=is_locked,
            completed_at=mp.completed_at if mp else None,
        )
        module_summaries.append(summary)

    student_name = student.user.full_name if (hasattr(student, "user") and student.user) else "Student"

    return CourseProgressReport(
        course_id=course.id,
        student_id=student.id,
        student_name=student_name,
        overall_progress_percentage=overall_pct,
        completed_lessons_count=completed_lessons_count,
        total_lessons_count=total_lessons_count,
        total_time_spent_seconds=total_time_spent,
        is_course_completed=overall_pct >= 100.0,
        modules=module_summaries,
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/api/lessons/{lesson_id}/progress", response_model=LessonProgressOut)
async def record_lesson_progress(
    lesson_id: int,
    payload: LessonProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Records student lesson completion and triggers module progress rollup"""
    l_res = await db.execute(select(CourseLesson).where(CourseLesson.id == lesson_id))
    lesson = l_res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    mod = await db.get(CourseModule, lesson.module_id)
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent module not found")

    course, student = await get_enrolled_student(current_user, mod.course_id, db)

    lp_res = await db.execute(
        select(StudentLessonProgress).where(
            StudentLessonProgress.lesson_id == lesson_id,
            StudentLessonProgress.student_id == student.id
        )
    )
    progress = lp_res.scalar_one_or_none()

    now = datetime.utcnow()
    if not progress:
        progress = StudentLessonProgress(
            lesson_id=lesson_id,
            student_id=student.id,
            status=payload.status,
            time_spent_seconds=payload.time_spent_seconds,
            completed_at=now if payload.status == "completed" else None,
        )
        db.add(progress)
    else:
        progress.time_spent_seconds += payload.time_spent_seconds
        progress.status = payload.status
        if payload.status == "completed" and not progress.completed_at:
            progress.completed_at = now

    await db.commit()
    await db.refresh(progress)

    # Recalculate parent module progress
    await recalculate_module_progress(lesson.module_id, student.id, db)

    return progress


@router.get("/api/courses/{course_id}/progress", response_model=CourseProgressReport)
async def get_my_course_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves authenticated student's overall progress across the course"""
    course, student = await get_enrolled_student(current_user, course_id, db)
    # Load user relationship on student for display name
    await db.refresh(student, ["user"])
    return await build_course_progress_report(course, student, db)


@router.get("/api/courses/{course_id}/students/{student_id}/progress", response_model=CourseProgressReport)
async def get_student_course_progress(
    course_id: int,
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Faculty / Admin inspects a specific student's detailed progress in a course"""
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    check_course_admin_or_faculty_access(current_user, course)

    res = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(selectinload(Student.user))
    )
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    return await build_course_progress_report(course, student, db)


@router.get("/api/courses/{course_id}/progress/roster", response_model=List[StudentProgressRosterItem])
async def get_course_progress_roster(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Faculty / Admin retrieves course-wide progress leaderboard and completion overview"""
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    check_course_admin_or_faculty_access(current_user, course)

    # Load enrolled students
    enr_res = await db.execute(
        select(Enrollment)
        .where(Enrollment.course_id == course_id, Enrollment.status.in_(["active", "completed"]))
        .options(selectinload(Enrollment.student).selectinload(Student.user))
    )
    enrollments = list(enr_res.scalars().all())

    # Count total published lessons in course
    l_res = await db.execute(
        select(func.count(CourseLesson.id))
        .join(CourseModule, CourseLesson.module_id == CourseModule.id)
        .where(CourseModule.course_id == course_id, CourseLesson.is_published == True)
    )
    total_lessons = l_res.scalar() or 0

    roster = []
    for enr in enrollments:
        stu = enr.student
        if not stu:
            continue

        # Count completed lessons
        p_res = await db.execute(
            select(func.count(StudentLessonProgress.id))
            .join(CourseLesson, StudentLessonProgress.lesson_id == CourseLesson.id)
            .join(CourseModule, CourseLesson.module_id == CourseModule.id)
            .where(
                CourseModule.course_id == course_id,
                StudentLessonProgress.student_id == stu.id,
                StudentLessonProgress.status == "completed"
            )
        )
        completed_count = p_res.scalar() or 0
        pct = round((completed_count / total_lessons) * 100.0, 1) if total_lessons > 0 else 0.0

        roster.append(
            StudentProgressRosterItem(
                student_id=stu.id,
                student_name=stu.user.full_name if stu.user else "Unknown Student",
                student_code=stu.student_id,
                enrollment_status=enr.status,
                progress_percentage=pct,
                completed_lessons_count=completed_count,
                total_lessons_count=total_lessons,
                is_completed=pct >= 100.0,
            )
        )

    return roster
