from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, Lecturer, Course, Enrollment,
    CourseEvaluationSurvey, SurveyQuestion, SurveyResponse, SurveyAnswer
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_student_feedback_and_course_evaluations_workflow(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student, Non-enrolled Student, and Lecturer
    student_user = User(
        email="eval_student@nsbm.ac.lk",
        username="eval_student",
        hashed_password=hash_password("Pass123!"),
        full_name="Dilshan Silva",
        role=UserRole.STUDENT,
        is_active=True,
    )
    other_student_user = User(
        email="eval_other@nsbm.ac.lk",
        username="eval_other",
        hashed_password=hash_password("Pass123!"),
        full_name="Niroshan Dias",
        role=UserRole.STUDENT,
        is_active=True,
    )
    lecturer_user = User(
        email="eval_lecturer@nsbm.ac.lk",
        username="eval_lecturer",
        hashed_password=hash_password("Pass123!"),
        full_name="Prof. Sunethra Jayasinghe",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add_all([student_user, other_student_user, lecturer_user])
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-EVL-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=2,
        gpa=3.85,
        credits_earned=90,
    )
    other_student = Student(
        user_id=other_student_user.id,
        student_id="STU-EVL-02",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=1,
        semester=1,
        gpa=3.2,
        credits_earned=15,
    )
    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-EVL-01",
        faculty="Computing",
        department="Software Engineering",
    )
    test_session.add_all([student, other_student, lecturer])
    await test_session.commit()

    course = Course(
        course_code="SE308",
        title="Enterprise Architecture and Cloud Systems",
        credits=4,
        faculty="Computing",
        department="Software Engineering",
        semester=2,
        year=3,
        lecturer_id=lecturer.id,
    )
    test_session.add(course)
    await test_session.commit()

    # Enroll only student 1
    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        status="active",
    )
    test_session.add(enrollment)
    await test_session.commit()

    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    other_token = create_access_token({"sub": str(other_student_user.id), "role": "student"})
    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": "lecturer"})

    student_headers = {"Authorization": f"Bearer {student_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}

    # 2. Lecturer creates evaluation survey
    now = datetime.utcnow()
    create_res = await client.post(
        "/api/evaluations/surveys",
        headers=lecturer_headers,
        json={
            "course_id": course.id,
            "title": "Semester 2 Module Feedback",
            "description": "Please evaluate course delivery and lecture effectiveness.",
            "start_date": (now - timedelta(days=1)).isoformat(),
            "end_date": (now + timedelta(days=14)).isoformat(),
            "is_published": True,
            "is_anonymous": True,
        },
    )
    assert create_res.status_code == 201
    survey_data = create_res.json()
    survey_id = survey_data["id"]
    assert survey_data["course_code"] == "SE308"
    assert survey_data["questions_count"] >= 5

    # 3. Student views pending evaluations
    pending_res = await client.get("/api/evaluations/student/pending", headers=student_headers)
    assert pending_res.status_code == 200
    pending_list = pending_res.json()
    assert len(pending_list) == 1
    assert pending_list[0]["id"] == survey_id
    assert pending_list[0]["has_submitted"] is False

    # 4. Student views survey detail questionnaire
    detail_res = await client.get(f"/api/evaluations/surveys/{survey_id}", headers=student_headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    questions = detail_data["questions"]
    assert len(questions) >= 5
    rating_q = next(q for q in questions if q["question_type"].startswith("rating"))
    text_q = next(q for q in questions if q["question_type"] == "text")

    # 5. Non-enrolled student attempts to evaluate course -> 403 Forbidden
    other_submit_res = await client.post(
        f"/api/evaluations/surveys/{survey_id}/submit",
        headers=other_headers,
        json={
            "answers": [
                {"question_id": rating_q["id"], "numeric_rating": 5.0},
            ]
        },
    )
    assert other_submit_res.status_code == 403

    # 6. Enrolled student submits valid anonymous evaluation
    submit_res = await client.post(
        f"/api/evaluations/surveys/{survey_id}/submit",
        headers=student_headers,
        json={
            "answers": [
                {"question_id": rating_q["id"], "numeric_rating": 5.0},
                {"question_id": text_q["id"], "text_response": "Excellent depth on microservices and cloud design."},
            ]
        },
    )
    assert submit_res.status_code == 201
    assert submit_res.json()["status"] == "submitted"

    # 7. Duplicate submission prevented
    dup_res = await client.post(
        f"/api/evaluations/surveys/{survey_id}/submit",
        headers=student_headers,
        json={
            "answers": [
                {"question_id": rating_q["id"], "numeric_rating": 4.0},
            ]
        },
    )
    assert dup_res.status_code == 400
    assert "already submitted" in dup_res.json()["detail"]

    # 8. Pending evaluations now reflects completed status
    pending_after = await client.get("/api/evaluations/student/pending", headers=student_headers)
    assert pending_after.status_code == 200
    assert pending_after.json()[0]["has_submitted"] is True

    # 9. Faculty retrieves survey analytics
    analytics_res = await client.get(f"/api/evaluations/surveys/{survey_id}/analytics", headers=lecturer_headers)
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["total_responses"] == 1
    assert analytics_data["course_code"] == "SE308"
    assert analytics_data["overall_average"] is not None
    # Check text comment is aggregated
    found_comment = False
    for qa in analytics_data["question_analytics"]:
        if "microservices" in " ".join(qa["text_feedback"]):
            found_comment = True
            break
    assert found_comment is True
