from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course, Student, Lecturer, Enrollment
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_virtual_classrooms_and_live_sessions_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Enrolled Student, and Unenrolled Student
    admin_user = User(
        email="vc_admin@nsbm.ac.lk",
        username="vc_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="VC Administrator",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="vc_lecturer@nsbm.ac.lk",
        username="vc_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Dr. Cloud Specialist",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_user = User(
        email="vc_student@nsbm.ac.lk",
        username="vc_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Emma Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)

    outsider_user = User(
        email="vc_outsider@nsbm.ac.lk",
        username="vc_outsider",
        hashed_password=hash_password("StudentPass123!"),
        full_name="David Outsider",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(outsider_user)
    await test_session.commit()

    # Profiles
    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-VC-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add(lecturer)

    student = Student(
        user_id=student_user.id,
        student_id="STU-VC-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc CS",
        year_of_study=4,
        semester=1,
    )
    test_session.add(student)
    await test_session.commit()

    # Tokens & Headers
    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": lecturer_user.role.value})
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}

    student_token = create_access_token({"sub": str(student_user.id), "role": student_user.role.value})
    student_headers = {"Authorization": f"Bearer {student_token}"}

    outsider_token = create_access_token({"sub": str(outsider_user.id), "role": outsider_user.role.value})
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    # 2. Create Course and enroll student
    c_res = await client.post(
        "/api/courses",
        headers=admin_headers,
        json={
            "course_code": "CS430",
            "title": "Cloud Native Microservices",
            "credits": 4,
            "semester": 1,
            "year": 4,
            "lecturer_id": lecturer.id,
        }
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    enrollment = Enrollment(student_id=student.id, course_id=course_id, status="active")
    test_session.add(enrollment)
    await test_session.commit()

    # 3. Schedule Live Session
    # Student attempts to create session -> 403
    start_dt = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    end_dt = (datetime.utcnow() + timedelta(hours=3)).isoformat()

    bad_create = await client.post(
        f"/api/courses/{course_id}/live-sessions",
        headers=student_headers,
        json={
            "title": "Unauthorized Session",
            "join_url": "https://meet.nsbm.ac.lk/unauth",
            "start_time": start_dt,
            "end_time": end_dt,
        }
    )
    assert bad_create.status_code == 403

    # Lecturer schedules session
    session_res = await client.post(
        f"/api/courses/{course_id}/live-sessions",
        headers=lecturer_headers,
        json={
            "title": "Lecture 01: Service Mesh Architecture with Istio",
            "description": "Deep dive into ingress gateways, mTLS, and traffic shifting.",
            "provider": "zoom",
            "meeting_id": "987-6543-2100",
            "join_url": "https://zoom.us/j/98765432100",
            "host_url": "https://zoom.us/s/98765432100?role=host&token=secret123",
            "passcode": "istio2026",
            "start_time": start_dt,
            "end_time": end_dt,
            "is_recorded": True,
            "max_participants": 120,
            "session_settings": {"mute_on_entry": True, "enable_chat": True}
        }
    )
    assert session_res.status_code == 201
    session_data = session_res.json()
    session_id = session_data["id"]
    assert session_data["title"] == "Lecture 01: Service Mesh Architecture with Istio"
    assert session_data["host_name"] == "Dr. Cloud Specialist"
    assert session_data["host_url"] is not None

    # 4. Confidentiality of Host URLs
    # Student views session -> host_url must be None/hidden
    stu_view = await client.get(
        f"/api/live-sessions/{session_id}",
        headers=student_headers,
    )
    assert stu_view.status_code == 200
    assert stu_view.json()["host_url"] is None
    assert stu_view.json()["join_url"] == "https://zoom.us/j/98765432100"

    # Lecturer views session -> host_url is present
    lec_view = await client.get(
        f"/api/live-sessions/{session_id}",
        headers=lecturer_headers,
    )
    assert lec_view.status_code == 200
    assert lec_view.json()["host_url"] == "https://zoom.us/s/98765432100?role=host&token=secret123"

    # 5. Course Workspace Integration
    ws_res = await client.get(
        f"/api/courses/{course_id}/workspace",
        headers=student_headers,
    )
    assert ws_res.status_code == 200
    ws_data = ws_res.json()
    assert "upcoming_live_sessions" in ws_data
    assert len(ws_data["upcoming_live_sessions"]) == 1
    assert ws_data["upcoming_live_sessions"][0]["id"] == session_id

    # 6. Student Joins Live Session
    join_res = await client.post(
        f"/api/live-sessions/{session_id}/join?device_type=desktop_chrome",
        headers=student_headers,
    )
    assert join_res.status_code == 200
    join_data = join_res.json()
    assert join_data["session_id"] == session_id
    assert join_data["join_url"] == "https://zoom.us/j/98765432100"
    assert join_data["passcode"] == "istio2026"
    assert "attendance_id" in join_data

    # 7. Student Leaves Live Session
    leave_res = await client.post(
        f"/api/live-sessions/{session_id}/leave",
        headers=student_headers,
    )
    assert leave_res.status_code == 200
    leave_data = leave_res.json()
    assert leave_data["participant_name"] == "Emma Student"
    assert leave_data["left_at"] is not None
    assert leave_data["duration_minutes"] >= 1

    # 8. Lecturer Inspects Attendance Roster
    att_res = await client.get(
        f"/api/live-sessions/{session_id}/attendance",
        headers=lecturer_headers,
    )
    assert att_res.status_code == 200
    records = att_res.json()
    assert len(records) == 1
    assert records[0]["participant_name"] == "Emma Student"
    assert records[0]["duration_minutes"] >= 1

    # Student attempts to inspect attendance roster -> 403 Forbidden
    stu_att_fail = await client.get(
        f"/api/live-sessions/{session_id}/attendance",
        headers=student_headers,
    )
    assert stu_att_fail.status_code == 403

    # 9. Conclude Session and Attach Recording
    update_res = await client.patch(
        f"/api/live-sessions/{session_id}",
        headers=lecturer_headers,
        json={
            "status": "concluded",
            "recording_url": "https://storage.nsbm.ac.lk/recordings/cs430-lec01.mp4",
            "recording_duration_minutes": 115
        }
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "concluded"
    assert update_res.json()["recording_url"] == "https://storage.nsbm.ac.lk/recordings/cs430-lec01.mp4"

    # 10. BOLA Authorization: Unenrolled user cannot access
    out_join = await client.post(
        f"/api/live-sessions/{session_id}/join",
        headers=outsider_headers,
    )
    assert out_join.status_code == 403
