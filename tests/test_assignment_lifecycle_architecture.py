from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course, Student, Lecturer, Enrollment, Assignment
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_assignment_lifecycle_architecture(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Enrolled Student, and Unenrolled Student
    admin_user = User(
        email="assign_admin@nsbm.ac.lk",
        username="assign_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Assignment Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="assign_lecturer@nsbm.ac.lk",
        username="assign_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Donald Knuth",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_user = User(
        email="assign_student@nsbm.ac.lk",
        username="assign_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Grace Hopper",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)

    outsider_user = User(
        email="assign_outsider@nsbm.ac.lk",
        username="assign_outsider",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Outsider Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(outsider_user)
    await test_session.commit()

    # Profiles
    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-ASG-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add(lecturer)

    student = Student(
        user_id=student_user.id,
        student_id="STU-ASG-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=3,
        semester=1,
    )
    test_session.add(student)

    outsider = Student(
        user_id=outsider_user.id,
        student_id="STU-ASG-02",
        faculty="Business",
        department="Management",
        program="BSc Business Management",
        year_of_study=1,
        semester=1,
    )
    test_session.add(outsider)
    await test_session.commit()

    # Course
    course = Course(
        course_code="CS401",
        title="Advanced Algorithm Design & Analysis",
        description="Complexity, heuristics, and algorithmic paradigms.",
        credits=4,
        faculty="Computing",
        department="Computer Science",
        semester=1,
        year=3,
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

    # 2. Lecturer attempts to create an assignment with invalid availability dates (due <= available_from)
    now = datetime.utcnow()
    invalid_payload = {
        "course_id": course.id,
        "title": "Invalid Date Assignment",
        "due_date": (now + timedelta(days=1)).isoformat(),
        "available_from": (now + timedelta(days=2)).isoformat(),
        "max_marks": 100.0,
        "status": "draft",
    }
    r = await client.post(f"/api/courses/{course.id}/assignments", json=invalid_payload, headers=lecturer_headers)
    assert r.status_code == 400
    assert "due date must be after the available_from date" in r.json()["detail"]

    # 3. Student tries to create an assignment -> 403 Forbidden
    valid_draft_payload = {
        "course_id": course.id,
        "title": "Dynamic Programming Problem Set 1",
        "description": "Analyze and implement optimal memoized solutions.",
        "due_date": (now + timedelta(days=7)).isoformat(),
        "available_from": (now - timedelta(hours=1)).isoformat(),
        "cutoff_date": (now + timedelta(days=10)).isoformat(),
        "max_marks": 100.0,
        "weightage_percentage": 15.0,
        "assignment_type": "assignment",
        "grading_type": "points",
        "status": "draft",
        "allow_late_submissions": True,
        "late_penalty_percentage_per_day": 5.0,
        "submission_types": ["file", "text"],
        "allowed_file_extensions": [".pdf", ".py", ".zip"],
        "max_file_size_mb": 25,
        "max_attempts": 3,
        "anonymous_grading": True,
        "peer_review_enabled": False,
        "group_assignment": False,
    }
    r = await client.post(f"/api/courses/{course.id}/assignments", json=valid_draft_payload, headers=student_headers)
    assert r.status_code == 403

    # 4. Lecturer authors the draft assignment successfully
    r = await client.post(f"/api/courses/{course.id}/assignments", json=valid_draft_payload, headers=lecturer_headers)
    assert r.status_code == 201
    assignment_data = r.json()
    assignment_id = assignment_data["id"]
    assert assignment_data["title"] == "Dynamic Programming Problem Set 1"
    assert assignment_data["status"] == "draft"
    assert assignment_data["published_at"] is None
    assert assignment_data["anonymous_grading"] is True

    # 5. Student cannot access draft assignment directly -> 404
    r = await client.get(f"/api/assignments/{assignment_id}", headers=student_headers)
    assert r.status_code == 404

    # 6. Student listing course assignments does NOT include draft assignments
    r = await client.get(f"/api/courses/{course.id}/assignments", headers=student_headers)
    assert r.status_code == 200
    student_assignments = r.json()
    assert len(student_assignments) == 0

    # 7. Lecturer listing course assignments includes draft assignments
    r = await client.get(f"/api/courses/{course.id}/assignments", headers=lecturer_headers)
    assert r.status_code == 200
    lecturer_assignments = r.json()
    assert len(lecturer_assignments) == 1
    assert lecturer_assignments[0]["id"] == assignment_id

    # 8. Lecturer updates assignment parameters
    update_payload = {
        "title": "Dynamic Programming & Greedy Algorithms Problem Set 1",
        "weightage_percentage": 20.0,
    }
    r = await client.patch(f"/api/assignments/{assignment_id}", json=update_payload, headers=lecturer_headers)
    assert r.status_code == 200
    updated_data = r.json()
    assert updated_data["title"] == "Dynamic Programming & Greedy Algorithms Problem Set 1"
    assert updated_data["weightage_percentage"] == 20.0

    # 9. Lecturer publishes assignment via /publish endpoint
    r = await client.post(f"/api/assignments/{assignment_id}/publish", headers=lecturer_headers)
    assert r.status_code == 200
    pub_data = r.json()
    assert pub_data["status"] == "published"
    assert pub_data["published_at"] is not None

    # 10. Student now can view published assignment
    r = await client.get(f"/api/assignments/{assignment_id}", headers=student_headers)
    assert r.status_code == 200
    student_view = r.json()
    assert student_view["id"] == assignment_id
    assert student_view["is_available"] is True
    assert student_view["is_past_due"] is False
    assert student_view["is_past_cutoff"] is False

    # 11. Student listing course assignments now sees published assignment
    r = await client.get(f"/api/courses/{course.id}/assignments", headers=student_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1

    # 12. Unenrolled student tries to access assignment -> 403 Forbidden
    r = await client.get(f"/api/assignments/{assignment_id}", headers=outsider_headers)
    assert r.status_code == 403

    # 13. Lecturer closes the assignment
    r = await client.post(f"/api/assignments/{assignment_id}/close", headers=lecturer_headers)
    assert r.status_code == 200
    closed_data = r.json()
    assert closed_data["status"] == "closed"

    # 14. Lecturer deletes assignment (0 submissions) -> 204
    r = await client.delete(f"/api/assignments/{assignment_id}", headers=lecturer_headers)
    assert r.status_code == 204

    # Confirm assignment is gone
    r = await client.get(f"/api/assignments/{assignment_id}", headers=lecturer_headers)
    assert r.status_code == 404
