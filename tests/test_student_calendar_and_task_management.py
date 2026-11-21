from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, Lecturer, Course, Enrollment,
    Assignment, StudentTask, CalendarEvent
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_student_task_and_calendar_complete(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student, Lecturer, and Course
    lecturer_user = User(
        email="cal_lecturer@nsbm.ac.lk",
        username="cal_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Dr. Calendar Head",
        role=UserRole.LECTURER,
        is_active=True,
    )
    student_user = User(
        email="cal_student@nsbm.ac.lk",
        username="cal_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Janith Perera",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([lecturer_user, student_user])
    await test_session.commit()

    lecturer_profile = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-CAL-01",
        faculty="Computing",
        department="Software Engineering",
    )
    student_profile = Student(
        user_id=student_user.id,
        student_id="STU-CAL-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=2,
        gpa=3.65,
        credits_earned=80,
    )
    test_session.add_all([lecturer_profile, student_profile])
    await test_session.commit()

    course = Course(
        course_code="CS310",
        title="Distributed Systems",
        description="Scalable distributed architectures",
        credits=3,
        department="Software Engineering",
        faculty="Computing",
        semester=2,
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
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 2. Test Task Creation
    now = datetime.utcnow()
    due = now + timedelta(days=2)
    task_resp = await client.post(
        "/api/tasks",
        json={
            "course_id": course.id,
            "title": "Implement Raft consensus algorithm",
            "description": "Lab assignment 2 on leader election and log replication",
            "due_date": due.isoformat(),
            "priority": "urgent",
            "category": "assignment",
            "estimated_minutes": 120,
        },
        headers=student_headers,
    )
    assert task_resp.status_code == 201
    task_data = task_resp.json()
    assert task_data["title"] == "Implement Raft consensus algorithm"
    assert task_data["priority"] == "urgent"
    assert task_data["status"] == "todo"
    assert task_data["course_code"] == "CS310"
    task_id = task_data["id"]

    # 3. Test Task Listing
    list_resp = await client.get("/api/tasks", headers=student_headers)
    assert list_resp.status_code == 200
    tasks = list_resp.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_id

    # 4. Test Task Status Patch (mark completed)
    patch_resp = await client.patch(
        f"/api/tasks/{task_id}/status",
        json={"status": "completed"},
        headers=student_headers,
    )
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()
    assert patched_data["status"] == "completed"
    assert patched_data["completed_at"] is not None

    # 5. Test Task Metrics Endpoint
    metrics_resp = await client.get("/api/tasks/metrics", headers=student_headers)
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["total_tasks"] == 1
    assert metrics["completed_tasks"] == 1
    assert metrics["completion_rate"] == 100.0

    # 6. Test Calendar Event Creation (Personal Event)
    ev_start = now + timedelta(days=3)
    ev_end = ev_start + timedelta(hours=2)
    event_resp = await client.post(
        "/api/calendar/events",
        json={
            "course_id": course.id,
            "title": "Distributed Systems Group Discussion",
            "description": "Room 404 study session with team",
            "event_type": "personal",
            "start_time": ev_start.isoformat(),
            "end_time": ev_end.isoformat(),
            "location": "Discussion Pod 3",
            "color": "#4F46E5",
        },
        headers=student_headers,
    )
    assert event_resp.status_code == 201
    event_data = event_resp.json()
    assert event_data["title"] == "Distributed Systems Group Discussion"
    event_id = event_data["id"]

    # 7. Add an Assignment to the course with due date in the near future
    assignment_due = now + timedelta(days=4)
    assignment = Assignment(
        course_id=course.id,
        creator_id=lecturer_user.id,
        title="Project 1: Fault Tolerant KV Store",
        description="Design and test KV store under network partitions",
        due_date=assignment_due,
        max_marks=100.0,
        status="published",
    )
    test_session.add(assignment)
    await test_session.commit()

    # 8. Query Unified Calendar Events Feed
    cal_feed_resp = await client.get("/api/calendar/events", headers=student_headers)
    assert cal_feed_resp.status_code == 200
    cal_events = cal_feed_resp.json()
    assert len(cal_events) >= 2
    # Check personal event is in the feed
    assert any(e["title"] == "Distributed Systems Group Discussion" for e in cal_events)
    # Check system-generated assignment deadline is in the feed
    assert any("Project 1: Fault Tolerant KV Store" in e["title"] and e["event_type"] == "assignment_due" for e in cal_events)

    # 9. Clean up / update
    upd_ev = await client.put(
        f"/api/calendar/events/{event_id}",
        json={"title": "Distributed Systems Final Review"},
        headers=student_headers,
    )
    assert upd_ev.status_code == 200
    assert upd_ev.json()["title"] == "Distributed Systems Final Review"

    del_ev = await client.delete(f"/api/calendar/events/{event_id}", headers=student_headers)
    assert del_ev.status_code == 204

    del_task = await client.delete(f"/api/tasks/{task_id}", headers=student_headers)
    assert del_task.status_code == 204
