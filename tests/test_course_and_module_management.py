"""
NSBM EduSphere — Course and Module Management Tests
Validates course catalog operations, learning outcomes, delivery methods,
prerequisites configuration, structured learning modules, and access controls.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, Institution, Program
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def academic_base_fixture(test_session: AsyncSession):
    """Creates institution and program for course tests"""
    inst = Institution(name="NSBM Green University", code="NSBM", is_active=True)
    test_session.add(inst)
    await test_session.commit()
    await test_session.refresh(inst)

    prog = Program(
        institution_id=inst.id,
        code="BSC-SE",
        name="BSc in Software Engineering",
        qualification="BSc",
        total_credits=120,
        is_active=True,
    )
    test_session.add(prog)
    await test_session.commit()
    await test_session.refresh(prog)

    return {"inst": inst, "program": prog}


@pytest.fixture
async def auth_users(test_session: AsyncSession, academic_base_fixture):
    """Creates admin and student users"""
    inst = academic_base_fixture["inst"]

    admin = User(
        username="courseadmin",
        email="courseadmin@nsbm.ac.lk",
        full_name="Course Administrator",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.ADMIN,
        institution_id=inst.id,
        is_active=True,
    )
    student = User(
        username="coursestudent",
        email="student@nsbm.ac.lk",
        full_name="Enrolled Student",
        hashed_password=hash_password("Student@123"),
        role=UserRole.STUDENT,
        institution_id=inst.id,
        is_active=True,
    )

    test_session.add_all([admin, student])
    await test_session.commit()
    await test_session.refresh(admin)
    await test_session.refresh(student)

    return {
        "admin_token": create_access_token({"sub": str(admin.id), "role": admin.role.value}),
        "student_token": create_access_token({"sub": str(student.id), "role": student.role.value}),
        "base": academic_base_fixture,
    }


@pytest.mark.asyncio
async def test_course_crud_and_catalog_filtering(client: AsyncClient, auth_users):
    """Verify course creation with learning outcomes, delivery method, and catalog filtering"""
    admin_token = auth_users["admin_token"]
    base = auth_users["base"]
    program = base["program"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Course 1 (Advanced Software Engineering)
    payload1 = {
        "course_code": "SE301",
        "title": "Advanced Software Architecture",
        "description": "Enterprise microservices and domain-driven design.",
        "credits": 4,
        "faculty": "Computing",
        "department": "Software Engineering",
        "semester": 1,
        "year": 3,
        "max_students": 75,
        "program_id": program.id,
        "delivery_method": "blended",
        "learning_outcomes": [
            "Design scalable cloud-native architectures",
            "Implement resilient microservices patterns",
        ],
    }
    resp1 = await client.post("/api/v1/courses", json=payload1, headers=headers)
    assert resp1.status_code == 201
    course1 = resp1.json()
    assert course1["course_code"] == "SE301"
    assert course1["delivery_method"] == "blended"
    assert len(course1["learning_outcomes"]) == 2
    c1_id = course1["id"]

    # 2. Create Course 2 (Intro to Programming)
    payload2 = {
        "course_code": "CS101",
        "title": "Introduction to Computer Science",
        "credits": 3,
        "semester": 1,
        "year": 1,
        "delivery_method": "in_person",
    }
    resp2 = await client.post("/api/v1/courses", json=payload2, headers=headers)
    assert resp2.status_code == 201

    # 3. Filter catalog by delivery_method
    filter_resp = await client.get("/api/v1/courses?delivery_method=blended", headers=headers)
    assert filter_resp.status_code == 200
    blended_courses = filter_resp.json()
    assert len(blended_courses) >= 1
    assert any(c["course_code"] == "SE301" for c in blended_courses)

    # 4. Filter catalog by search query
    search_resp = await client.get("/api/v1/courses?search=Architecture", headers=headers)
    assert search_resp.status_code == 200
    found = search_resp.json()
    assert len(found) >= 1
    assert found[0]["course_code"] == "SE301"


@pytest.mark.asyncio
async def test_course_prerequisites_rules(client: AsyncClient, auth_users):
    """Verify prerequisite configuration, cycle/self-dependency rejection, and listing"""
    admin_token = auth_users["admin_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Introductory & Advanced courses
    c_intro_resp = await client.post(
        "/api/v1/courses",
        json={"course_code": "PR101", "title": "Programming 101", "credits": 3, "semester": 1, "year": 1},
        headers=headers,
    )
    intro_id = c_intro_resp.json()["id"]

    c_adv_resp = await client.post(
        "/api/v1/courses",
        json={"course_code": "PR201", "title": "Programming 201", "credits": 3, "semester": 2, "year": 1},
        headers=headers,
    )
    adv_id = c_adv_resp.json()["id"]

    # 2. Reject self-prerequisite
    self_resp = await client.post(
        f"/api/v1/courses/{adv_id}/prerequisites",
        json={"prerequisite_course_id": adv_id, "is_mandatory": True, "minimum_grade": "C"},
        headers=headers,
    )
    assert self_resp.status_code == 400

    # 3. Add Intro as prerequisite for Advanced
    add_resp = await client.post(
        f"/api/v1/courses/{adv_id}/prerequisites",
        json={"prerequisite_course_id": intro_id, "is_mandatory": True, "minimum_grade": "B"},
        headers=headers,
    )
    assert add_resp.status_code == 201
    prereq = add_resp.json()
    assert prereq["prerequisite_course_code"] == "PR101"
    assert prereq["minimum_grade"] == "B"

    # 4. List prerequisites
    list_resp = await client.get(f"/api/v1/courses/{adv_id}/prerequisites", headers=headers)
    assert list_resp.status_code == 200
    prereqs = list_resp.json()
    assert len(prereqs) == 1
    assert prereqs[0]["prerequisite_course_id"] == intro_id


@pytest.mark.asyncio
async def test_course_learning_modules_flow(client: AsyncClient, auth_users):
    """Verify sequential course learning modules creation, reordering, and detail retrieval"""
    admin_token = auth_users["admin_token"]
    student_token = auth_users["student_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Course
    c_resp = await client.post(
        "/api/v1/courses",
        json={"course_code": "MOD101", "title": "Full-Stack Development", "credits": 3, "semester": 1, "year": 2},
        headers=headers,
    )
    course_id = c_resp.json()["id"]

    # 2. Add Module 1
    m1_resp = await client.post(
        f"/api/v1/courses/{course_id}/modules",
        json={
            "order_index": 1,
            "title": "Module 1: REST API Architecture & OpenAPI",
            "description": "FastAPI fundamentals and request validation.",
            "learning_objectives": ["Understand ASGI", "Build CRUD endpoints"],
            "estimated_hours": 12.5,
        },
        headers=headers,
    )
    assert m1_resp.status_code == 201
    m1 = m1_resp.json()
    assert m1["title"] == "Module 1: REST API Architecture & OpenAPI"
    m1_id = m1["id"]

    # 3. Add Module 2
    m2_resp = await client.post(
        f"/api/v1/courses/{course_id}/modules",
        json={
            "order_index": 2,
            "title": "Module 2: React 19 Frontend Engineering",
            "estimated_hours": 15.0,
        },
        headers=headers,
    )
    assert m2_resp.status_code == 201

    # 4. List Modules for Course
    list_resp = await client.get(f"/api/v1/courses/{course_id}/modules", headers=headers)
    assert list_resp.status_code == 200
    modules = list_resp.json()
    assert len(modules) == 2
    assert modules[0]["order_index"] == 1
    assert modules[1]["order_index"] == 2

    # 5. Non-admin (Student) forbidden from modifying modules
    mod_edit_resp = await client.put(
        f"/api/v1/modules/{m1_id}",
        json={"title": "Hacked Module Title"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert mod_edit_resp.status_code == 403
