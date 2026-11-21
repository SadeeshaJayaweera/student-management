from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    Assignment, AssignmentSubmission, AssignmentStatus
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_rubric_based_assessment_engine_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Enrolled Student, Outsider Student
    admin_user = User(
        email="rubric_admin@nsbm.ac.lk",
        username="rubric_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Assessment Dean",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="rubric_lecturer@nsbm.ac.lk",
        username="rubric_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Dr. Alan Turing",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_user = User(
        email="rubric_student@nsbm.ac.lk",
        username="rubric_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Ada Lovelace",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)

    outsider_user = User(
        email="rubric_outsider@nsbm.ac.lk",
        username="rubric_outsider",
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
        lecturer_id="LEC-RUB-01",
        faculty="Computing",
        department="Software Engineering",
    )
    test_session.add(lecturer)

    student = Student(
        user_id=student_user.id,
        student_id="STU-RUB-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=2,
        semester=2,
    )
    test_session.add(student)

    outsider = Student(
        user_id=outsider_user.id,
        student_id="STU-RUB-02",
        faculty="Management",
        department="Logistics",
        program="BSc Logistics",
        year_of_study=1,
        semester=1,
    )
    test_session.add(outsider)
    await test_session.commit()

    # Course
    course = Course(
        course_code="SE302",
        title="Enterprise Software Architecture",
        description="Scalable cloud architectures and quality engineering.",
        credits=4,
        faculty="Computing",
        department="Software Engineering",
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

    # Assignment
    now = datetime.utcnow()
    assignment = Assignment(
        course_id=course.id,
        creator_id=lecturer_user.id,
        title="Distributed Microservices Project",
        description="Implement event-driven microservices architecture.",
        due_date=now + timedelta(days=14),
        available_from=now - timedelta(days=1),
        max_marks=100.0,
        status="published",
    )
    test_session.add(assignment)
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

    # 2. Student cannot create a rubric -> 403 Forbidden
    rubric_payload = {
        "title": "SE302 Architecture Evaluation Rubric",
        "description": "Standardized multi-dimensional criteria for enterprise systems.",
        "scoring_strategy": "analytic",
        "is_template": False,
        "total_points": 100.0,
        "criteria": [
            {
                "title": "Architectural Design & Patterns",
                "description": "Proper application of clean architecture and isolation.",
                "max_points": 50.0,
                "weight": 1.0,
                "order_index": 0,
                "levels": [
                    {"title": "Exemplary", "description": "Flawless separation of concerns", "point_value": 50.0, "order_index": 0},
                    {"title": "Proficient", "description": "Good structure with minor leaks", "point_value": 35.0, "order_index": 1},
                    {"title": "Unsatisfactory", "description": "Monolithic tightly coupled code", "point_value": 15.0, "order_index": 2},
                ]
            },
            {
                "title": "Test Coverage & Resiliency",
                "description": "Comprehensive integration testing and chaos resilience.",
                "max_points": 50.0,
                "weight": 1.0,
                "order_index": 1,
                "levels": [
                    {"title": "Exemplary", "description": "Over 90% coverage with resilient retries", "point_value": 50.0, "order_index": 0},
                    {"title": "Proficient", "description": "Core flows tested", "point_value": 35.0, "order_index": 1},
                    {"title": "Unsatisfactory", "description": "Insufficient test cases", "point_value": 10.0, "order_index": 2},
                ]
            }
        ]
    }
    r = await client.post(f"/api/courses/{course.id}/rubrics", json=rubric_payload, headers=student_headers)
    assert r.status_code == 403

    # 3. Lecturer authors the rubric successfully
    r = await client.post(f"/api/courses/{course.id}/rubrics", json=rubric_payload, headers=lecturer_headers)
    assert r.status_code == 201
    rubric_data = r.json()
    rubric_id = rubric_data["id"]
    assert rubric_data["title"] == "SE302 Architecture Evaluation Rubric"
    assert rubric_data["total_points"] == 100.0
    assert len(rubric_data["criteria"]) == 2
    crit_1_id = rubric_data["criteria"][0]["id"]
    crit_2_id = rubric_data["criteria"][1]["id"]
    assert len(rubric_data["criteria"][0]["levels"]) == 3

    # 4. List course rubrics
    r = await client.get(f"/api/courses/{course.id}/rubrics", headers=lecturer_headers)
    assert r.status_code == 200
    course_rubrics = r.json()
    assert len(course_rubrics) >= 1
    assert any(rb["id"] == rubric_id for rb in course_rubrics)

    # 5. Retrieve specific rubric
    r = await client.get(f"/api/rubrics/{rubric_id}", headers=student_headers)
    assert r.status_code == 200
    assert r.json()["id"] == rubric_id

    # 6. Attach rubric to assignment
    r = await client.post(f"/api/assignments/{assignment.id}/rubric/{rubric_id}", headers=lecturer_headers)
    assert r.status_code == 200
    asg_updated = r.json()
    assert asg_updated["rubric_id"] == rubric_id
    assert asg_updated["grading_type"] == "rubric"
    assert asg_updated["max_marks"] == 100.0

    # 7. Create a student submission for grading
    submission = AssignmentSubmission(
        assignment_id=assignment.id,
        student_id=student.id,
        text_content="https://github.com/student/microservices-final",
        status=AssignmentStatus.SUBMITTED,
    )
    test_session.add(submission)
    await test_session.commit()

    # 8. Evaluation with score exceeding criterion max_points returns 400
    invalid_eval_payload = {
        "submission_id": submission.id,
        "feedback": "Invalid scoring attempt",
        "criteria_scores": [
            {"criterion_id": crit_1_id, "points": 60.0, "comment": "Exceeds max 50 points"}
        ]
    }
    r = await client.post(f"/api/assignments/{assignment.id}/rubric-evaluations", json=invalid_eval_payload, headers=lecturer_headers)
    assert r.status_code == 400
    assert "exceed maximum points" in r.json()["detail"]

    # 9. Lecturer submits legitimate rubric evaluation
    valid_eval_payload = {
        "submission_id": submission.id,
        "feedback": "Outstanding architectural separation and resilient message handling.",
        "criteria_scores": [
            {"criterion_id": crit_1_id, "points": 48.0, "comment": "Clean bounded contexts and domain events"},
            {"criterion_id": crit_2_id, "points": 45.0, "comment": "Robust circuit breakers and comprehensive suites"}
        ]
    }
    r = await client.post(f"/api/assignments/{assignment.id}/rubric-evaluations", json=valid_eval_payload, headers=lecturer_headers)
    assert r.status_code == 201
    eval_data = r.json()
    assert eval_data["rubric_id"] == rubric_id
    assert eval_data["total_score"] == 93.0
    assert eval_data["max_possible_score"] == 100.0
    assert eval_data["percentage"] == 93.0

    # 10. Verify submission is updated with marks and status
    await test_session.refresh(submission)
    assert submission.marks == 93.0
    assert submission.status == AssignmentStatus.GRADED

    # 11. Student retrieves own rubric evaluation
    r = await client.get(f"/api/assignments/{assignment.id}/rubric-evaluations/{submission.id}", headers=student_headers)
    assert r.status_code == 200
    student_eval = r.json()
    assert student_eval["total_score"] == 93.0
    assert len(student_eval["criteria_scores"]) == 2

    # 12. Outsider student cannot view the rubric evaluation -> 403 Forbidden
    r = await client.get(f"/api/assignments/{assignment.id}/rubric-evaluations/{submission.id}", headers=outsider_headers)
    assert r.status_code == 403

    # 13. Cannot delete rubric while evaluation exists -> 400 Bad Request
    r = await client.delete(f"/api/rubrics/{rubric_id}", headers=lecturer_headers)
    assert r.status_code == 400
    assert "Cannot delete rubric with" in r.json()["detail"]
