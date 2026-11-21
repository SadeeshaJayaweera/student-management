import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, Lecturer, Course, Enrollment
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_messaging_and_communication_workflows(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student User, Lecturer User, and External User
    student_user = User(
        email="msg_student@nsbm.ac.lk",
        username="msg_student",
        hashed_password=hash_password("Pass123!"),
        full_name="Samantha Perera",
        role=UserRole.STUDENT,
        is_active=True,
    )
    lecturer_user = User(
        email="msg_lecturer@nsbm.ac.lk",
        username="msg_lecturer",
        hashed_password=hash_password("Pass123!"),
        full_name="Dr. Kamal Silva",
        role=UserRole.LECTURER,
        is_active=True,
    )
    other_user = User(
        email="msg_other@nsbm.ac.lk",
        username="msg_other",
        hashed_password=hash_password("Pass123!"),
        full_name="Nimal Fernando",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([student_user, lecturer_user, other_user])
    await test_session.commit()

    student_profile = Student(
        user_id=student_user.id,
        student_id="STU-MSG-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=2,
        semester=1,
        gpa=3.75,
        credits_earned=60,
    )
    lecturer_profile = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-MSG-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add_all([student_profile, lecturer_profile])
    await test_session.commit()

    course = Course(
        course_code="CS204",
        title="Data Structures and Algorithms",
        faculty="Computing",
        department="Computer Science",
        credits=4,
        description="Core algorithms",
        semester=1,
        year=2,
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
    other_token = create_access_token({"sub": str(other_user.id), "role": "student"})

    student_headers = {"Authorization": f"Bearer {student_token}"}
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # 2. Test Contact Directory
    contacts_res = await client.get("/api/messaging/contacts", headers=student_headers)
    assert contacts_res.status_code == 200
    contacts_data = contacts_res.json()
    assert len(contacts_data) >= 1
    # Check that lecturer is in contacts
    lecturer_in_contacts = any(c["user_id"] == lecturer_user.id for c in contacts_data)
    assert lecturer_in_contacts is True

    # 3. Prevent Self-Messaging
    self_res = await client.post(
        "/api/messaging/conversations",
        headers=student_headers,
        json={
            "recipient_id": student_user.id,
            "subject": "Self note",
            "thread_type": "direct",
            "initial_message": "Talking to myself",
        },
    )
    assert self_res.status_code == 400

    # 4. Create Conversation (Student to Lecturer)
    conv_create_res = await client.post(
        "/api/messaging/conversations",
        headers=student_headers,
        json={
            "recipient_id": lecturer_user.id,
            "subject": "Inquiry regarding Assignment 1",
            "thread_type": "course_inquiry",
            "course_id": course.id,
            "initial_message": "Dear Dr. Kamal, could you please clarify question 3?",
            "attachment_url": "https://cdn.nsbm.ac.lk/docs/clarification.pdf",
            "attachment_name": "clarification.pdf",
        },
    )
    assert conv_create_res.status_code == 201
    conv_data = conv_create_res.json()
    conv_id = conv_data["id"]
    assert conv_data["subject"] == "Inquiry regarding Assignment 1"
    assert conv_data["course_code"] == "CS204"
    assert len(conv_data["messages"]) == 1
    assert conv_data["messages"][0]["content"] == "Dear Dr. Kamal, could you please clarify question 3?"
    assert conv_data["messages"][0]["attachment_name"] == "clarification.pdf"

    # 5. Check Lecturer's Unread Count
    unread_res = await client.get("/api/messaging/unread-count", headers=lecturer_headers)
    assert unread_res.status_code == 200
    assert unread_res.json()["unread_count"] >= 1

    # 6. Lecturer lists conversations
    list_res = await client.get("/api/messaging/conversations", headers=lecturer_headers)
    assert list_res.status_code == 200
    list_items = list_res.json()
    assert any(c["id"] == conv_id for c in list_items)
    target_c = next(c for c in list_items if c["id"] == conv_id)
    assert target_c["unread_count"] == 1
    assert "clarify question 3" in target_c["latest_message_snippet"]

    # 7. Lecturer views conversation (auto-marks read)
    detail_res = await client.get(f"/api/messaging/conversations/{conv_id}", headers=lecturer_headers)
    assert detail_res.status_code == 200
    assert len(detail_res.json()["messages"]) == 1

    # Check unread count is now 0 for lecturer
    unread_res_after = await client.get("/api/messaging/unread-count", headers=lecturer_headers)
    assert unread_res_after.status_code == 200
    assert unread_res_after.json()["unread_count"] == 0

    # 8. Lecturer replies to Student
    reply_res = await client.post(
        f"/api/messaging/conversations/{conv_id}/messages",
        headers=lecturer_headers,
        json={
            "content": "Hello Samantha, in question 3, assume a directed acyclic graph.",
        },
    )
    assert reply_res.status_code == 201
    reply_data = reply_res.json()
    assert reply_data["sender_id"] == lecturer_user.id
    assert "directed acyclic graph" in reply_data["content"]

    # 9. Student checks unread count and marks conversation as read explicitly
    student_unread = await client.get("/api/messaging/unread-count", headers=student_headers)
    assert student_unread.json()["unread_count"] >= 1

    mark_read_res = await client.post(f"/api/messaging/conversations/{conv_id}/read", headers=student_headers)
    assert mark_read_res.status_code == 200
    assert mark_read_res.json()["success"] is True

    student_unread_after = await client.get("/api/messaging/unread-count", headers=student_headers)
    assert student_unread_after.json()["unread_count"] == 0

    # 10. Third party unauthorized access is forbidden (403)
    unauthorized_res = await client.get(f"/api/messaging/conversations/{conv_id}", headers=other_headers)
    assert unauthorized_res.status_code == 403

    unauthorized_send = await client.post(
        f"/api/messaging/conversations/{conv_id}/messages",
        headers=other_headers,
        json={"content": "Eavesdropping"},
    )
    assert unauthorized_send.status_code == 403
