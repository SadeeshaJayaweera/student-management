"""
NSBM EduSphere — Secure Student Information Management Tests
Validates student provisioning, academic status transitions, PII masking,
filtered searching, and fine-grained authorization enforcement.
"""
import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, Institution, Campus, Program, Faculty, Department, Student
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def student_infra_fixture(test_session: AsyncSession):
    """Sets up institution, campus, faculty, department, program, and roles for testing"""
    inst = Institution(name="NSBM University", code="NSBM", is_active=True)
    test_session.add(inst)
    await test_session.commit()
    await test_session.refresh(inst)

    campus = Campus(institution_id=inst.id, name="Green Campus Pitipana", code="CMP-PITI", city="Homagama")
    faculty = Faculty(institution_id=inst.id, name="School of Computing", code="FOC")
    test_session.add_all([campus, faculty])
    await test_session.commit()
    await test_session.refresh(campus)
    await test_session.refresh(faculty)

    dept = Department(institution_id=inst.id, faculty_id=faculty.id, name="Software Engineering", code="DEP-SE")
    test_session.add(dept)
    await test_session.commit()
    await test_session.refresh(dept)

    prog = Program(
        institution_id=inst.id,
        faculty_id=faculty.id,
        department_id=dept.id,
        code="BSC-SE",
        name="BSc (Hons) in Software Engineering",
        qualification="BSc",
        total_credits=120,
    )
    test_session.add(prog)
    await test_session.commit()
    await test_session.refresh(prog)

    # Users: Admin, Registrar, Lecturer, Student 1, Student 2
    admin_user = User(
        username="admin_user",
        email="admin@nsbm.ac.lk",
        full_name="Admin Officer",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.ADMIN,
        institution_id=inst.id,
        is_active=True,
    )
    registrar_user = User(
        username="registrar_user",
        email="registrar@nsbm.ac.lk",
        full_name="Registrar Officer",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.REGISTRAR,
        institution_id=inst.id,
        is_active=True,
    )
    lecturer_user = User(
        username="lecturer_user",
        email="lecturer@nsbm.ac.lk",
        full_name="Dr. Lecturer",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.LECTURER,
        institution_id=inst.id,
        is_active=True,
    )
    student1_user = User(
        username="student1",
        email="student1@nsbm.ac.lk",
        full_name="Student One",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.STUDENT,
        institution_id=inst.id,
        is_active=True,
    )
    student2_user = User(
        username="student2",
        email="student2@nsbm.ac.lk",
        full_name="Student Two",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.STUDENT,
        institution_id=inst.id,
        is_active=True,
    )

    test_session.add_all([admin_user, registrar_user, lecturer_user, student1_user, student2_user])
    await test_session.commit()
    for u in [admin_user, registrar_user, lecturer_user, student1_user, student2_user]:
        await test_session.refresh(u)

    return {
        "inst": inst,
        "campus": campus,
        "faculty": faculty,
        "dept": dept,
        "program": prog,
        "admin": admin_user,
        "registrar": registrar_user,
        "lecturer": lecturer_user,
        "student1_user": student1_user,
        "student2_user": student2_user,
        "admin_token": create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value}),
        "registrar_token": create_access_token({"sub": str(registrar_user.id), "role": registrar_user.role.value}),
        "lecturer_token": create_access_token({"sub": str(lecturer_user.id), "role": lecturer_user.role.value}),
        "student1_token": create_access_token({"sub": str(student1_user.id), "role": student1_user.role.value}),
        "student2_token": create_access_token({"sub": str(student2_user.id), "role": student2_user.role.value}),
    }


