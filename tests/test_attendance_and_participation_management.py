from datetime import datetime, date, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, Lecturer, Course, Enrollment,
    Attendance, AttendanceStatus, AttendanceSession, AttendanceCorrectionRequest
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_attendance_and_participation_complete(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Lecturer and Student users
    lecturer_user = User(
        email="att_lecturer@nsbm.ac.lk",
        username="att_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Dr. Attendance Director",
        role=UserRole.LECTURER,
        is_active=True,
    )
    student_user = User(
        email="att_student@nsbm.ac.lk",
        username="att_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Kavindu Fernando",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([lecturer_user, student_user])
    await test_session.commit()

    lecturer_profile = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-ATT-01",
        faculty="Computing",
        department="Software Engineering",
    )
    student_profile = Student(
        user_id=student_user.id,
        student_id="STU-ATT-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=1,
        gpa=3.70,
        credits_earned=75,
    )
    test_session.add_all([lecturer_profile, student_profile])
    await test_session.commit()

    course = Course(
        course_code="SE305",
        title="Software Quality Assurance",
        description="Testing and verification",
        credits=3,
        department="Software Engineering",
        faculty="Computing",
        semester=1,
        year=3,
        lecturer_id=lecturer_profile.id,
    )
    test_session.add(course)
    await test_session.commit()

    # Enroll student
    enrollment = Enrollment(
        student_id=student_profile.id,
        course_id=course.id,
        status="active",
    )
    test_session.add(enrollment)
    await test_session.commit()

    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": "lecturer"})
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}

    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 2. Lecturer creates an attendance session with PIN check-in enabled
    today_str = date.today().isoformat()
    session_resp = await client.post(
        "/api/attendance/sessions",
        json={
            "course_id": course.id,
            "session_title": "Lecture 01: SQA Foundations",
            "session_date": today_str,
            "start_time": "09:00",
            "end_time": "11:00",
            "allow_self_checkin": True,
            "code_valid_minutes": 120,
        },
        headers=lecturer_headers,
    )
    assert session_resp.status_code == 201
    session_data = session_resp.json()
    assert session_data["session_title"] == "Lecture 01: SQA Foundations"
    assert session_data["checkin_code"] is not None
    assert len(session_data["checkin_code"]) == 6
    session_id = session_data["id"]
    valid_code = session_data["checkin_code"]

    # 3. Student tries invalid PIN check-in -> Expect 400
    bad_checkin = await client.post(
        f"/api/attendance/sessions/{session_id}/checkin",
        json={"checkin_code": "000000"},
        headers=student_headers,
    )
    assert bad_checkin.status_code == 400
    assert "Invalid check-in code" in bad_checkin.json()["detail"]

    # 4. Student checks in with valid PIN
    good_checkin = await client.post(
        f"/api/attendance/sessions/{session_id}/checkin",
        json={"checkin_code": valid_code},
        headers=student_headers,
    )
    assert good_checkin.status_code == 200
    assert good_checkin.json()["success"] is True

    # 5. Lecturer inspects session roster
    roster_resp = await client.get(
        f"/api/attendance/sessions/{session_id}/roster",
        headers=lecturer_headers,
    )
    assert roster_resp.status_code == 200
    roster = roster_resp.json()
    assert len(roster) == 1
    assert roster[0]["student_id"] == student_profile.id
    assert roster[0]["status"] == "present"
    assert roster[0]["checkin_method"] == "code"

    # 6. Lecturer batch marks participation score for student
    batch_resp = await client.post(
        f"/api/attendance/sessions/{session_id}/roster",
        json={
            "items": [
                {
                    "student_id": student_profile.id,
                    "status": "present",
                    "participation_score": 9.5,
                    "notes": "Excellent active participation in SQA discussion",
                }
            ]
        },
        headers=lecturer_headers,
    )
    assert batch_resp.status_code == 200
    assert batch_resp.json()["updated_count"] == 1

    # 7. Student submits absence excuse / correction request for a previous date
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    excuse_resp = await client.post(
        "/api/attendance/corrections",
        json={
            "course_id": course.id,
            "session_id": session_id,
            "attendance_date": yesterday_str,
            "requested_status": "excused",
            "reason": "University varsity basketball tournament representation",
            "supporting_document_url": "https://nsbm.ac.lk/sports/duty_leave_letter.pdf",
        },
        headers=student_headers,
    )
    assert excuse_resp.status_code == 201
    excuse_data = excuse_resp.json()
    assert excuse_data["requested_status"] == "excused"
    assert excuse_data["status"] == "pending"
    corr_id = excuse_data["id"]

    # 8. Lecturer reviews and approves excuse
    resolve_resp = await client.put(
        f"/api/attendance/corrections/{corr_id}/resolve",
        json={
            "status": "approved",
            "review_comment": "Approved official duty leave for varsity sports representation.",
        },
        headers=lecturer_headers,
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "approved"

    # 9. Check course attendance summary
    summary_resp = await client.get(
        f"/api/attendance/courses/{course.id}/summary",
        headers=student_headers,
    )
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["course_code"] == "SE305"
    assert summary["policy_threshold"] == 80.0
    assert summary["attendance_rate"] >= 80.0
    assert summary["status_level"] == "good"
    assert summary["present_count"] >= 1
    assert summary["excused_count"] >= 1
