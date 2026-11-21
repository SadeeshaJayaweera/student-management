"""
NSBM EduSphere — Academic Year & Semester Management Integration Tests
Validates academic calendar creation, semester cycles, registration windows,
current-term flag transitions, and tenant access controls.
"""
from datetime import date, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, Institution
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def institution_fixture(test_session: AsyncSession):
    """Creates two test institutions for tenant testing"""
    inst1 = Institution(name="NSBM Green University", code="NSBM", is_active=True)
    inst2 = Institution(name="Global University", code="GLOBAL", is_active=True)
    test_session.add_all([inst1, inst2])
    await test_session.commit()
    await test_session.refresh(inst1)
    await test_session.refresh(inst2)
    return inst1, inst2


@pytest.fixture
async def auth_users(test_session: AsyncSession, institution_fixture):
    """Creates admin, cross-institution admin, and student users"""
    inst1, inst2 = institution_fixture

    admin = User(
        username="termadmin",
        email="termadmin@nsbm.ac.lk",
        full_name="Academic Term Admin",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.ADMIN,
        institution_id=inst1.id,
        is_active=True,
    )
    other_admin = User(
        username="otheradmin",
        email="otheradmin@global.edu",
        full_name="Other Admin",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.ADMIN,
        institution_id=inst2.id,
        is_active=True,
    )
    student = User(
        username="termstudent",
        email="termstudent@nsbm.ac.lk",
        full_name="Term Student",
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
        "inst1": inst1,
        "inst2": inst2,
    }


@pytest.mark.asyncio
async def test_academic_year_lifecycle_and_current_term(client: AsyncClient, auth_users):
    """Verify academic year creation, validation, updating, and current term assignment"""
    admin_token = auth_users["admin_token"]
    inst1 = auth_users["inst1"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    today = date.today()

    # 1. Reject invalid dates (end_date <= start_date)
    invalid_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/academic-years",
        json={
            "code": "AY-BAD",
            "name": "Invalid Term",
            "start_date": str(today),
            "end_date": str(today - timedelta(days=1)),
        },
        headers=headers,
    )
    assert invalid_resp.status_code == 400

    # 2. Create Academic Year 1
    ay1_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/academic-years",
        json={
            "code": "AY-2025-2026",
            "name": "Academic Year 2025/2026",
            "start_date": str(today),
            "end_date": str(today + timedelta(days=365)),
            "is_current": True,
        },
        headers=headers,
    )
    assert ay1_resp.status_code == 201
    ay1 = ay1_resp.json()
    assert ay1["is_current"] is True
    ay1_id = ay1["id"]

    # 3. Create Academic Year 2 and set as current
    ay2_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/academic-years",
        json={
            "code": "AY-2026-2027",
            "name": "Academic Year 2026/2027",
            "start_date": str(today + timedelta(days=366)),
            "end_date": str(today + timedelta(days=730)),
            "is_current": True,
        },
        headers=headers,
    )
    assert ay2_resp.status_code == 201
    ay2 = ay2_resp.json()
    assert ay2["is_current"] is True
    ay2_id = ay2["id"]

    # Verify AY 1 is no longer current
    get_ay1 = await client.get(f"/api/v1/academic-years/{ay1_id}", headers=headers)
    assert get_ay1.status_code == 200
    assert get_ay1.json()["is_current"] is False

    # 4. Switch back to AY 1 via set-current endpoint
    switch_resp = await client.post(f"/api/v1/academic-years/{ay1_id}/set-current", headers=headers)
    assert switch_resp.status_code == 200
    assert switch_resp.json()["is_current"] is True


@pytest.mark.asyncio
async def test_semester_lifecycle_and_registration_calendar(client: AsyncClient, auth_users):
    """Verify semester calendar creation with census, registration, and examination windows"""
    admin_token = auth_users["admin_token"]
    inst1 = auth_users["inst1"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    today = date.today()

    # 1. Setup Academic Year
    ay_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/academic-years",
        json={
            "code": "AY-2025-2026-SEM",
            "name": "Academic Year 2025/2026",
            "start_date": str(today),
            "end_date": str(today + timedelta(days=365)),
            "is_current": True,
        },
        headers=headers,
    )
    assert ay_resp.status_code == 201
    ay_id = ay_resp.json()["id"]

    # 2. Create Semester 1
    sem1_payload = {
        "code": "AY25-S1",
        "name": "Year 1 Semester 1",
        "term_number": 1,
        "start_date": str(today),
        "end_date": str(today + timedelta(days=150)),
        "census_date": str(today + timedelta(days=30)),
        "registration_start_date": str(today - timedelta(days=14)),
        "registration_end_date": str(today + timedelta(days=14)),
        "add_drop_deadline": str(today + timedelta(days=21)),
        "exam_start_date": str(today + timedelta(days=130)),
        "exam_end_date": str(today + timedelta(days=150)),
        "is_current": True,
    }
    sem1_resp = await client.post(
        f"/api/v1/academic-years/{ay_id}/semesters",
        json=sem1_payload,
        headers=headers,
    )
    assert sem1_resp.status_code == 201
    sem1 = sem1_resp.json()
    assert sem1["code"] == "AY25-S1"
    assert sem1["term_number"] == 1
    assert sem1["is_current"] is True
    sem1_id = sem1["id"]

    # 3. Get Current Semester for Institution
    curr_resp = await client.get(
        f"/api/v1/institutions/{inst1.id}/semesters/current",
        headers=headers,
    )
    assert curr_resp.status_code == 200
    curr_data = curr_resp.json()
    assert curr_data is not None
    assert curr_data["id"] == sem1_id

    # 4. List Semesters
    list_resp = await client.get(f"/api/v1/academic-years/{ay_id}/semesters", headers=headers)
    assert list_resp.status_code == 200
    semesters = list_resp.json()
    assert len(semesters) == 1
    assert semesters[0]["id"] == sem1_id


@pytest.mark.asyncio
async def test_academic_terms_rbac_and_tenant_security(client: AsyncClient, auth_users):
    """Verify students cannot mutate terms and cross-institution tenant admins are rejected"""
    admin_token = auth_users["admin_token"]
    other_admin_token = auth_users["other_admin_token"]
    student_token = auth_users["student_token"]
    inst1 = auth_users["inst1"]

    today = date.today()
    payload = {
        "code": "AY-ATTEMPT",
        "name": "Attempt Term",
        "start_date": str(today),
        "end_date": str(today + timedelta(days=365)),
    }

    # 1. Student access denied (403)
    stu_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/academic-years",
        json=payload,
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert stu_resp.status_code == 403

    # 2. Cross-tenant admin access denied (403)
    cross_resp = await client.post(
        f"/api/v1/institutions/{inst1.id}/academic-years",
        json=payload,
        headers={"Authorization": f"Bearer {other_admin_token}"},
    )
    assert cross_resp.status_code == 403