@pytest.mark.asyncio
async def test_student_provisioning_and_authorization(client: AsyncClient, student_infra_fixture):
    """Verifies that only authorized staff (Admin/Registrar) can provision student profiles"""
    f = student_infra_fixture

    payload = {
        "user_id": f["student1_user"].id,
        "student_id": "NSBM/2026/SE/001",
        "faculty": "School of Computing",
        "department": "Software Engineering",
        "program": "BSc (Hons) in Software Engineering",
        "year_of_study": 1,
        "semester": 1,
        "campus_id": f["campus"].id,
        "program_id": f["program"].id,
        "faculty_id": f["faculty"].id,
        "department_id": f["dept"].id,
        "national_id": "200109876543",
        "date_of_birth": "2001-05-15",
        "gender": "male",
        "address": "123 Colombo Road",
        "emergency_contact": "+94771234567",
        "academic_standing": "good_standing",
        "enrollment_status": "enrolled",
    }

    # Student trying to create profile -> 403
    res = await client.post(
        "/api/students",
        json=payload,
        headers={"Authorization": f"Bearer {f['student1_token']}"}
    )
    assert res.status_code == 403

    # Registrar creates student profile -> 201
    res = await client.post(
        "/api/students",
        json=payload,
        headers={"Authorization": f"Bearer {f['registrar_token']}"}
    )
    assert res.status_code == 201
    created = res.json()
    assert created["student_id"] == "NSBM/2026/SE/001"
    assert created["national_id"] == "200109876543"
    assert created["date_of_birth"] == "2001-05-15"
    assert created["campus_id"] == f["campus"].id
    assert created["program_id"] == f["program"].id

    # Duplicate provisioning -> 409
    dup_res = await client.post(
        "/api/students",
        json=payload,
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_student_pii_masking_and_bola_defense(client: AsyncClient, student_infra_fixture):
    """
    Verifies BOLA defense and role-based PII masking:
    - Admin, Registrar, and Student themselves see full PII (national_id, date_of_birth).
    - Lecturers see redacted PII (national_id: REDACTED, date_of_birth: null).
    - Other students cannot view peer profiles (403 Forbidden).
    """
    f = student_infra_fixture

    # Provision student
    res = await client.post(
        "/api/students",
        json={
            "user_id": f["student1_user"].id,
            "student_id": "NSBM/2026/SE/002",
            "campus_id": f["campus"].id,
            "program_id": f["program"].id,
            "national_id": "199912345678",
            "date_of_birth": "1999-10-20",
            "address": "456 Kandy Rd",
            "emergency_contact": "+94770001122"
        },
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert res.status_code == 201
    student_record_id = res.json()["id"]

    # 1. Admin reads profile -> Full PII
    admin_get = await client.get(
        f"/api/students/{student_record_id}",
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert admin_get.status_code == 200
    assert admin_get.json()["national_id"] == "199912345678"
    assert admin_get.json()["date_of_birth"] == "1999-10-20"

    # 2. Student himself reads profile -> Full PII
    student_get = await client.get(
        f"/api/students/{student_record_id}",
        headers={"Authorization": f"Bearer {f['student1_token']}"}
    )
    assert student_get.status_code == 200
    assert student_get.json()["national_id"] == "199912345678"
    assert student_get.json()["date_of_birth"] == "1999-10-20"

    # 3. Lecturer reads profile -> Redacted PII
    lecturer_get = await client.get(
        f"/api/students/{student_record_id}",
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )
    assert lecturer_get.status_code == 200
    assert lecturer_get.json()["national_id"] == "REDACTED"
    assert lecturer_get.json()["date_of_birth"] is None

    # 4. Another student reads profile -> 403 Forbidden (BOLA defense)
    other_student_get = await client.get(
        f"/api/students/{student_record_id}",
        headers={"Authorization": f"Bearer {f['student2_token']}"}
    )
    assert other_student_get.status_code == 403


@pytest.mark.asyncio
async def test_student_status_transitions_and_profile_updates(client: AsyncClient, student_infra_fixture):
    """
    Verifies:
    - Administrative status updates (enrollment_status, academic_standing).
    - Rejection of invalid status transitions.
    - Privilege escalation defense: students cannot alter academic status or programs.
    - Students can safely update address and emergency contact.
    """
    f = student_infra_fixture

    res = await client.post(
        "/api/students",
        json={
            "user_id": f["student1_user"].id,
            "student_id": "NSBM/2026/SE/003",
            "campus_id": f["campus"].id,
            "program_id": f["program"].id,
            "academic_standing": "good_standing",
            "enrollment_status": "enrolled"
        },
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert res.status_code == 201
    s_id = res.json()["id"]

    # 1. Admin updates status to on_leave and probation -> 200
    status_patch = await client.patch(
        f"/api/students/{s_id}/status",
        json={
            "enrollment_status": "on_leave",
            "academic_standing": "academic_probation"
        },
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert status_patch.status_code == 200
    assert status_patch.json()["enrollment_status"] == "on_leave"
    assert status_patch.json()["academic_standing"] == "academic_probation"

    # 2. Invalid status -> 400
    invalid_patch = await client.patch(
        f"/api/students/{s_id}/status",
        json={"enrollment_status": "expelled_invalid_state"},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert invalid_patch.status_code == 400

    # 3. Student attempting to update academic status directly -> 403
    student_attempt = await client.put(
        f"/api/students/{s_id}",
        json={"academic_standing": "good_standing"},
        headers={"Authorization": f"Bearer {f['student1_token']}"}
    )
    assert student_attempt.status_code == 403

    # 4. Student updating allowed personal details -> 200
    student_personal_update = await client.put(
        f"/api/students/{s_id}",
        json={"address": "New Student Apartment", "emergency_contact": "+94719998888"},
        headers={"Authorization": f"Bearer {f['student1_token']}"}
    )
    assert student_personal_update.status_code == 200
    assert student_personal_update.json()["address"] == "New Student Apartment"
    assert student_personal_update.json()["emergency_contact"] == "+94719998888"
