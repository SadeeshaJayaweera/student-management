"""
NSBM EduSphere — Course Workspace Architecture Tests
Validates unified course workspace retrieval, role-based contextual filtering,
syllabus and settings configuration, and strict enrollment authorization.
"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    User, UserRole, Institution, Course, CourseModule, Assignment,
    Student, Lecturer, Enrollment
)
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def workspace_infra_fixture(test_session: AsyncSession):
    """Sets up course with modules, assignments, instructor, enrolled student, and unenrolled student"""
    inst = Institution(name="NSBM University", code="NSBM-WS", is_active=True)
    test_session.add(inst)
    await test_session.commit()
    await test_session.refresh(inst)

    # Users
    admin_u = User(username="ws_admin", email="admin@nsbm.ac.lk", full_name="Workspace Admin", hashed_password=hash_password("Pass@123"), role=UserRole.ADMIN, institution_id=inst.id, is_active=True)
    lec_u = User(username="ws_lecturer", email="lec@nsbm.ac.lk", full_name="Dr. Alan Turing", hashed_password=hash_password("Pass@123"), role=UserRole.LECTURER, institution_id=inst.id, is_active=True)
    s_enrolled_u = User(username="ws_enrolled", email="enrolled@nsbm.ac.lk", full_name="Enrolled Student", hashed_password=hash_password("Pass@123"), role=UserRole.STUDENT, institution_id=inst.id, is_active=True)
    s_outsider_u = User(username="ws_outsider", email="outsider@nsbm.ac.lk", full_name="Outsider Student", hashed_password=hash_password("Pass@123"), role=UserRole.STUDENT, institution_id=inst.id, is_active=True)
    test_session.add_all([admin_u, lec_u, s_enrolled_u, s_outsider_u])
    await test_session.commit()
    for u in [admin_u, lec_u, s_enrolled_u, s_outsider_u]:
        await test_session.refresh(u)

    lec = Lecturer(
        user_id=lec_u.id,
        institution_id=inst.id,
        lecturer_id="LEC-WS-01",
        faculty="Computing",
        department="Software Engineering",
        office_location="Hall 3, Room 101",
        office_hours={"tuesday": "10:00-12:00"}
    )
    s_enrolled = Student(user_id=s_enrolled_u.id, institution_id=inst.id, student_id="STU-ENR-01", faculty="Computing", department="SE", program="BSc SE", year_of_study=1, semester=1)
    s_outsider = Student(user_id=s_outsider_u.id, institution_id=inst.id, student_id="STU-OUT-01", faculty="Computing", department="SE", program="BSc SE", year_of_study=1, semester=1)
    test_session.add_all([lec, s_enrolled, s_outsider])
    await test_session.commit()
    await test_session.refresh(lec)
    await test_session.refresh(s_enrolled)
    await test_session.refresh(s_outsider)

    # Course
    course = Course(
        institution_id=inst.id,
        course_code="CS301",
        title="Cloud Architecture & Microservices",
        credits=4,
        faculty="Computing",
        department="Software Engineering",
        semester=1,
        year=2026,
        lecturer_id=lec.id,
        syllabus_data={"overview": "Modern microservices and container orchestration.", "textbook": "Building Microservices by Sam Newman"},
        workspace_settings={"allow_discussions": True, "show_grades": True},
        banner_url="https://images.unsplash.com/cloud-banner.jpg",
        is_active=True
    )
    test_session.add(course)
    await test_session.commit()
    await test_session.refresh(course)

    # Module
    mod = CourseModule(
        course_id=course.id,
        order_index=1,
        title="Module 1: Domain-Driven Design",
        description="Introduction to bounded contexts and aggregate roots",
        learning_objectives=["Understand bounded contexts", "Design domain events"],
        estimated_hours=6.0,
        is_active=True
    )
    # Assignment
    assign = Assignment(
        course_id=course.id,
        title="Architecture Design Proposal",
        description="Submit architecture blueprint in PDF",
        due_date=datetime.utcnow() + timedelta(days=7),
        max_marks=100.0,
        assignment_type="project"
    )
    # Enrollment for s_enrolled
    enrollment = Enrollment(student_id=s_enrolled.id, course_id=course.id, status="active")

    test_session.add_all([mod, assign, enrollment])
    await test_session.commit()

    return {
        "inst": inst,
        "course": course,
        "admin_token": create_access_token({"sub": str(admin_u.id), "role": admin_u.role.value}),
        "lecturer_token": create_access_token({"sub": str(lec_u.id), "role": lec_u.role.value}),
        "enrolled_token": create_access_token({"sub": str(s_enrolled_u.id), "role": s_enrolled_u.role.value}),
        "outsider_token": create_access_token({"sub": str(s_outsider_u.id), "role": s_outsider_u.role.value}),
    }


@pytest.mark.asyncio
async def test_course_workspace_access_authorization(client: AsyncClient, workspace_infra_fixture):
    """Verifies that only enrolled students, assigned instructor, or admin can access course workspace"""
    f = workspace_infra_fixture
    cid = f["course"].id

    # 1. Unenrolled outsider student -> 403 Forbidden
    outsider_res = await client.get(
        f"/api/courses/{cid}/workspace",
        headers={"Authorization": f"Bearer {f['outsider_token']}"}
    )
    assert outsider_res.status_code == 403

    # 2. Enrolled student -> 200 OK
    enrolled_res = await client.get(
        f"/api/courses/{cid}/workspace",
        headers={"Authorization": f"Bearer {f['enrolled_token']}"}
    )
    assert enrolled_res.status_code == 200
    assert enrolled_res.json()["user_context"]["role"] == "student"
    assert enrolled_res.json()["user_context"]["enrollment_status"] == "active"

    # 3. Instructor -> 200 OK
    lecturer_res = await client.get(
        f"/api/courses/{cid}/workspace",
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )
    assert lecturer_res.status_code == 200
    assert lecturer_res.json()["user_context"]["is_instructor"] is True

    # 4. Admin -> 200 OK
    admin_res = await client.get(
        f"/api/courses/{cid}/workspace",
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["user_context"]["is_admin"] is True


@pytest.mark.asyncio
async def test_course_workspace_content_aggregation(client: AsyncClient, workspace_infra_fixture):
    """Verifies unified course workspace returns syllabus, active modules, instructor info, assignments, and stats"""
    f = workspace_infra_fixture
    cid = f["course"].id

    res = await client.get(
        f"/api/courses/{cid}/workspace",
        headers={"Authorization": f"Bearer {f['enrolled_token']}"}
    )
    assert res.status_code == 200
    ws = res.json()
    assert ws["course_code"] == "CS301"
    assert ws["banner_url"] == "https://images.unsplash.com/cloud-banner.jpg"
    assert ws["syllabus_data"]["textbook"] == "Building Microservices by Sam Newman"
    assert ws["stats"]["enrolled_count"] == 1
    assert ws["stats"]["modules_count"] == 1
    assert ws["stats"]["assignments_count"] == 1
    assert ws["lecturer"]["full_name"] == "Dr. Alan Turing"
    assert len(ws["modules"]) == 1
    assert ws["modules"][0]["title"] == "Module 1: Domain-Driven Design"
    assert len(ws["active_assignments"]) == 1
    assert ws["active_assignments"][0]["title"] == "Architecture Design Proposal"


@pytest.mark.asyncio
async def test_course_workspace_settings_update(client: AsyncClient, workspace_infra_fixture):
    """Verifies instructor can update course workspace settings while students are forbidden"""
    f = workspace_infra_fixture
    cid = f["course"].id

    # 1. Student attempts to update settings -> 403 Forbidden
    student_attempt = await client.put(
        f"/api/courses/{cid}/workspace/settings",
        json={"banner_url": "https://hacked.com/image.png"},
        headers={"Authorization": f"Bearer {f['enrolled_token']}"}
    )
    assert student_attempt.status_code == 403

    # 2. Instructor updates settings -> 200 OK
    instructor_update = await client.put(
        f"/api/courses/{cid}/workspace/settings",
        json={
            "banner_url": "https://images.unsplash.com/new-cloud-banner.jpg",
            "workspace_settings": {"allow_discussions": False, "sequential_modules": True}
        },
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )
    assert instructor_update.status_code == 200
    assert instructor_update.json()["banner_url"] == "https://images.unsplash.com/new-cloud-banner.jpg"
    assert instructor_update.json()["workspace_settings"]["sequential_modules"] is True
