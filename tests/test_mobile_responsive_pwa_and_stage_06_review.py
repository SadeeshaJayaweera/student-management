from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, Lecturer, Course, Enrollment,
    TimetableSlot, AttendanceSession, StudentTask,
    CollaborationWorkspace, CollaborationWorkspaceMember,
    Conversation, ConversationParticipant, Message,
    Notification, CourseEvaluationSurvey, SurveyQuestion,
    WellbeingSupportRequest, WellbeingResource
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_mobile_responsive_pwa_endpoints(client: AsyncClient):
    """Verify Progressive Web App manifest and Service Worker endpoints."""
    # 1. Manifest Endpoint
    manifest_res = await client.get("/manifest.json")
    assert manifest_res.status_code == 200
    manifest = manifest_res.json()
    assert manifest["short_name"] == "EduSphere"
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "/"
    assert manifest["theme_color"] == "#050510"

    # 2. Service Worker Endpoint
    sw_res = await client.get("/sw.js")
    assert sw_res.status_code == 200
    assert "application/javascript" in sw_res.headers.get("content-type", "")
    assert sw_res.headers.get("service-worker-allowed") == "/"
    assert "edusphere-pwa-v1" in sw_res.text


@pytest.mark.asyncio
async def test_stage_06_student_experience_comprehensive_e2e(
    client: AsyncClient,
    test_session: AsyncSession
):
    """
    Comprehensive integration verification for Stage 06: Student Experience and Collaboration.
    Validates Changes 51 through 60 end-to-end.
    """
    # 1. Setup Student and Lecturer Users
    student_user = User(
        email="stage6_student@nsbm.ac.lk",
        username="stage6_student",
        hashed_password=hash_password("Pass123!"),
        full_name="Tharindu Alwis",
        role=UserRole.STUDENT,
        is_active=True,
    )
    lecturer_user = User(
        email="stage6_lecturer@nsbm.ac.lk",
        username="stage6_lecturer",
        hashed_password=hash_password("Pass123!"),
        full_name="Dr. Ruwan Wickrama",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add_all([student_user, lecturer_user])
    await test_session.commit()

    student_profile = Student(
        user_id=student_user.id,
        student_id="STU-S6-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=1,
        gpa=3.82,
        credits_earned=75,
    )
    lecturer_profile = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-S6-01",
        faculty="Computing",
        department="Software Engineering",
    )
    test_session.add_all([student_profile, lecturer_profile])
    await test_session.commit()

    course = Course(
        course_code="SE310",
        title="Mobile Architecture and Distributed Systems",
        credits=4,
        faculty="Computing",
        department="Software Engineering",
        semester=1,
        year=3,
        lecturer_id=lecturer_profile.id,
    )
    test_session.add(course)
    await test_session.commit()

    enrollment = Enrollment(
        student_id=student_profile.id,
        course_id=course.id,
        status="active",
    )
    test_session.add(enrollment)
    await test_session.commit()

    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": "lecturer"})
    student_headers = {"Authorization": f"Bearer {student_token}"}
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}

    # ---------------------------------------------------------
    # Change 51: Personalized Student Dashboard
    # ---------------------------------------------------------
    dash_res = await client.get("/api/students/dashboard/personalized", headers=student_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["full_name"] == "Tharindu Alwis"
    assert dash_data["gpa"] == 3.82

    # ---------------------------------------------------------
    # Change 52: Advanced Student Timetable & iCal export
    # ---------------------------------------------------------
    slot = TimetableSlot(
        course_id=course.id,
        title="SE310 Lecture",
        day_of_week="Monday",
        start_time="09:00",
        end_time="11:00",
        room="Audi 02",
        slot_type="lecture",
        lecturer_id=lecturer_profile.id,
    )
    test_session.add(slot)
    await test_session.commit()

    tt_res = await client.get("/api/timetable/student", headers=student_headers)
    assert tt_res.status_code == 200
    assert len(tt_res.json()) >= 1

    ical_res = await client.get("/api/timetable/ical/export", headers=student_headers)
    assert ical_res.status_code == 200
    assert "BEGIN:VCALENDAR" in ical_res.text

    # ---------------------------------------------------------
    # Change 53: Attendance & PIN check-in
    # ---------------------------------------------------------
    sess_res = await client.post(
        "/api/attendance/sessions",
        headers=lecturer_headers,
        json={
            "course_id": course.id,
            "session_title": "Mobile PWA Principles",
            "session_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "start_time": "09:00",
            "end_time": "11:00",
            "allow_self_checkin": True,
            "code_valid_minutes": 120,
        },
    )
    assert sess_res.status_code == 201
    sess_data = sess_res.json()
    session_id = sess_data["id"]
    checkin_code = sess_data["checkin_code"]

    checkin_res = await client.post(
        f"/api/attendance/sessions/{session_id}/checkin",
        headers=student_headers,
        json={"checkin_code": checkin_code},
    )
    assert checkin_res.status_code == 200
    assert checkin_res.json()["success"] is True

    # ---------------------------------------------------------
    # Change 54: Student Calendar & Tasks
    # ---------------------------------------------------------
    now = datetime.utcnow()
    task_res = await client.post(
        "/api/tasks",
        headers=student_headers,
        json={
            "title": "Review Service Worker Caching Strategies",
            "priority": "high",
            "due_date": (now + timedelta(days=2)).isoformat(),
        },
    )
    assert task_res.status_code == 201

    tasks_list = await client.get("/api/tasks", headers=student_headers)
    assert tasks_list.status_code == 200
    assert any(t["title"] == "Review Service Worker Caching Strategies" for t in tasks_list.json())

    event_res = await client.post(
        "/api/calendar/events",
        headers=student_headers,
        json={
            "title": "PWA Workshop Session",
            "start_time": (now + timedelta(days=3)).isoformat(),
            "end_time": (now + timedelta(days=3, hours=2)).isoformat(),
            "event_type": "study_session",
        },
    )
    assert event_res.status_code == 201

    cal_res = await client.get("/api/calendar/events", headers=student_headers)
    assert cal_res.status_code == 200
    assert any(ev["title"] == "PWA Workshop Session" for ev in cal_res.json())

    # ---------------------------------------------------------
    # Change 55: Collaboration Spaces
    # ---------------------------------------------------------
    ws_res = await client.post(
        "/api/collaboration/workspaces",
        headers=student_headers,
        json={
            "course_id": course.id,
            "name": "Mobile Systems Study Group",
            "description": "Collaborative PWA exercises",
            "topic": "Progressive Web Apps",
            "visibility": "course_public",
        },
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # ---------------------------------------------------------
    # Change 56: Messaging & Communication
    # ---------------------------------------------------------
    msg_res = await client.post(
        "/api/messaging/conversations",
        headers=student_headers,
        json={
            "recipient_id": lecturer_user.id,
            "subject": "Question about PWA manifest scope",
            "thread_type": "course_inquiry",
            "initial_message": "Hello Dr. Ruwan, does manifest scope apply to all routes?",
        },
    )
    assert msg_res.status_code == 201
    conv_id = msg_res.json()["id"]

    unread_res = await client.get("/api/messaging/unread-count", headers=lecturer_headers)
    assert unread_res.status_code == 200
    assert unread_res.json()["unread_count"] >= 1

    # ---------------------------------------------------------
    # Change 57: Advanced Notification Center
    # ---------------------------------------------------------
    notif_res = await client.post(
        "/api/notifications",
        headers=lecturer_headers,
        json={
            "user_id": student_user.id,
            "title": "Lecture Notes Posted",
            "message": "Slides for Chapter 5 are now online.",
            "category": "academic",
            "priority": "normal",
        },
    )
    assert notif_res.status_code == 201

    stats_res = await client.get("/api/notifications/stats", headers=student_headers)
    assert stats_res.status_code == 200
    assert stats_res.json()["total_unread"] >= 1

    # ---------------------------------------------------------
    # Change 58: Course Evaluation & Feedback
    # ---------------------------------------------------------
    eval_res = await client.post(
        "/api/evaluations/surveys",
        headers=lecturer_headers,
        json={
            "course_id": course.id,
            "title": "Mid-Term Module Evaluation",
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_published": True,
            "is_anonymous": True,
        },
    )
    assert eval_res.status_code == 201
    eval_id = eval_res.json()["id"]

    pending_evals = await client.get("/api/evaluations/student/pending", headers=student_headers)
    assert pending_evals.status_code == 200
    assert any(e["id"] == eval_id for e in pending_evals.json())

    # ---------------------------------------------------------
    # Change 59: Student Wellbeing & Counseling Workflows
    # ---------------------------------------------------------
    wb_res = await client.post(
        "/api/wellbeing/requests",
        headers=student_headers,
        json={
            "request_type": "academic_stress",
            "subject": "Workload Balancing Assistance",
            "description": "Seeking time management strategies between coursework and exams.",
            "urgency": "normal",
        },
    )
    assert wb_res.status_code == 201
    wb_id = wb_res.json()["id"]

    my_wb = await client.get("/api/wellbeing/requests/my", headers=student_headers)
    assert my_wb.status_code == 200
    assert any(r["id"] == wb_id for r in my_wb.json())
