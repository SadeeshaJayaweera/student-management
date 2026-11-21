from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, Lecturer,
    WellbeingSupportRequest, WellbeingAppointment, WellbeingResource
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_student_wellbeing_and_support_workflows(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student, Counselor (Lecturer), and External User
    student_user = User(
        email="wb_student@nsbm.ac.lk",
        username="wb_student",
        hashed_password=hash_password("Pass123!"),
        full_name="Chamodi Wickramasinghe",
        role=UserRole.STUDENT,
        is_active=True,
    )
    counselor_user = User(
        email="wb_counselor@nsbm.ac.lk",
        username="wb_counselor",
        hashed_password=hash_password("Pass123!"),
        full_name="Dr. Anura Senanayake",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add_all([student_user, counselor_user])
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-WB-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=2,
        semester=1,
        gpa=3.6,
        credits_earned=60,
    )
    counselor_profile = Lecturer(
        user_id=counselor_user.id,
        lecturer_id="LEC-WB-01",
        faculty="Computing",
        department="Student Wellness & Guidance",
    )
    test_session.add_all([student, counselor_profile])
    await test_session.commit()

    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    counselor_token = create_access_token({"sub": str(counselor_user.id), "role": "lecturer"})

    student_headers = {"Authorization": f"Bearer {student_token}"}
    counselor_headers = {"Authorization": f"Bearer {counselor_token}"}

    # 2. Student Submits Confidential Support Request
    create_req_res = await client.post(
        "/api/wellbeing/requests",
        headers=student_headers,
        json={
            "request_type": "academic_stress",
            "subject": "Overwhelming Exam Pressure and Burnout",
            "description": "I have been struggling with severe fatigue and anxiety leading into the upcoming semester finals.",
            "urgency": "crisis",
            "is_confidential": True,
        },
    )
    assert create_req_res.status_code == 201
    req_data = create_req_res.json()
    req_id = req_data["id"]
    assert req_data["status"] == "submitted"
    assert req_data["urgency"] == "crisis"
    assert req_data["is_confidential"] is True

    # 3. Student views their own support requests
    my_requests_res = await client.get("/api/wellbeing/requests/my", headers=student_headers)
    assert my_requests_res.status_code == 200
    my_list = my_requests_res.json()
    assert len(my_list) == 1
    assert my_list[0]["id"] == req_id

    # 4. Counselor views triage queue (Student cannot access)
    forbidden_res = await client.get("/api/wellbeing/counselor/requests", headers=student_headers)
    assert forbidden_res.status_code == 403

    counselor_queue_res = await client.get("/api/wellbeing/counselor/requests", headers=counselor_headers)
    assert counselor_queue_res.status_code == 200
    queue = counselor_queue_res.json()
    assert len(queue) >= 1
    assert queue[0]["id"] == req_id
    assert queue[0]["urgency"] == "crisis"

    # 5. Counselor updates status to in_progress
    status_update_res = await client.put(
        f"/api/wellbeing/requests/{req_id}/status",
        headers=counselor_headers,
        json={
            "status": "in_progress",
            "resolution_notes": "Reviewed intake notes; scheduling an urgent counseling session.",
        },
    )
    assert status_update_res.status_code == 200
    assert status_update_res.json()["status"] == "in_progress"

    # 6. Counselor schedules an appointment
    appt_time = datetime.utcnow() + timedelta(days=1)
    appt_res = await client.post(
        f"/api/wellbeing/requests/{req_id}/appointments",
        headers=counselor_headers,
        json={
            "scheduled_at": appt_time.isoformat(),
            "duration_minutes": 50,
            "appointment_type": "virtual",
            "location_or_link": "https://meet.nsbm.ac.lk/counseling-room-01",
            "meeting_notes": "First evaluation and stress management plan.",
        },
    )
    assert appt_res.status_code == 201
    appt_data = appt_res.json()
    assert appt_data["duration_minutes"] == 50
    assert "counseling-room-01" in appt_data["location_or_link"]

    # 7. Student checks my requests and sees scheduled appointment
    my_updated_res = await client.get("/api/wellbeing/requests/my", headers=student_headers)
    assert my_updated_res.status_code == 200
    updated_req = my_updated_res.json()[0]
    assert updated_req["status"] == "scheduled"
    assert len(updated_req["appointments"]) == 1
    assert updated_req["appointments"][0]["id"] == appt_data["id"]

    # 8. Staff creates wellness resource
    resource_create_res = await client.post(
        "/api/wellbeing/resources",
        headers=counselor_headers,
        json={
            "title": "Exam Stress Relief & Guided Breathing Exercises",
            "category": "stress_management",
            "description": "5-minute evidence-based mindfulness and audio breathing techniques.",
            "content_url": "https://wellness.nsbm.ac.lk/mindfulness/exam-calm",
            "emergency_phone": "1926",
            "is_crisis_resource": False,
            "is_featured": True,
        },
    )
    assert resource_create_res.status_code == 201
    res_data = resource_create_res.json()
    assert res_data["category"] == "stress_management"

    # 9. Student retrieves wellness resources directory
    resources_list_res = await client.get("/api/wellbeing/resources?category=stress_management", headers=student_headers)
    assert resources_list_res.status_code == 200
    res_list = resources_list_res.json()
    assert len(res_list) >= 1
    assert any(r["title"] == "Exam Stress Relief & Guided Breathing Exercises" for r in res_list)
