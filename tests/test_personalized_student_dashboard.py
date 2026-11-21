from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, Lecturer, Course, Enrollment,
    CourseModule, CourseLesson, StudentLessonProgress,
    Assignment, AssignmentSubmission, AssignmentStatus,
    Quiz, VirtualClassroomSession, CourseAnnouncement,
    Attendance, Notification
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_personalized_student_dashboard_endpoints(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student, Lecturer, and Course
    now = datetime.utcnow()
    student_user = User(
        email="dash_student@nsbm.ac.lk",
        username="dash_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Samantha Ray",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)

    lecturer_user = User(
        email="dash_lecturer@nsbm.ac.lk",
        username="dash_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Dr. Victor Frankenstein",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)
    await test_session.commit()

    # Profiles
    student = Student(
        user_id=student_user.id,
        student_id="STU-DASH-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc (Hons) Software Engineering",
        year_of_study=3,
        semester=1,
        gpa=3.85,
        credits_earned=75,
    )
    test_session.add(student)

    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-DASH-01",
        faculty="Computing",
        department="Software Engineering",
    )
    test_session.add(lecturer)
    await test_session.commit()

    # Course
    course = Course(
        course_code="SE302",
        title="Software Architecture & Cloud Systems",
        description="Microservices, distributed systems, and cloud patterns.",
        credits=4,
        faculty="Computing",
        department="Software Engineering",
        semester=1,
        year=3,
        lecturer_id=lecturer.id,
        delivery_method="hybrid",
        is_active=True,
    )
    test_session.add(course)
    await test_session.commit()

    # Enrollment
    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        status="enrolled",
    )
    test_session.add(enrollment)

    # 2. Modules & Lessons Progress
    module = CourseModule(
        course_id=course.id,
        title="Module 1: Cloud-Native Microservices",
        order_index=1,
        status="published",
    )
    test_session.add(module)
    await test_session.commit()

    lesson1 = CourseLesson(
        module_id=module.id,
        title="1.1 Service Decomposition Patterns",
        lesson_type="reading",
        order_index=1,
        is_published=True,
    )
    lesson2 = CourseLesson(
        module_id=module.id,
        title="1.2 Event-Driven Architecture",
        lesson_type="reading",
        order_index=2,
        is_published=True,
    )
    test_session.add_all([lesson1, lesson2])
    await test_session.commit()

    # Complete Lesson 1 for student
    progress = StudentLessonProgress(
        student_id=student.id,
        lesson_id=lesson1.id,
        status="completed",
        completed_at=now,
    )
    test_session.add(progress)

    # 3. Attendance Record (1 Present out of 2 = 50% attendance)
    att1 = Attendance(
        student_id=student.id,
        course_id=course.id,
        date=now.date() - timedelta(days=2),
        status="present",
    )
    att2 = Attendance(
        student_id=student.id,
        course_id=course.id,
        date=now.date() - timedelta(days=1),
        status="absent",
    )
    test_session.add_all([att1, att2])

    # 4. Upcoming Assignment Due in 2 Days
    assignment = Assignment(
        course_id=course.id,
        title="Kubernetes Deployment Manifests",
        due_date=now + timedelta(days=2),
        max_marks=100.0,
        weightage_percentage=20.0,
        status="published",
    )
    test_session.add(assignment)

    # 5. Virtual Classroom Session Tomorrow
    session = VirtualClassroomSession(
        course_id=course.id,
        host_id=lecturer_user.id,
        title="Live Workshop: Helm & CI/CD",
        start_time=now + timedelta(hours=20),
        end_time=now + timedelta(hours=22),
        provider="zoom",
        join_url="https://meet.nsbm.ac.lk/se302-live",
        status="scheduled",
    )
    test_session.add(session)

    # 6. Course Announcement
    announcement = CourseAnnouncement(
        course_id=course.id,
        author_id=lecturer_user.id,
        title="Midterm Assessment Guidelines Published",
        content="Please check the repository guidelines for deployment manifests.",
        is_pinned=True,
        published_at=now - timedelta(hours=2),
    )
    test_session.add(announcement)

    # 7. Unread Notification
    notification = Notification(
        user_id=student_user.id,
        title="Welcome to SE302",
        message="Course workspace is now unlocked.",
        notification_type="info",
        is_read=False,
    )
    test_session.add(notification)
    await test_session.commit()

    # Auth token
    student_token = create_access_token({"sub": str(student_user.id), "role": student_user.role.value})
    headers = {"Authorization": f"Bearer {student_token}"}

    # ─── 8. Test Personalized Dashboard API ───────────────────────────────────────
    res = await client.get("/api/students/dashboard/personalized", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Profile & standing
    assert data["student_id"] == "STU-DASH-01"
    assert data["full_name"] == "Samantha Ray"
    assert data["gpa"] == 3.85
    assert data["enrolled_courses_count"] == 1
    assert data["unread_notifications_count"] == 1
    assert data["overall_attendance_rate"] == 50.0  # 1 present out of 2

    # Course progress
    assert len(data["courses_progress"]) == 1
    cp = data["courses_progress"][0]
    assert cp["course_code"] == "SE302"
    assert cp["total_lessons"] == 2
    assert cp["completed_lessons"] == 1
    assert cp["progress_percentage"] == 50.0
    assert cp["attendance_rate"] == 50.0
    assert "Victor Frankenstein" in cp["lecturer_name"]

    # Upcoming Deadlines
    assert len(data["upcoming_deadlines"]) >= 1
    dl = data["upcoming_deadlines"][0]
    assert dl["title"] == "Kubernetes Deployment Manifests"
    assert dl["submission_status"] == "pending"
    assert 1.0 <= dl["days_remaining"] <= 2.1

    # Upcoming Classes
    assert len(data["upcoming_classes"]) == 1
    cls_item = data["upcoming_classes"][0]
    assert cls_item["title"] == "Live Workshop: Helm & CI/CD"
    assert "https://meet.nsbm.ac.lk" in cls_item["join_url"]

    # Recent Announcements
    assert len(data["recent_announcements"]) == 1
    ann = data["recent_announcements"][0]
    assert ann["is_pinned"] is True
    assert "Midterm Assessment" in ann["title"]

    # Recommendations
    assert len(data["recommendations"]) >= 2
    rec_cats = [r["category"] for r in data["recommendations"]]
    assert "urgent_deadline" in rec_cats
    assert "learning_progress" in rec_cats
    assert "academic_alert" in rec_cats  # Because attendance is 50% (< 80%)
    assert "study_resource" in rec_cats   # Because GPA is 3.85 (>= 3.5)
