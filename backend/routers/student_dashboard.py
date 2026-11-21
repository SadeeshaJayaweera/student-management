"""
NSBM EduSphere — Personalized Student Dashboard Router
Provides an aggregated, real-time personalized student overview:
- Course progress and module completion metrics
- Upcoming time-sensitive deadlines across assignments and quizzes
- Live virtual classroom schedules and attendance
- Course announcements and unread notifications
- Personalized automated learning recommendations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Student, Course, Lecturer, Enrollment,
    CourseModule, CourseLesson, StudentLessonProgress,
    Assignment, AssignmentSubmission, AssignmentStatus,
    Quiz, QuizAttempt, VirtualClassroomSession,
    CourseAnnouncement, Notification, Attendance,
    GradebookCategory, GradeScale, GradebookOverride
)
from backend.schemas import (
    PersonalizedStudentDashboardOut, CourseProgressSummary,
    UpcomingDeadlineItem, UpcomingClassSession,
    DashboardAnnouncementItem, PersonalizedRecommendation
)
from backend.utils.security import get_current_user
from backend.routers.gradebook import get_effective_scale, map_percentage_to_grade

router = APIRouter(tags=["Personalized Student Dashboard"])


@router.get("/api/students/dashboard/personalized", response_model=PersonalizedStudentDashboardOut)
async def get_personalized_student_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve comprehensive, personalized student dashboard data:
    course progress, upcoming deadlines, classes, announcements, and AI/rule recommendations.
    """
    # 1. Resolve student profile
    res_student = await db.execute(
        select(Student)
        .where(Student.user_id == current_user.id)
        .options(selectinload(Student.user))
    )
    student = res_student.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found for current user."
        )

    now = datetime.utcnow()

    # 2. Enrolled courses
    res_enrollments = await db.execute(
        select(Enrollment)
        .where(
            Enrollment.student_id == student.id,
            Enrollment.status.in_(["enrolled", "active"])
        )
        .options(
            selectinload(Enrollment.course).selectinload(Course.lecturer).selectinload(Lecturer.user),
            selectinload(Enrollment.course).selectinload(Course.modules).selectinload(CourseModule.lessons),
        )
    )
    enrollments = res_enrollments.scalars().all()
    enrolled_courses = [e.course for e in enrollments if e.course and e.course.is_active]
    enrolled_course_ids = [c.id for c in enrolled_courses]

    # 3. Overall Attendance
    res_att_total = await db.execute(
        select(func.count(Attendance.id)).where(Attendance.student_id == student.id)
    )
    total_att_count = res_att_total.scalar() or 0

    res_att_present = await db.execute(
        select(func.count(Attendance.id)).where(
            Attendance.student_id == student.id,
            Attendance.status == "present"
        )
    )
    present_att_count = res_att_present.scalar() or 0
    overall_att_rate = round((present_att_count / total_att_count * 100.0), 1) if total_att_count > 0 else 100.0

    # 4. Course Progress Aggregations
    courses_progress: List[CourseProgressSummary] = []
    course_att_map: Dict[int, float] = {}

    for c in enrolled_courses:
        # Lessons count
        all_lessons = []
        for m in (c.modules or []):
            all_lessons.extend(m.lessons or [])
        total_lessons = len(all_lessons)
        lesson_ids = [l.id for l in all_lessons]

        completed_lessons = 0
        if lesson_ids:
            res_comp = await db.execute(
                select(func.count(StudentLessonProgress.id)).where(
                    StudentLessonProgress.student_id == student.id,
                    StudentLessonProgress.lesson_id.in_(lesson_ids),
                    StudentLessonProgress.status == "completed"
                )
            )
            completed_lessons = res_comp.scalar() or 0

        progress_pct = round((completed_lessons / total_lessons * 100.0), 1) if total_lessons > 0 else 0.0

        # Course attendance
        res_c_att_tot = await db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == student.id,
                Attendance.course_id == c.id
            )
        )
        c_tot = res_c_att_tot.scalar() or 0

        res_c_att_pres = await db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == student.id,
                Attendance.course_id == c.id,
                Attendance.status == "present"
            )
        )
        c_pres = res_c_att_pres.scalar() or 0
        c_att_rate = round((c_pres / c_tot * 100.0), 1) if c_tot > 0 else 100.0
        course_att_map[c.id] = c_att_rate

        # Course current grade
        res_ov = await db.execute(
            select(GradebookOverride).where(
                GradebookOverride.course_id == c.id,
                GradebookOverride.student_id == student.id
            )
        )
        ov = res_ov.scalar_one_or_none()
        if ov and ov.overridden_percentage is not None:
            c_grade_pct = ov.overridden_percentage
            c_letter = ov.overridden_letter_grade or "A"
        else:
            # Simple score average from graded submissions
            res_asg_scores = await db.execute(
                select(AssignmentSubmission.marks, Assignment.max_marks)
                .join(Assignment, Assignment.id == AssignmentSubmission.assignment_id)
                .where(
                    Assignment.course_id == c.id,
                    AssignmentSubmission.student_id == student.id,
                    AssignmentSubmission.marks.isnot(None),
                    Assignment.max_marks > 0
                )
            )
            scores = res_asg_scores.all()
            if scores:
                c_grade_pct = round(sum((m / mm * 100.0) for m, mm in scores) / len(scores), 1)
                scale = await get_effective_scale(c.id, db)
                c_letter, _ = map_percentage_to_grade(c_grade_pct, scale)
            else:
                c_grade_pct = None
                c_letter = None

        lecturer_name = (
            c.lecturer.user.full_name
            if (c.lecturer and c.lecturer.user and c.lecturer.user.full_name)
            else "Department Faculty"
        )

        courses_progress.append(
            CourseProgressSummary(
                course_id=c.id,
                course_code=c.course_code,
                course_title=c.title,
                faculty=c.faculty or "",
                department=c.department or "",
                lecturer_name=lecturer_name,
                delivery_method=c.delivery_method or "in_person",
                completed_lessons=completed_lessons,
                total_lessons=total_lessons,
                progress_percentage=progress_pct,
                current_grade_percentage=c_grade_pct,
                letter_grade=c_letter,
                attendance_rate=c_att_rate,
            )
        )

    # 5. Upcoming Deadlines (Assignments and Quizzes)
    upcoming_deadlines: List[UpcomingDeadlineItem] = []
    if enrolled_course_ids:
        # Assignments
        res_asgs = await db.execute(
            select(Assignment, Course)
            .join(Course, Course.id == Assignment.course_id)
            .where(
                Assignment.course_id.in_(enrolled_course_ids),
                Assignment.status == "published",
                Assignment.due_date >= (now - timedelta(days=2))
            )
            .order_by(Assignment.due_date.asc())
            .limit(10)
        )
        asg_rows = res_asgs.all()
        asg_ids = [a.id for a, _ in asg_rows]

        sub_map = {}
        if asg_ids:
            res_sub = await db.execute(
                select(AssignmentSubmission).where(
                    AssignmentSubmission.assignment_id.in_(asg_ids),
                    AssignmentSubmission.student_id == student.id
                )
            )
            for s in res_sub.scalars().all():
                sub_map[s.assignment_id] = s

        for a, c in asg_rows:
            sub = sub_map.get(a.id)
            is_overdue = now > a.due_date
            sub_status = (
                sub.status.value if (sub and hasattr(sub.status, "value"))
                else (str(sub.status) if sub else ("missed" if is_overdue else "pending"))
            )
            days_rem = (a.due_date - now).total_seconds() / 86400.0

            upcoming_deadlines.append(
                UpcomingDeadlineItem(
                    id=a.id,
                    item_type="assignment",
                    title=a.title,
                    course_id=c.id,
                    course_code=c.course_code,
                    course_title=c.title,
                    due_date=a.due_date,
                    days_remaining=round(days_rem, 1),
                    is_overdue=is_overdue,
                    max_marks=a.max_marks,
                    submission_status=sub_status,
                )
            )

        # Quizzes
        res_quizzes = await db.execute(
            select(Quiz, Course)
            .join(Course, Course.id == Quiz.course_id)
            .where(
                Quiz.course_id.in_(enrolled_course_ids),
                Quiz.status == "published",
                Quiz.due_date >= (now - timedelta(days=2))
            )
            .order_by(Quiz.due_date.asc())
            .limit(10)
        )
        quiz_rows = res_quizzes.all()
        quiz_ids = [q.id for q, _ in quiz_rows]

        att_map = {}
        if quiz_ids:
            res_atts = await db.execute(
                select(QuizAttempt).where(
                    QuizAttempt.quiz_id.in_(quiz_ids),
                    QuizAttempt.student_id == student.id
                )
            )
            for att in res_atts.scalars().all():
                att_map[att.quiz_id] = att

        for q, c in quiz_rows:
            att = att_map.get(q.id)
            is_overdue = now > q.due_date
            sub_status = att.status if att else ("missed" if is_overdue else "pending")
            days_rem = (q.due_date - now).total_seconds() / 86400.0

            upcoming_deadlines.append(
                UpcomingDeadlineItem(
                    id=q.id,
                    item_type="quiz",
                    title=q.title,
                    course_id=c.id,
                    course_code=c.course_code,
                    course_title=c.title,
                    due_date=q.due_date,
                    days_remaining=round(days_rem, 1),
                    is_overdue=is_overdue,
                    max_marks=q.total_points,
                    submission_status=sub_status,
                )
            )

    upcoming_deadlines.sort(key=lambda x: x.due_date)

    # 6. Upcoming Live Classes
    upcoming_classes: List[UpcomingClassSession] = []
    if enrolled_course_ids:
        res_sessions = await db.execute(
            select(VirtualClassroomSession, Course)
            .join(Course, Course.id == VirtualClassroomSession.course_id)
            .where(
                VirtualClassroomSession.course_id.in_(enrolled_course_ids),
                VirtualClassroomSession.end_time >= now,
                VirtualClassroomSession.status != "cancelled"
            )
            .order_by(VirtualClassroomSession.start_time.asc())
            .limit(5)
        )
        for s, c in res_sessions.all():
            is_live = (s.start_time <= now <= s.end_time)
            dur = int((s.end_time - s.start_time).total_seconds() / 60) if s.end_time and s.start_time else 60
            upcoming_classes.append(
                UpcomingClassSession(
                    session_id=s.id,
                    course_id=c.id,
                    course_code=c.course_code,
                    course_title=c.title,
                    title=s.title,
                    start_time=s.start_time,
                    duration_minutes=dur,
                    session_type=s.provider or "live_class",
                    join_url=s.join_url,
                    is_live=is_live,
                )
            )

    # 7. Recent Announcements
    recent_announcements: List[DashboardAnnouncementItem] = []
    if enrolled_course_ids:
        res_ann = await db.execute(
            select(CourseAnnouncement, Course, User)
            .join(Course, Course.id == CourseAnnouncement.course_id)
            .outerjoin(User, User.id == CourseAnnouncement.author_id)
            .where(CourseAnnouncement.course_id.in_(enrolled_course_ids))
            .order_by(CourseAnnouncement.is_pinned.desc(), CourseAnnouncement.published_at.desc())
            .limit(6)
        )
        for a, c, u in res_ann.all():
            recent_announcements.append(
                DashboardAnnouncementItem(
                    id=a.id,
                    course_id=c.id,
                    course_code=c.course_code,
                    course_title=c.title,
                    title=a.title,
                    content=a.content,
                    is_pinned=a.is_pinned,
                    author_name=u.full_name if u else "Course Faculty",
                    published_at=a.published_at,
                )
            )

    # 8. Unread Notifications Count
    res_notif = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    )
    unread_notifs = res_notif.scalar() or 0

    # 9. Personalized Recommendations Engine
    recommendations: List[PersonalizedRecommendation] = []

    # Recommendation: Urgent deadlines within 72 hours
    urgent_items = [
        d for d in upcoming_deadlines
        if not d.is_overdue and d.submission_status in {"pending", "unsubmitted"} and (0 <= d.days_remaining <= 3.0)
    ]
    for u in urgent_items[:2]:
        hrs = max(1, int(u.days_remaining * 24))
        recommendations.append(
            PersonalizedRecommendation(
                id=f"rec-urgent-{u.item_type}-{u.id}",
                category="urgent_deadline",
                priority="high",
                title=f"Due in {hrs}h: {u.title}",
                description=f"{u.course_code} deadline approaching. Finalize and submit your work before cutoff.",
                action_label="Go to Submission",
                action_link="/assignments",
            )
        )

    # Recommendation: Incomplete module continuation
    lagging_courses = [cp for cp in courses_progress if cp.progress_percentage < 60.0 and cp.total_lessons > 0]
    for lc in lagging_courses[:2]:
        recommendations.append(
            PersonalizedRecommendation(
                id=f"rec-progress-{lc.course_id}",
                category="learning_progress",
                priority="medium",
                title=f"Continue Modules: {lc.course_code}",
                description=f"You have completed {lc.completed_lessons} of {lc.total_lessons} lessons ({lc.progress_percentage}%). Resume reading to stay on track.",
                action_label="Resume Course",
                action_link=f"/courses",
            )
        )

    # Recommendation: Attendance alert
    if overall_att_rate < 80.0:
        recommendations.append(
            PersonalizedRecommendation(
                id="rec-attendance-warning",
                category="academic_alert",
                priority="high",
                title="Attendance Threshold Warning",
                description=f"Your overall attendance is currently {overall_att_rate}%, below the 80% institutional threshold. Please consult your academic advisor.",
                action_label="Review Attendance",
                action_link="/attendance",
            )
        )

    # Recommendation: Honor/Dean's standing or study resource
    if student.gpa and student.gpa >= 3.5:
        recommendations.append(
            PersonalizedRecommendation(
                id="rec-honor-standing",
                category="study_resource",
                priority="low",
                title="Distinguished Honor Standing",
                description=f"Cumulative GPA: {round(student.gpa, 2)}. You qualify for student research mentorship and teaching assistantship tracks.",
                action_label="Explore Mentorship",
                action_link="/alumni",
            )
        )

    pending_tasks = len([d for d in upcoming_deadlines if d.submission_status in {"pending", "unsubmitted"}])

    return PersonalizedStudentDashboardOut(
        student_id=student.student_id,
        full_name=current_user.full_name or student.student_id,
        email=current_user.email,
        faculty=student.faculty or "",
        department=student.department or "",
        program=student.program or "",
        year_of_study=student.year_of_study or 1,
        semester=student.semester or 1,
        gpa=round(student.gpa or 0.0, 2),
        credits_earned=student.credits_earned or 0,
        overall_attendance_rate=overall_att_rate,
        enrolled_courses_count=len(enrolled_courses),
        pending_tasks_count=pending_tasks,
        unread_notifications_count=unread_notifs,
        courses_progress=courses_progress,
        upcoming_deadlines=upcoming_deadlines,
        upcoming_classes=upcoming_classes,
        recent_announcements=recent_announcements,
        recommendations=recommendations,
    )
