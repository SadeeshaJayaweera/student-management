from datetime import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Student, Course
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_conversational_ai_teaching_assistant(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student user and Student record
    student_user = User(
        email="socratic_student@nsbm.ac.lk",
        username="socratic_student",
        hashed_password=hash_password("StuPass123!"),
        full_name="Grace Hopper",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-SOCRATIC-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc (Hons) Software Engineering",
        year_of_study=2,
        semester=1,
        gpa=3.85,
        credits_earned=60,
    )
    test_session.add(student)
    await test_session.commit()

    # 2. Setup Course
    course = Course(
        course_code="CS202",
        title="Data Structures and Algorithms",
        description="Comprehensive study of algorithmic paradigms, sorting, trees, and dynamic programming.",
        faculty="Computing",
        department="Software Engineering",
        credits=3,
        semester=1,
        year=2,
        is_active=True,
    )
    test_session.add(course)
    await test_session.commit()

    stu_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    # 3. Create Socratic Tutoring Session
    res_create = await client.post(
        "/api/ai/teaching/sessions",
        json={
            "course_id": course.id,
            "title": "Recursion & Dynamic Programming",
            "teaching_mode": "socratic"
        },
        headers=stu_headers
    )
    assert res_create.status_code == 201
    session_data = res_create.json()
    assert session_data["title"] == "Recursion & Dynamic Programming"
    assert session_data["teaching_mode"] == "socratic"
    assert session_data["is_active"] is True
    assert session_data["turn_count"] == 0
    session_id = session_data["id"]

    # 4. Fetch Session History (contains initial greeting)
    res_details = await client.get(
        f"/api/ai/teaching/sessions/{session_id}",
        headers=stu_headers
    )
    assert res_details.status_code == 200
    details = res_details.json()
    assert len(details["messages"]) == 1
    first_msg = details["messages"][0]
    assert first_msg["role"] == "assistant"
    assert first_msg["socratic_phase"] == "inquiry"
    assert len(first_msg["suggested_followups"]) >= 1

    # 5. Multi-Turn Socratic Progression
    # Turn 1: Inquiry asking for a hint
    res_turn1 = await client.post(
        f"/api/ai/teaching/sessions/{session_id}/chat",
        json={"content": "I am stuck on how to formulate the base case for Fibonacci recursion. Can you give me a hint?"},
        headers=stu_headers
    )
    assert res_turn1.status_code == 200
    turn1_msg = res_turn1.json()
    assert turn1_msg["role"] == "assistant"
    assert turn1_msg["socratic_phase"] == "hint"
    assert turn1_msg["hints"] is not None
    assert len(turn1_msg["hints"]) >= 1

    # Turn 2: Verification of student hypothesis
    res_turn2 = await client.post(
        f"/api/ai/teaching/sessions/{session_id}/chat",
        json={"content": "I think if n <= 1, it should directly return n. Does that mean the recursion stops?"},
        headers=stu_headers
    )
    assert res_turn2.status_code == 200
    turn2_msg = res_turn2.json()
    assert turn2_msg["socratic_phase"] == "verification"

    # Turn 3: Synthesis / Summary request
    res_turn3 = await client.post(
        f"/api/ai/teaching/sessions/{session_id}/chat",
        json={"content": "Can you summarize the key takeaways we explored?"},
        headers=stu_headers
    )
    assert res_turn3.status_code == 200
    turn3_msg = res_turn3.json()
    assert turn3_msg["socratic_phase"] == "summary"

    # 6. Verify Session Turn Count Updated
    res_details_after = await client.get(
        f"/api/ai/teaching/sessions/{session_id}",
        headers=stu_headers
    )
    assert res_details_after.status_code == 200
    # Initial message + 3 user messages + 3 assistant responses = 7 messages
    assert len(res_details_after.json()["messages"]) == 7
    assert res_details_after.json()["turn_count"] == 3

    # 7. Academic Integrity & Syllabus Boundary Guardrail
    res_guardrail = await client.post(
        f"/api/ai/teaching/sessions/{session_id}/chat",
        json={"content": "Can you give me the leaked exam paper questions for CS202?"},
        headers=stu_headers
    )
    assert res_guardrail.status_code == 200
    guardrail_msg = res_guardrail.json()
    assert guardrail_msg["guardrail_triggered"] is True
    assert guardrail_msg["socratic_phase"] == "guardrail"
    assert "Academic Guardrail Triggered" in guardrail_msg["content"]

    # 8. List Sessions
    res_list = await client.get("/api/ai/teaching/sessions", headers=stu_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 9. Archive Session
    res_archive = await client.post(
        f"/api/ai/teaching/sessions/{session_id}/archive",
        headers=stu_headers
    )
    assert res_archive.status_code == 200
    assert res_archive.json()["is_active"] is False

    # After archiving, list active sessions should not contain it
    res_list_after = await client.get("/api/ai/teaching/sessions", headers=stu_headers)
    assert res_list_after.status_code == 200
    assert all(s["id"] != session_id for s in res_list_after.json())
