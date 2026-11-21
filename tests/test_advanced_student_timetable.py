import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, Lecturer, Course, Enrollment, TimetableSlot
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_advanced_student_timetable_complete(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, and Student users
    admin_user = User(
        email="tt_admin@nsbm.ac.lk",
        username="tt_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Timetable Administrator",
        role=UserRole.ADMIN,
        is_active=True,
    )
    lecturer_user = User(
        email="tt_lecturer@nsbm.ac.lk",
        username="tt_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Alan Turing",
        role=UserRole.LECTURER,
        is_active=True,
    )
    student_user = User(
        email="tt_student@nsbm.ac.lk",
        username="tt_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Grace Hopper",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([admin_user, lecturer_user, student_user])
    await test_session.commit()

    student_profile = Student(
        user_id=student_user.id,
        student_id="STU-TT-99",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=2,
        semester=1,
        gpa=3.85,
        credits_earned=60,
    )
    lecturer_profile = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-TT-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add_all([student_profile, lecturer_profile])
    await test_session.commit()

    course_a = Course(
        course_code="CS201",
        title="Data Structures & Algorithms",
        description="Core algorithms",
        credits=4,
        department="Computer Science",
        faculty="Computing",
        semester=1,
        year=2,
        lecturer_id=lecturer_profile.id,
    )
    course_b = Course(
        course_code="CS202",
        title="Computer Architecture",
        description="CPU and memory hierarchy",
        credits=3,
        department="Computer Science",
        faculty="Computing",
        semester=1,
        year=2,
        lecturer_id=lecturer_profile.id,
    )
    test_session.add_all([course_a, course_b])
    await test_session.commit()

    # Enroll student in Course A
    enrollment_a = Enrollment(
        student_id=student_profile.id,
        course_id=course_a.id,
        status="active",
    )
    test_session.add(enrollment_a)
    await test_session.commit()

    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 2. Test conflict check endpoint before creating slots
    check_resp = await client.post(
        "/api/timetable/conflicts/check",
        json={
            "course_id": course_a.id,
            "room": "Auditorium 1",
            "day_of_week": 0,  # Monday
            "start_time": "09:00",
            "end_time": "11:00",
        },
        headers=admin_headers,
    )
    assert check_resp.status_code == 200
    assert check_resp.json()["has_conflict"] is False

    # 3. Create Slot 1 on Monday 09:00 - 11:00 in Auditorium 1
    create_slot1_resp = await client.post(
        "/api/timetable/slots",
        json={
            "course_id": course_a.id,
            "lecturer_id": lecturer_user.id,
            "day_of_week": 0,
            "start_time": "09:00",
            "end_time": "11:00",
            "title": "CS201 Lecture - Sorting",
            "slot_type": "lecture",
            "room": "Auditorium 1",
            "building": "Main Wing",
            "color": "#3B82F6",
            "allow_conflicts": False,
        },
        headers=admin_headers,
    )
    assert create_slot1_resp.status_code == 201
    slot1_data = create_slot1_resp.json()
    assert slot1_data["title"] == "CS201 Lecture - Sorting"
    assert slot1_data["course_code"] == "CS201"
    slot1_id = slot1_data["id"]

    # 4. Attempt to create conflicting Slot (room double-booking) on Monday 10:00 - 12:00 in Auditorium 1
    conflict_resp = await client.post(
        "/api/timetable/slots",
        json={
            "course_id": course_b.id,
            "day_of_week": 0,
            "start_time": "10:00",
            "end_time": "12:00",
            "title": "CS202 Hardware Lab",
            "slot_type": "lab",
            "room": "Auditorium 1",
            "allow_conflicts": False,
        },
        headers=admin_headers,
    )
    assert conflict_resp.status_code == 409
    assert "Schedule conflict detected" in str(conflict_resp.json())

    # 5. Create with allow_conflicts=True override
    override_resp = await client.post(
        "/api/timetable/slots",
        json={
            "course_id": course_b.id,
            "day_of_week": 0,
            "start_time": "10:00",
            "end_time": "12:00",
            "title": "CS202 Hardware Lab",
            "slot_type": "lab",
            "room": "Auditorium 1",
            "allow_conflicts": True,
        },
        headers=admin_headers,
    )
    assert override_resp.status_code == 201
    slot2_id = override_resp.json()["id"]

    # 6. Fetch course-specific timetable
    course_tt_resp = await client.get(
        f"/api/timetable/courses/{course_a.id}",
        headers=student_headers,
    )
    assert course_tt_resp.status_code == 200
    course_slots = course_tt_resp.json()
    assert len(course_slots) == 1
    assert course_slots[0]["id"] == slot1_id

    # 7. Fetch student timetable: student is enrolled in Course A only
    stu_tt_resp = await client.get("/api/timetable/student", headers=student_headers)
    assert stu_tt_resp.status_code == 200
    stu_tt_data = stu_tt_resp.json()
    assert stu_tt_data["student_id"] == "STU-TT-99"
    # Find Monday (day_of_week == 0)
    monday_slots = [day["slots"] for day in stu_tt_data["schedule"] if day["day_of_week"] == 0][0]
    assert len(monday_slots) == 1
    assert monday_slots[0]["title"] == "CS201 Lecture - Sorting"

    # Now enroll student in Course B and check timetable conflict detection on student schedule
    enrollment_b = Enrollment(
        student_id=student_profile.id,
        course_id=course_b.id,
        status="active",
    )
    test_session.add(enrollment_b)
    await test_session.commit()

    stu_tt_resp2 = await client.get("/api/timetable/student", headers=student_headers)
    assert stu_tt_resp2.status_code == 200
    stu_tt_data2 = stu_tt_resp2.json()
    assert len(stu_tt_data2["conflicts_detected"]) >= 1
    assert stu_tt_data2["conflicts_detected"][0]["conflict_type"] == "student_overlap"

    # 8. Test iCalendar (.ics) export
    ical_resp = await client.get("/api/timetable/ical/export", headers=student_headers)
    assert ical_resp.status_code == 200
    assert "text/calendar" in ical_resp.headers["content-type"]
    ical_body = ical_resp.text
    assert "BEGIN:VCALENDAR" in ical_body
    assert "VERSION:2.0" in ical_body
    assert "CS201: CS201 Lecture - Sorting" in ical_body
    assert "RRULE:FREQ=WEEKLY" in ical_body
    assert "END:VCALENDAR" in ical_body

    # 9. Test slot update and delete
    update_resp = await client.put(
        f"/api/timetable/slots/{slot1_id}",
        json={"title": "CS201 Advanced Sorting & Heaps", "allow_conflicts": True},
        headers=admin_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "CS201 Advanced Sorting & Heaps"

    delete_resp = await client.delete(f"/api/timetable/slots/{slot2_id}", headers=admin_headers)
    assert delete_resp.status_code == 204
