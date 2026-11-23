from datetime import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_ai_quiz_and_question_generation(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Lecturer and Student users
    lecturer_user = User(
        email="quiz_prof@nsbm.ac.lk",
        username="quiz_prof",
        hashed_password=hash_password("ProfPass123!"),
        full_name="Prof. Barbara Liskov",
        role=UserRole.LECTURER,
        is_active=True,
    )
    student_user = User(
        email="quiz_student@nsbm.ac.lk",
        username="quiz_student",
        hashed_password=hash_password("StuPass123!"),
        full_name="Linus Torvalds",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([lecturer_user, student_user])
    await test_session.commit()

    # 2. Setup Course
    course = Course(
        course_code="CS305",
        title="Software Architecture & Design Patterns",
        description="Object-oriented architecture, SOLID principles, creational, structural, and behavioral patterns.",
        faculty="Computing",
        department="Software Engineering",
        credits=3,
        semester=1,
        year=3,
        is_active=True,
    )
    test_session.add(course)
    await test_session.commit()

    lec_token = create_access_token({"sub": str(lecturer_user.id), "role": "lecturer"})
    lec_headers = {"Authorization": f"Bearer {lec_token}"}
    stu_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    sample_lecture_notes = (
        "The Liskov Substitution Principle (LSP) asserts that objects of a superclass should be replaceable "
        "with objects of its subclasses without breaking application correctness. "
        "Preconditions cannot be strengthened in a subtype, and postconditions cannot be weakened. "
        "In concurrency, immutable state eliminates race conditions by guaranteeing thread safety without mutex contention. "
        "Factory patterns encapsulate object creation logic, decoupling clients from concrete classes."
    )

    # 3. RBAC Check: Student cannot generate quiz questions
    res_forbidden = await client.post(
        "/api/ai/quiz-generation/generate",
        json={
            "course_id": course.id,
            "title": "Unauthorized Generation",
            "source_text": sample_lecture_notes,
            "question_count": 3
        },
        headers=stu_headers
    )
    assert res_forbidden.status_code == 403

    # 4. Lecturer generates questions with Bloom's level 'analyze' and 'hard' difficulty
    res_gen = await client.post(
        "/api/ai/quiz-generation/generate",
        json={
            "course_id": course.id,
            "title": "LSP & Architectural Principles Assessment",
            "source_text": sample_lecture_notes,
            "blooms_level": "analyze",
            "difficulty": "hard",
            "question_count": 3,
            "question_types": ["multiple_choice", "code_analysis", "short_answer"]
        },
        headers=lec_headers
    )
    assert res_gen.status_code == 201
    job_data = res_gen.json()
    assert job_data["title"] == "LSP & Architectural Principles Assessment"
    assert job_data["blooms_level"] == "analyze"
    assert job_data["difficulty"] == "hard"
    assert len(job_data["questions"]) == 3
    job_id = job_data["id"]

    # Verify MCQ item structure
    mcq_q = next(q for q in job_data["questions"] if q["question_type"] == "multiple_choice")
    assert mcq_q["options"] is not None
    assert len(mcq_q["options"]) == 4
    assert mcq_q["correct_answer"] == "A"
    assert "distractor" in mcq_q["explanation"].lower()

    # Verify Code Analysis item structure
    code_q = next(q for q in job_data["questions"] if q["question_type"] == "code_analysis")
    assert "```python" in code_q["prompt"]
    assert code_q["rubric_guide"] is not None
    assert "criteria" in code_q["rubric_guide"]

    # 5. Fetch Generation Job Details
    res_details = await client.get(
        f"/api/ai/quiz-generation/jobs/{job_id}",
        headers=lec_headers
    )
    assert res_details.status_code == 200
    assert len(res_details.json()["questions"]) == 3

    # 6. Approve and Export an Individual Question to Question Bank
    res_approve = await client.post(
        f"/api/ai/quiz-generation/questions/{mcq_q['id']}/approve",
        headers=lec_headers
    )
    assert res_approve.status_code == 200
    approve_data = res_approve.json()
    assert approve_data["status"] == "approved_and_exported"
    assert approve_data["question_bank_item_id"] is not None

    # 7. Publish Entire Job as a Live Student-Facing Quiz
    res_publish = await client.post(
        f"/api/ai/quiz-generation/jobs/{job_id}/publish-quiz",
        json={
            "title": "Live Quiz: Software Architecture & LSP",
            "time_limit_minutes": 45
        },
        headers=lec_headers
    )
    assert res_publish.status_code == 200
    publish_data = res_publish.json()
    assert publish_data["title"] == "Live Quiz: Software Architecture & LSP"
    assert publish_data["status"] == "published"
    assert publish_data["questions_count"] == 3
    assert publish_data["quiz_id"] is not None
