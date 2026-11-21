"""
NSBM EduSphere — Academic Program & Curriculum Management Tests
Validates degree programs, qualification levels, specializations,
department linkage, and tenant authorization boundaries.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, Institution, Faculty, Department
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def academic_hierarchy_fixture(test_session: AsyncSession):
    """Creates institutions, faculty, and department for program testing"""
    inst1 = Institution(name="NSBM Green University", code="NSBM", is_active=True)
    inst2 = Institution(name="Other University", code="OTHER", is_active=True)
    test_session.add_all([inst1, inst2])
    await test_session.commit()
    await test_session.refresh(inst1)
    await test_session.refresh(inst2)

    faculty = Faculty(
        institution_id=inst1.id,
        code="FOC",
        name="Faculty of Computing",
        is_active=True,
    )
    test_session.add(faculty)
    await test_session.commit()
    await test_session.refresh(faculty)

    dept = Department(
        institution_id=inst1.id,
        faculty_id=faculty.id,
        code="DSE",
        name="Department of Software Engineering",
        is_active=True,
    )
    test_session.add(dept)
    await test_session.commit()
    await test_session.refresh(dept)

    return {
        "inst1": inst1,
        "inst2": inst2,
        "faculty": faculty,
        "department": dept,
    }


@pytest.fixture
async def auth_users(test_session: AsyncSession, academic_hierarchy_fixture):
    """Creates admin, cross-institution admin, and student users"""
    inst1 = academic_hierarchy_fixture["inst1"]
    inst2 = academic_hierarchy_fixture["inst2"]

    admin = User(
        username="progadmin",
        email="progadmin@nsbm.ac.lk",
        full_name="Program Admin",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.ADMIN,
        institution_id=inst1.id,
        is_active=True,
    )
    other_admin = User(
        username="otherprogadmin",
        email="other@other.edu",
        full_name="Other Admin",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.ADMIN,
        institution_id=inst2.id,
        is_active=True,
    )
    student = User(
        username="progstudent",
        email="student@nsbm.ac.lk",
        full_name="Student",
        hashed_password=hash_password("Student@123"),
        role=UserRole.STUDENT,
        institution_id=inst1.id,
        is_active=True,
    )

    test_session.add_all([admin, other_admin, student])
    await test_session.commit()
    await test_session.refresh(admin)
    await test_session.refresh(other_admin)
    await test_session.refresh(student)

    return {
        "admin_token": create_access_token({"sub": str(admin.id), "role": admin.role.value}),
        "other_admin_token": create_access_token({"sub": str(other_admin.id), "role": other_admin.role.value}),
        "student_token": create_access_token({"sub": str(student.id), "role": student.role.value}),
        "hierarchy": academic_hierarchy_fixture,
    }


@pytest.mark.asyncio
async def test_program_crud_lifecycle(client: AsyncClient, auth_users):
    """Verify degree program creation, linkage to faculty/department, update, and retrieval"""
    admin_token = auth_users["admin_token"]
    hierarchy = auth_users["hierarchy"]
    inst1 = hierarchy["inst1"]
    faculty = hierarchy["faculty"]
    dept = hierarchy["department"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Program
    payload = {
        "code": "BSC-SE",
        "name": "BSc (Hons) in Software Engineering",
        "qualification": "BSc (Hons)",
        "duration_years": 4.0,
        "total_credits": 120,
        "faculty_id": faculty.id,
        "department_id": dept.id,
        "description": "Comprehensive 4-year degree in modern software architecture.",
        "is_active": True,
    }
    create_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/programs",
        json=payload,
        headers=headers,
    )
    assert create_resp.status_code == 201
    prog = create_resp.json()
    assert prog["code"] == "BSC-SE"
    assert prog["qualification"] == "BSc (Hons)"
    assert prog["total_credits"] == 120
    assert prog["faculty_id"] == faculty.id
    assert prog["department_id"] == dept.id
    prog_id = prog["id"]

    # 2. Get Program by ID
    get_resp = await client.get(f"/api/v1/programs/{prog_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == prog_id

    # 3. List Programs for Institution
    list_resp = await client.get(f"/api/v1/institutions/{inst1.id}/programs", headers=headers)
    assert list_resp.status_code == 200
    progs = list_resp.json()
    assert len(progs) >= 1
    assert any(p["code"] == "BSC-SE" for p in progs)

    # 4. Update Program
    update_resp = await client.put(
        f"/api/v1/programs/{prog_id}",
        json={"name": "BSc (Hons) in Software Engineering (Accredited)"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "BSc (Hons) in Software Engineering (Accredited)"


@pytest.mark.asyncio
async def test_specialization_pathway_management(client: AsyncClient, auth_users):
    """Verify specializations / pathways under a degree program"""
    admin_token = auth_users["admin_token"]
    hierarchy = auth_users["hierarchy"]
    inst1 = hierarchy["inst1"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Setup Program
    prog_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/programs",
        json={
            "code": "BSC-CS",
            "name": "BSc in Computer Science",
            "qualification": "BSc",
            "duration_years": 3.0,
            "total_credits": 90,
        },
        headers=headers,
    )
    assert prog_resp.status_code == 201
    prog_id = prog_resp.json()["id"]

    # 2. Create Specialization Track
    spec_payload = {
        "code": "SPEC-AI",
        "name": "Artificial Intelligence & Machine Learning",
        "description": "Specialized coursework in deep learning and NLP.",
        "required_credits": 30,
        "is_active": True,
    }
    spec_resp = await client.post(
        f"/api/v1/programs/{prog_id}/specializations",
        json=spec_payload,
        headers=headers,
    )
    assert spec_resp.status_code == 201
    spec = spec_resp.json()
    assert spec["code"] == "SPEC-AI"
    assert spec["program_id"] == prog_id
    assert spec["required_credits"] == 30
    spec_id = spec["id"]

    # 3. List Specializations for Program
    list_resp = await client.get(f"/api/v1/programs/{prog_id}/specializations", headers=headers)
    assert list_resp.status_code == 200
    specs = list_resp.json()
    assert len(specs) == 1
    assert specs[0]["id"] == spec_id


@pytest.mark.asyncio
async def test_program_curriculum_rbac_and_tenant_security(client: AsyncClient, auth_users):
    """Verify unauthorized students and cross-tenant admins cannot create or modify programs"""
    other_admin_token = auth_users["other_admin_token"]
    student_token = auth_users["student_token"]
    hierarchy = auth_users["hierarchy"]
    inst1 = hierarchy["inst1"]

    payload = {
        "code": "FAIL-PROG",
        "name": "Unauthorized Program",
        "qualification": "BSc",
        "duration_years": 4.0,
        "total_credits": 120,
    }

    # 1. Student access denied (403)
    stu_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/programs",
        json=payload,
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert stu_resp.status_code == 403

    # 2. Cross-tenant admin access denied (403)
    cross_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/programs",
        json=payload,
        headers={"Authorization": f"Bearer {other_admin_token}"},
    )
    assert cross_resp.status_code == 403
