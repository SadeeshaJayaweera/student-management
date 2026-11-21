import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course, CourseModule, CourseLesson, Student, Enrollment
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_rich_learning_content_authoring_and_sanitization(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin & Student users
    admin_user = User(
        email="author_admin@nsbm.ac.lk",
        username="author_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Content Author",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)
    await test_session.commit()
    await test_session.refresh(admin_user)

    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create Course, Module, and Lesson
    c_res = await client.post(
        "/api/courses",
        headers=admin_headers,
        json={
            "course_code": "SE305",
            "title": "Software Architecture and Design Patterns",
            "credits": 3,
            "semester": 1,
            "year": 3,
            "max_students": 60
        }
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    m_res = await client.post(
        f"/api/courses/{course_id}/modules",
        headers=admin_headers,
        json={
            "order_index": 1,
            "title": "Module 1: Microservices & Event-Driven Architecture",
            "estimated_hours": 10.0,
            "status": "published"
        }
    )
    assert m_res.status_code == 201
    module_id = m_res.json()["id"]

    l_res = await client.post(
        f"/api/modules/{module_id}/lessons",
        headers=admin_headers,
        json={
            "title": "Lesson 1: Saga Pattern Implementation",
            "lesson_type": "reading",
            "estimated_minutes": 25,
            "order_index": 1,
            "is_required": True,
            "is_published": True
        }
    )
    assert l_res.status_code == 201
    lesson_id = l_res.json()["id"]

    # 3. Author Initial Rich Content (v1) with Anti-XSS Sanitization
    malicious_payload = (
        "# Saga Pattern in Microservices\n\n"
        "The Saga pattern provides transaction management across distributed services.\n"
        "<script>alert('XSS Exploit')</script>\n"
        "<img src='valid.png' onerror='alert(\"XSS2\")' alt='Architecture Diagram' />\n"
        "```python\ndef execute_saga():\n    pass\n```"
    )
    v1_res = await client.post(
        f"/api/lessons/{lesson_id}/content",
        headers=admin_headers,
        json={
            "raw_content": malicious_payload,
            "content_format": "markdown",
            "widget_configs": {"interactive_quiz": False, "code_runner": True},
            "change_summary": "Initial draft of Saga pattern lecture"
        }
    )
    assert v1_res.status_code == 201
    v1_data = v1_res.json()
    assert v1_data["version_number"] == 1
    assert v1_data["is_current"] is True
    # Verify malicious script tag and inline onerror are stripped out
    assert "<script>" not in v1_data["rendered_content"]
    assert "alert(" not in v1_data["rendered_content"]
    assert "onerror=" not in v1_data["rendered_content"]
    # Verify legitimate markdown was preserved
    assert "# Saga Pattern in Microservices" in v1_data["rendered_content"]

    # 4. Author Update (v2)
    v2_content = (
        "# Saga Pattern in Microservices (Updated)\n\n"
        "Coordinating transactions using Orchestration and Choreography approaches."
    )
    v2_res = await client.post(
        f"/api/lessons/{lesson_id}/content",
        headers=admin_headers,
        json={
            "raw_content": v2_content,
            "content_format": "markdown",
            "change_summary": "Added orchestration vs choreography details"
        }
    )
    assert v2_res.status_code == 201
    v2_data = v2_res.json()
    assert v2_data["version_number"] == 2
    assert v2_data["is_current"] is True

    # 5. Check Version History List
    history_res = await client.get(
        f"/api/lessons/{lesson_id}/content/versions",
        headers=admin_headers
    )
    assert history_res.status_code == 200
    versions = history_res.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2
    assert versions[0]["is_current"] is True
    assert versions[1]["version_number"] == 1
    assert versions[1]["is_current"] is False

    # 6. Rollback to v1
    rollback_res = await client.post(
        f"/api/lessons/{lesson_id}/content/rollback/1",
        headers=admin_headers
    )
    assert rollback_res.status_code == 200
    v3_data = rollback_res.json()
    assert v3_data["version_number"] == 3
    assert v3_data["is_current"] is True
    assert "Rollback to version 1" in v3_data["change_summary"]

    # Verify active content now reflects restored v1
    current_res = await client.get(
        f"/api/lessons/{lesson_id}/content",
        headers=admin_headers
    )
    assert current_res.status_code == 200
    current_data = current_res.json()
    assert current_data["version_number"] == 3
    assert "# Saga Pattern in Microservices" in current_data["rendered_content"]

    # 7. Student RBAC Enforcement
    student_user = User(
        email="student_se305@nsbm.ac.lk",
        username="student_se305",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Enrolled Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)
    await test_session.commit()
    await test_session.refresh(student_user)

    student = Student(
        user_id=student_user.id,
        student_id="STU-SE305",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        academic_standing="good_standing"
    )
    test_session.add(student)
    await test_session.commit()

    student_token = create_access_token({"sub": str(student_user.id), "role": student_user.role.value})
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Student can read current content
    stu_get = await client.get(f"/api/lessons/{lesson_id}/content", headers=student_headers)
    assert stu_get.status_code == 200

    # Student cannot author content
    stu_author = await client.post(
        f"/api/lessons/{lesson_id}/content",
        headers=student_headers,
        json={"raw_content": "Hacked content", "content_format": "markdown"}
    )
    assert stu_author.status_code == 403

    # Student cannot view revision history
    stu_hist = await client.get(
        f"/api/lessons/{lesson_id}/content/versions",
        headers=student_headers
    )
    assert stu_hist.status_code == 403

    # Student cannot rollback
    stu_rollback = await client.post(
        f"/api/lessons/{lesson_id}/content/rollback/1",
        headers=student_headers
    )
    assert stu_rollback.status_code == 403
