"""
NSBM EduSphere — Institution and Campus Management Integration Tests
Validates enterprise multi-campus, faculty, and department hierarchy operations,
role-based permissions, and cross-institution tenant isolation.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, Institution
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def institution_fixture(test_session: AsyncSession):
    """Creates two test institutions for tenant hierarchy tests"""
    inst1 = Institution(
        name="NSBM Green University",
        code="NSBM",
        subdomain="nsbm",
        domain="nsbm.ac.lk",
        is_active=True,
    )
    inst2 = Institution(
        name="Partner University",
        code="PARTNER",
        subdomain="partner",
        domain="partner.edu",
        is_active=True,
    )
    test_session.add_all([inst1, inst2])
    await test_session.commit()
    await test_session.refresh(inst1)
    await test_session.refresh(inst2)
    return inst1, inst2


@pytest.fixture
async def auth_users(test_session: AsyncSession, institution_fixture):
    """Creates admin, other institution admin, and student users"""
    inst1, inst2 = institution_fixture

    admin = User(
        username="nsbmadmin",
        email="admin@nsbm.ac.lk",
        full_name="NSBM Administrator",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.ADMIN,
        institution_id=inst1.id,
        is_active=True,
    )
    other_admin = User(
        username="partneradmin",
        email="admin@partner.edu",
        full_name="Partner Administrator",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.ADMIN,
        institution_id=inst2.id,
        is_active=True,
    )
    student = User(
        username="regularstudent",
        email="student@nsbm.ac.lk",
        full_name="Regular Student",
        hashed_password=hash_password("Student@123"),
        role=UserRole.STUDENT,
        institution_id=inst1.id,
        is_active=True,
    )
    superadmin = User(
        username="globalsuperadmin",
        email="superadmin@edusphere.io",
        full_name="Global Superadmin",
        hashed_password=hash_password("SuperAdmin@123"),
        role=UserRole.ADMIN,
        institution_id=None,  # Platform-wide superadmin
        is_active=True,
    )

    test_session.add_all([admin, other_admin, student, superadmin])
    await test_session.commit()
    await test_session.refresh(admin)
    await test_session.refresh(other_admin)
    await test_session.refresh(student)
    await test_session.refresh(superadmin)

    return {
        "admin_token": create_access_token({"sub": str(admin.id), "role": admin.role.value}),
        "other_admin_token": create_access_token({"sub": str(other_admin.id), "role": other_admin.role.value}),
        "student_token": create_access_token({"sub": str(student.id), "role": student.role.value}),
        "superadmin_token": create_access_token({"sub": str(superadmin.id), "role": superadmin.role.value}),
        "inst1": inst1,
        "inst2": inst2,
    }


@pytest.mark.asyncio
async def test_campus_crud_lifecycle(client: AsyncClient, auth_users):
    """Verify full CRUD lifecycle for campuses under an institution"""
    admin_token = auth_users["admin_token"]
    inst1 = auth_users["inst1"]

    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Campus
    create_payload = {
        "code": "MAIN",
        "name": "Pitipana Main Campus",
        "address": "Mahenwatta, Pitipana, Homagama",
        "city": "Homagama",
        "state": "Western Province",
        "country": "Sri Lanka",
        "contact_email": "info@nsbm.ac.lk",
        "contact_phone": "+94115445000",
        "is_active": True,
    }
    create_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/campuses",
        json=create_payload,
        headers=headers,
    )
    assert create_resp.status_code == 201
    campus_data = create_resp.json()
    assert campus_data["code"] == "MAIN"
    assert campus_data["name"] == "Pitipana Main Campus"
    campus_id = campus_data["id"]

    # 2. Get Campus by ID
    get_resp = await client.get(f"/api/v1/campuses/{campus_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == campus_id

    # 3. List Campuses
    list_resp = await client.get(f"/api/v1/institutions/{inst1.id}/campuses", headers=headers)
    assert list_resp.status_code == 200
    campuses = list_resp.json()
    assert len(campuses) >= 1
    assert any(c["code"] == "MAIN" for c in campuses)

    # 4. Update Campus
    update_resp = await client.put(
        f"/api/v1/campuses/{campus_id}",
        json={"name": "Pitipana Green Campus (Main)"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Pitipana Green Campus (Main)"


@pytest.mark.asyncio
async def test_faculty_and_department_hierarchy(client: AsyncClient, auth_users):
    """Verify complete hierarchy: Institution -> Campus -> Faculty -> Department"""
    admin_token = auth_users["admin_token"]
    inst1 = auth_users["inst1"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Setup Campus
    camp_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/campuses",
        json={"code": "CITY", "name": "City Campus Colombo"},
        headers=headers,
    )
    assert camp_resp.status_code == 201
    campus_id = camp_resp.json()["id"]

    # 2. Create Faculty
    fac_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/faculties",
        json={
            "code": "FOC",
            "name": "Faculty of Computing",
            "campus_id": campus_id,
            "description": "Excellence in computing, software, and AI education.",
            "dean_name": "Dr. Rasika Silva",
            "contact_email": "dean.computing@nsbm.ac.lk",
            "is_active": True,
        },
        headers=headers,
    )
    assert fac_resp.status_code == 201
    faculty_data = fac_resp.json()
    assert faculty_data["code"] == "FOC"
    faculty_id = faculty_data["id"]

    # 3. Create Department under Faculty
    dept_resp = await client.post(
        f"/api/v1/faculties/{faculty_id}/departments",
        json={
            "code": "DSE",
            "name": "Department of Software Engineering",
            "description": "Modern software engineering and distributed systems.",
            "head_of_department": "Prof. Anura Jayasumana",
            "contact_email": "hod.se@nsbm.ac.lk",
            "is_active": True,
        },
        headers=headers,
    )
    assert dept_resp.status_code == 201
    dept_data = dept_resp.json()
    assert dept_data["code"] == "DSE"
    assert dept_data["faculty_id"] == faculty_id
    dept_id = dept_data["id"]

    # 4. List Departments
    dept_list_resp = await client.get(f"/api/v1/faculties/{faculty_id}/departments", headers=headers)
    assert dept_list_resp.status_code == 200
    depts = dept_list_resp.json()
    assert len(depts) == 1
    assert depts[0]["id"] == dept_id


@pytest.mark.asyncio
async def test_academic_hierarchy_rbac_and_tenant_isolation(client: AsyncClient, auth_users):
    """Verify unauthorized users and cross-tenant institution admins cannot mutate hierarchy"""
    admin_token = auth_users["admin_token"]
    other_admin_token = auth_users["other_admin_token"]
    student_token = auth_users["student_token"]
    inst1 = auth_users["inst1"]
    inst2 = auth_users["inst2"]

    # 1. Non-admin (Student) forbidden from creating campus
    stu_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/campuses",
        json={"code": "FAIL", "name": "Forbidden Campus"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert stu_resp.status_code == 403

    # 2. Admin of Institution 2 forbidden from creating campus in Institution 1 (Tenant isolation)
    other_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/campuses",
        json={"code": "HACK", "name": "Cross Tenant Campus"},
        headers={"Authorization": f"Bearer {other_admin_token}"},
    )
    assert other_resp.status_code == 403

    # 3. Global Superadmin can create campus in any institution
    super_token = auth_users["superadmin_token"]
    super_resp = await client.post(
        f"/api/v1/institutions/{inst2.id}/campuses",
        json={"code": "PARTNER1", "name": "Partner Main Campus"},
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert super_resp.status_code == 201
    assert super_resp.json()["code"] == "PARTNER1"
