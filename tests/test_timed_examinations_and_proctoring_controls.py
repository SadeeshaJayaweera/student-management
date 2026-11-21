from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    Quiz, ExamProctoringSession, ExamProctoringEvent
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_timed_examinations_and_proctoring_controls_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Enrolled Student, Outsider Student
    admin_user = User(
        email="proc_admin@nsbm.ac.lk",
        username="proc_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Chief Invigilator",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="proc_lecturer@nsbm.ac.lk",
        username="proc_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Tim Berners-Lee",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_user = User(
        email="proc_student@nsbm.ac.lk",
        username="proc_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Linus Torvalds",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)

    outsider_user = User(
        email="proc_outsider@nsbm.ac.lk",
        username="proc_outsider",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Outsider User",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(outsider_user)
    await test_session.commit()

    # Profiles
    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-PRC-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add(lecturer)

    student = Student(
        user_id=student_user.id,
        student_id="STU-PRC-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=3,
        semester=1,
    )
    test_session.add(student)

    outsider = Student(
        user_id=outsider_user.id,
        student_id="STU-PRC-02",
        faculty="Business",
        department="Marketing",
        program="BSc Marketing",
        year_of_study=1,
        semester=1,
    )
    test_session.add(outsider)
    await test_session.commit()

    # Course
    course = Course(
        course_code="CS315",
        title="Operating Systems & Kernel Architecture",
        description="Process synchronization, memory virtualization, and file systems.",
        credits=4,
        faculty="Computing",
        department="Computer Science",
        semester=1,
        year=3,
        lecturer_id=lecturer.id,
    )
    test_session.add(course)
    await test_session.commit()

    # Enrollment
    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        status="active",
    )
    test_session.add(enrollment)

    # Timed Quiz / Exam
    now = datetime.utcnow()
    quiz = Quiz(
        course_id=course.id,
        creator_id=lecturer_user.id,
        title="CS315 Final Proctored Examination",
        description="Comprehensive timed examination with browser proctoring.",
        time_limit_minutes=60,
        passing_score_percentage=50.0,
        max_attempts=1,
        status="published",
        available_from=now - timedelta(days=1),
        due_date=now + timedelta(days=3),
    )
    test_session.add(quiz)
    await test_session.commit()

    # Auth tokens
    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": lecturer_user.role.value})
    student_token = create_access_token({"sub": str(student_user.id), "role": student_user.role.value})
    outsider_token = create_access_token({"sub": str(outsider_user.id), "role": outsider_user.role.value})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    # 2. Outsider cannot start proctoring session -> 403 Forbidden
    start_payload = {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (EduSphere SafeBrowser 1.0)",
    }
    r = await client.post(f"/api/exams/{quiz.id}/proctoring/start", json=start_payload, headers=outsider_headers)
    assert r.status_code == 403

    # 3. Enrolled student initiates proctoring session
    r = await client.post(f"/api/exams/{quiz.id}/proctoring/start", json=start_payload, headers=student_headers)
    assert r.status_code == 201
    session_data = r.json()
    session_id = session_data["id"]
    session_token = session_data["session_token"]
    assert session_token.startswith("NSBM-PROC-")
    assert session_data["status"] == "active"
    assert session_data["remaining_seconds"] > 3500.0  # Approx 60 min
    assert session_data["is_flagged"] is False

    # 4. Student sends keep-alive heartbeat
    r = await client.post(f"/api/proctoring/{session_token}/heartbeat")
    assert r.status_code == 200
    hb = r.json()
    assert hb["status"] == "active"
    assert hb["remaining_seconds"] > 3500.0
    assert hb["is_flagged"] is False

    # 5. Client records proctoring security events (tab switches & fullscreen loss)
    # Event 1: Tab switch
    r = await client.post(f"/api/proctoring/{session_token}/events", json={"event_type": "tab_switch", "severity": "medium"})
    assert r.status_code == 201
    # Event 2: Tab switch
    r = await client.post(f"/api/proctoring/{session_token}/events", json={"event_type": "tab_switch", "severity": "medium"})
    assert r.status_code == 201
    # Event 3: Tab switch (reaches threshold of 3 -> flags session)
    r = await client.post(f"/api/proctoring/{session_token}/events", json={"event_type": "tab_switch", "severity": "high"})
    assert r.status_code == 201
    # Event 4: Fullscreen exit
    r = await client.post(f"/api/proctoring/{session_token}/events", json={"event_type": "fullscreen_exit", "severity": "high"})
    assert r.status_code == 201

    # 6. Check student session status
    r = await client.get(f"/api/proctoring/{session_token}/status")
    assert r.status_code == 200
    status_data = r.json()
    assert status_data["tab_switch_count"] == 3
    assert status_data["fullscreen_exit_count"] == 1
    assert status_data["is_flagged"] is True
    assert "Suspicious activity threshold exceeded" in status_data["flag_reason"]
    assert len(status_data["events"]) == 4

    # 7. Student or outsider cannot view live invigilator dashboard -> 403
    r = await client.get(f"/api/exams/{quiz.id}/proctoring/live", headers=student_headers)
    assert r.status_code == 403

    # 8. Instructor accesses live invigilation dashboard
    r = await client.get(f"/api/exams/{quiz.id}/proctoring/live", headers=lecturer_headers)
    assert r.status_code == 200
    live_sessions = r.json()
    assert len(live_sessions) == 1
    assert live_sessions[0]["id"] == session_id
    assert live_sessions[0]["is_flagged"] is True

    # 9. Instructor forcibly terminates session for unauthorized tab switching
    term_params = {"reason": "Multiple unauthorized window blurs and tab switching detected"}
    r = await client.post(f"/api/exams/{quiz.id}/proctoring/{session_id}/terminate", params=term_params, headers=lecturer_headers)
    assert r.status_code == 200
    term_data = r.json()
    assert term_data["status"] == "terminated"
    assert "Multiple unauthorized window blurs" in term_data["flag_reason"]

    # 10. Heartbeat on expired session triggers auto-submission
    session_obj = await test_session.get(ExamProctoringSession, session_id)
    session_obj.expires_at = datetime.utcnow() - timedelta(minutes=5)
    await test_session.commit()

    r = await client.post(f"/api/proctoring/{session_token}/heartbeat")
    assert r.status_code == 200
    assert r.json()["status"] == "auto_submitted"
    assert r.json()["remaining_seconds"] == 0.0
