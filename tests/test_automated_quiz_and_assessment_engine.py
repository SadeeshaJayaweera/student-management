from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    QuestionBankItem, Quiz, QuizQuestion, QuizAttempt
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_automated_quiz_and_assessment_engine_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Enrolled Student, Outsider Student
    admin_user = User(
        email="quiz_admin@nsbm.ac.lk",
        username="quiz_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Exam Controller",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="quiz_lecturer@nsbm.ac.lk",
        username="quiz_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Claude Shannon",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_user = User(
        email="quiz_student@nsbm.ac.lk",
        username="quiz_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="John von Neumann",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)

    outsider_user = User(
        email="quiz_outsider@nsbm.ac.lk",
        username="quiz_outsider",
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
        lecturer_id="LEC-QZ-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add(lecturer)

    student = Student(
        user_id=student_user.id,
        student_id="STU-QZ-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=2,
        semester=2,
    )
    test_session.add(student)

    outsider = Student(
        user_id=outsider_user.id,
        student_id="STU-QZ-02",
        faculty="Business",
        department="Finance",
        program="BSc Finance",
        year_of_study=1,
        semester=1,
    )
    test_session.add(outsider)
    await test_session.commit()

    # Course
    course = Course(
        course_code="CS210",
        title="Information Theory & Automata",
        description="Entropy, formal grammars, and Turing machines.",
        credits=4,
        faculty="Computing",
        department="Computer Science",
        semester=2,
        year=2,
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

    # 3. Questions in Question Bank
    q1 = QuestionBankItem(
        course_id=course.id,
        creator_id=lecturer_user.id,
        title="Shannon Entropy Definition",
        prompt="Who introduced the fundamental concept of information entropy in 1948?",
        question_type="single_choice",
        difficulty_level="beginner",
        default_points=2.0,
        options=[
            {"id": "opt_a", "text": "Alan Turing", "is_correct": False},
            {"id": "opt_b", "text": "Claude Shannon", "is_correct": True},
            {"id": "opt_c", "text": "John von Neumann", "is_correct": False},
        ],
        explanation="Claude Shannon introduced information entropy in 'A Mathematical Theory of Communication'.",
    )
    test_session.add(q1)

    q2 = QuestionBankItem(
        course_id=course.id,
        creator_id=lecturer_user.id,
        title="Binary Channel Capacity",
        prompt="What is the maximum channel capacity (in bits/symbol) of a noiseless binary symmetric channel?",
        question_type="numerical",
        difficulty_level="intermediate",
        default_points=3.0,
        answer_key={"target_value": 1.0, "tolerance": 0.05},
        explanation="For a noiseless binary channel, capacity is 1 bit per transmission.",
    )
    test_session.add(q2)

    q3 = QuestionBankItem(
        course_id=course.id,
        creator_id=lecturer_user.id,
        title="Turing Machine Halting Decidability",
        prompt="The general halting problem for Turing machines is undecidable.",
        question_type="true_false",
        difficulty_level="intermediate",
        default_points=1.0,
        options=[
            {"id": "opt_true", "text": "True", "is_correct": True},
            {"id": "opt_false", "text": "False", "is_correct": False},
        ],
        explanation="Alan Turing proved that no algorithm can decide halting for arbitrary machines.",
    )
    test_session.add(q3)
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

    # 4. Lecturer creates Quiz
    now = datetime.utcnow()
    quiz_payload = {
        "title": "Automata & Information Theory Midterm Quiz",
        "description": "Deterministic assessment on Shannon entropy and Turing decidability.",
        "time_limit_minutes": 30,
        "passing_score_percentage": 60.0,
        "max_attempts": 2,
        "shuffle_questions": True,
        "shuffle_options": True,
        "show_correct_answers": True,
        "allow_backtracking": True,
        "status": "published",
        "available_from": (now - timedelta(days=1)).isoformat(),
        "due_date": (now + timedelta(days=7)).isoformat(),
    }
    r = await client.post(f"/api/courses/{course.id}/quizzes", json=quiz_payload, headers=lecturer_headers)
    assert r.status_code == 201
    quiz_data = r.json()
    quiz_id = quiz_data["id"]
    assert quiz_data["title"] == "Automata & Information Theory Midterm Quiz"
    assert quiz_data["passing_score_percentage"] == 60.0

    # 5. Add questions to quiz
    r = await client.post(f"/api/quizzes/{quiz_id}/questions", json={"question_item_id": q1.id, "points": 2.0}, headers=lecturer_headers)
    assert r.status_code == 201
    r = await client.post(f"/api/quizzes/{quiz_id}/questions", json={"question_item_id": q2.id, "points": 3.0}, headers=lecturer_headers)
    assert r.status_code == 201
    r = await client.post(f"/api/quizzes/{quiz_id}/questions", json={"question_item_id": q3.id, "points": 1.0}, headers=lecturer_headers)
    assert r.status_code == 201

    # Verify quiz total points updated to 6.0
    r = await client.get(f"/api/quizzes/{quiz_id}", headers=student_headers)
    assert r.status_code == 200
    assert r.json()["total_points"] == 6.0
    assert r.json()["questions_count"] == 3

    # 6. Outsider student cannot take quiz -> 403 Forbidden
    r = await client.post(f"/api/quizzes/{quiz_id}/start", headers=outsider_headers)
    assert r.status_code == 403

    # 7. Enrolled student starts Attempt 1
    r = await client.post(f"/api/quizzes/{quiz_id}/start", headers=student_headers)
    assert r.status_code == 201
    start_data = r.json()
    attempt_id = start_data["attempt_id"]
    assert start_data["attempt_number"] == 1
    assert len(start_data["questions"]) == 3
    # Check that answers are stripped from student view
    for sq in start_data["questions"]:
        if sq["options"]:
            for opt in sq["options"]:
                assert "is_correct" not in opt

    # 8. Student autosaves intermediate answers
    autosave_payload = {
        "answers": [
            {"question_id": q1.id, "selected_option_ids": ["opt_b"]},
            {"question_id": q2.id, "numerical_answer": 1.02}
        ]
    }
    r = await client.post(f"/api/quizzes/{quiz_id}/attempts/{attempt_id}/autosave", json=autosave_payload, headers=student_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "autosaved"

    # 9. Student submits completed attempt
    # Q1: opt_b (Correct -> 2.0)
    # Q2: 1.02 (Within tolerance 0.05 of 1.0 -> 3.0)
    # Q3: opt_false (Wrong -> 0.0)
    # Total = 5.0 / 6.0 = 83.33% -> Passed
    submit_payload = {
        "answers": [
            {"question_id": q1.id, "selected_option_ids": ["opt_b"]},
            {"question_id": q2.id, "numerical_answer": 1.02},
            {"question_id": q3.id, "selected_option_ids": ["opt_false"]}
        ]
    }
    r = await client.post(f"/api/quizzes/{quiz_id}/attempts/{attempt_id}/submit", json=submit_payload, headers=student_headers)
    assert r.status_code == 200
    graded = r.json()
    assert graded["id"] == attempt_id
    assert graded["total_score"] == 5.0
    assert graded["max_score"] == 6.0
    assert graded["percentage"] == 83.33
    assert graded["is_passed"] is True
    assert graded["status"] == "graded"

    # 10. Student starts Attempt 2
    r = await client.post(f"/api/quizzes/{quiz_id}/start", headers=student_headers)
    assert r.status_code == 201
    start_data_2 = r.json()
    attempt_2_id = start_data_2["attempt_id"]
    assert start_data_2["attempt_number"] == 2

    # Submit Attempt 2 with wrong answers
    submit_payload_2 = {
        "answers": [
            {"question_id": q1.id, "selected_option_ids": ["opt_a"]},
            {"question_id": q2.id, "numerical_answer": 50.0},
            {"question_id": q3.id, "selected_option_ids": ["opt_false"]}
        ]
    }
    r = await client.post(f"/api/quizzes/{quiz_id}/attempts/{attempt_2_id}/submit", json=submit_payload_2, headers=student_headers)
    assert r.status_code == 200
    graded_2 = r.json()
    assert graded_2["total_score"] == 0.0
    assert graded_2["percentage"] == 0.0
    assert graded_2["is_passed"] is False

    # 11. Student attempts 3rd attempt -> 400 Bad Request (exceeds max_attempts=2)
    r = await client.post(f"/api/quizzes/{quiz_id}/start", headers=student_headers)
    assert r.status_code == 400
    assert "Maximum attempt limit (2) reached" in r.json()["detail"]

    # 12. Instructor lists all attempts for the quiz
    r = await client.get(f"/api/quizzes/{quiz_id}/attempts", headers=lecturer_headers)
    assert r.status_code == 200
    all_attempts = r.json()
    assert len(all_attempts) == 2
