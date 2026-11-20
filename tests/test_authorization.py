"""
NSBM EduSphere — Resource-Level Authorization (BOLA / IDOR Defense) Tests
Tests Broken Object-Level Authorization defense, ownership verification,
staff access allowances, and privilege escalation prevention on resource mutations.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, Student, Course, Lecturer, Assignment, Enrollment
from backend.utils.security import hash_password


@pytest.fixture
async def two_students_and_admin(test_session: AsyncSession):
    # Student 1
    u1 = User(
        email="student1@nsbm.ac.lk",
        username="student1",
        hashed_password=hash_password("Student1@123"),
        full_name="Student One",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(u1)
    await test_session.flush()

    s1 = Student(
        user_id=u1.id,
        student_id="STU001",
        faculty="Computing",
        department="Software Engineering",
        program="BSc SE",
        year_of_study=1,
        semester=1,
        address="123 Galle Rd",
    )
    test_session.add(s1)

    # Student 2
    u2 = User(
        email="student2@nsbm.ac.lk",
        username="student2",
        hashed_password=hash_password("Student2@123"),
        full_name="Student Two",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(u2)
    await test_session.flush()

    s2 = Student(
        user_id=u2.id,
        student_id="STU002",
        faculty="Computing",
        department="Information Systems",
        program="BSc MIS",
        year_of_study=2,
        semester=1,
        address="456 Kandy Rd",
    )
    test_session.add(s2)

    # Admin
    admin_u = User(
        email="admin_authz@nsbm.ac.lk",
        username="admin_authz",
        hashed_password=hash_password("AdminAuthz@123"),
        full_name="Admin Authz",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_u)

    # Lecturer
    lec_u = User(
        email="lecturer_authz@nsbm.ac.lk",
        username="lecturer_authz",
        hashed_password=hash_password("LecturerAuthz@123"),
        full_name="Lecturer Authz",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lec_u)
    await test_session.flush()

    lec = Lecturer(
        user_id=lec_u.id,
        lecturer_id="LEC001",
        faculty="Computing",
        department="Software Engineering",
    )
    test_session.add(lec)

    await test_session.commit()
    return {
        "student1": (u1, s1),
        "student2": (u2, s2),
        "admin": admin_u,
        "lecturer": (lec_u, lec),
    }


@pytest.mark.asyncio
async def test_student_can_read_own_profile(client: AsyncClient, two_students_and_admin):
    """Verify Student One can successfully read their own profile"""
    login = await client.post(
        "/api/auth/login",
        data={"username": "student1", "password": "Student1@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/students/STU001", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["student_id"] == "STU001"


@pytest.mark.asyncio
async def test_student_cannot_read_other_student_profile_bola(client: AsyncClient, two_students_and_admin):
    """
    CRITICAL BOLA DEFENSE:
    Student One attempting to access Student Two's profile must receive 403 Forbidden!
    """
    login = await client.post(
        "/api/auth/login",
        data={"username": "student1", "password": "Student1@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to read STU002
    resp = await client.get("/api/students/STU002", headers=headers)
    assert resp.status_code == 403
    assert "access denied" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_faculty_and_admin_can_read_any_student_profile(client: AsyncClient, two_students_and_admin):
    """Verify authorized academic staff (Lecturer and Admin) can view student profiles"""
    # Lecturer login
    lec_login = await client.post(
        "/api/auth/login",
        data={"username": "lecturer_authz", "password": "LecturerAuthz@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    lec_headers = {"Authorization": f"Bearer {lec_login.json()['access_token']}"}

    resp = await client.get("/api/students/STU001", headers=lec_headers)
    assert resp.status_code == 200

    # Admin login
    adm_login = await client.post(
        "/api/auth/login",
        data={"username": "admin_authz", "password": "AdminAuthz@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    adm_resp = await client.get("/api/students/STU002", headers=adm_headers)
    assert adm_resp.status_code == 200


@pytest.mark.asyncio
async def test_student_can_update_own_contact_but_not_academic_fields(client: AsyncClient, two_students_and_admin):
    """Verify student can update personal address, but cannot alter academic year"""
    login = await client.post(
        "/api/auth/login",
        data={"username": "student1", "password": "Student1@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Update personal address -> 200 OK
    upd_resp = await client.put(
        "/api/students/STU001",
        json={"address": "Updated Address 999"},
        headers=headers,
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["address"] == "Updated Address 999"

    # 2. Attempt privilege escalation (change year_of_study to 4) -> 403 Forbidden!
    cheat_resp = await client.put(
        "/api/students/STU001",
        json={"year_of_study": 4},
        headers=headers,
    )
    assert cheat_resp.status_code == 403
    assert "only academic staff" in cheat_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_student_cannot_modify_other_student_profile(client: AsyncClient, two_students_and_admin):
    """Verify Student One cannot modify Student Two's profile (BOLA defense on mutations)"""
    login = await client.post(
        "/api/auth/login",
        data={"username": "student1", "password": "Student1@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.put(
        "/api/students/STU002",
        json={"address": "Malicious Tampering"},
        headers=headers,
    )
    assert resp.status_code == 403
    assert "access denied" in resp.json()["detail"].lower()
