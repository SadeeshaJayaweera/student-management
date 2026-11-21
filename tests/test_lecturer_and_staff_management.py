"""
NSBM EduSphere — Lecturer and Staff Management Tests
Validates academic staff provisioning, department assignments, teaching workload calculation,
privilege escalation defenses, and filtered catalog queries.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, Institution, Campus, Faculty, Department, Lecturer, Course, Enrollment, Student
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def staff_infra_fixture(test_session: AsyncSession):
    """Sets up institution, campus, faculty, department, courses, and role accounts for staff testing"""
    inst = Institution(name="NSBM University", code="NSBM-STAFF", is_active=True)
    test_session.add(inst)
    await test_session.commit()
    await test_session.refresh(inst)

    campus = Campus(institution_id=inst.id, name="Green Campus", code="CMP-GC", city="Homagama")
    faculty = Faculty(institution_id=inst.id, name="Faculty of Computing", code="FOC")
    test_session.add_all([campus, faculty])
    await test_session.commit()
    await test_session.refresh(campus)
    await test_session.refresh(faculty)

    dept = Department(institution_id=inst.id, faculty_id=faculty.id, name="Computer Networks", code="DEP-CN")
    test_session.add(dept)
    await test_session.commit()
    await test_session.refresh(dept)

    # Users
    admin_user = User(
        username="staff_admin",
        email="staffadmin@nsbm.ac.lk",
        full_name="Staff Administrator",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.ADMIN,
        institution_id=inst.id,
        is_active=True,
    )
    dean_user = User(
        username="dean_computing",
        email="dean@nsbm.ac.lk",
        full_name="Prof. Dean",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.DEAN,
        institution_id=inst.id,
        is_active=True,
    )
    lecturer1_user = User(
        username="prof_kamal",
        email="kamal@nsbm.ac.lk",
        full_name="Dr. Kamal Silva",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.LECTURER,
        institution_id=inst.id,
        is_active=True,
    )
    lecturer2_user = User(
        username="prof_nimal",
        email="nimal@nsbm.ac.lk",
        full_name="Dr. Nimal Perera",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.LECTURER,
        institution_id=inst.id,
        is_active=True,
    )
    student_user = User(
        username="student_user",
        email="stu@nsbm.ac.lk",
        full_name="Campus Student",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.STUDENT,
        institution_id=inst.id,
        is_active=True,
    )

    test_session.add_all([admin_user, dean_user, lecturer1_user, lecturer2_user, student_user])
    await test_session.commit()
    for u in [admin_user, dean_user, lecturer1_user, lecturer2_user, student_user]:
        await test_session.refresh(u)

    return {
        "inst": inst,
        "campus": campus,
        "faculty": faculty,
        "dept": dept,
        "admin": admin_user,
        "dean": dean_user,
        "lecturer1": lecturer1_user,
        "lecturer2": lecturer2_user,
        "student": student_user,
        "admin_token": create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value}),
        "dean_token": create_access_token({"sub": str(dean_user.id), "role": dean_user.role.value}),
        "lecturer1_token": create_access_token({"sub": str(lecturer1_user.id), "role": lecturer1_user.role.value}),
        "lecturer2_token": create_access_token({"sub": str(lecturer2_user.id), "role": lecturer2_user.role.value}),
        "student_token": create_access_token({"sub": str(student_user.id), "role": student_user.role.value}),
    }


@pytest.mark.asyncio
async def test_lecturer_provisioning_and_rbac(client: AsyncClient, staff_infra_fixture):
    """Verifies that only Admins/Deans/Registrars can provision lecturer profiles and target users must be faculty"""
    f = staff_infra_fixture

    payload = {
        "user_id": f["lecturer1"].id,
        "lecturer_id": "LEC-2026-001",
        "faculty": "Faculty of Computing",
        "department": "Computer Networks",
        "specialization": "Cloud Infrastructure & Cybersecurity",
        "qualification": "PhD in Cybersecurity",
        "designation": "Senior Lecturer",
        "employment_status": "full_time",
        "campus_id": f["campus"].id,
        "faculty_id": f["faculty"].id,
        "department_id": f["dept"].id,
        "office_location": "Building C, Room 302",
        "office_hours": {"monday": "10:00-12:00", "thursday": "14:00-16:00"},
        "max_teaching_load_hours": 18,
    }

    # 1. Student attempting to provision staff profile -> 403 Forbidden
    res = await client.post(
        "/api/lecturers",
        json=payload,
        headers={"Authorization": f"Bearer {f['student_token']}"}
    )
    assert res.status_code == 403

    # 2. Dean provisions staff profile -> 201 Created
    res = await client.post(
        "/api/lecturers",
        json=payload,
        headers={"Authorization": f"Bearer {f['dean_token']}"}
    )
    assert res.status_code == 201
    created = res.json()
    assert created["lecturer_id"] == "LEC-2026-001"
    assert created["designation"] == "Senior Lecturer"
    assert created["employment_status"] == "full_time"
    assert created["max_teaching_load_hours"] == 18
    assert created["campus_id"] == f["campus"].id

    # 3. Provisioning for a student user -> 400 Bad Request
    invalid_payload = dict(payload)
    invalid_payload["user_id"] = f["student"].id
    invalid_payload["lecturer_id"] = "LEC-INVALID-001"
    res = await client.post(
        "/api/lecturers",
        json=invalid_payload,
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert res.status_code == 400

    # 4. Duplicate provisioning -> 409 Conflict
    res = await client.post(
        "/api/lecturers",
        json=payload,
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_lecturer_profile_updates_and_privilege_escalation(client: AsyncClient, staff_infra_fixture):
    """
    Verifies:
    - Lecturer can update their own personal details (bio, office_hours, research).
    - Lecturer CANNOT escalate privilege by altering employment_status or max_teaching_load_hours.
    - Admin/Dean can update appointment, designation, and employment status.
    """
    f = staff_infra_fixture

    # Provision lecturer
    res = await client.post(
        "/api/lecturers",
        json={
            "user_id": f["lecturer1"].id,
            "lecturer_id": "LEC-2026-002",
            "faculty": "Faculty of Computing",
            "department": "Computer Networks",
            "designation": "Lecturer",
            "employment_status": "full_time",
            "campus_id": f["campus"].id,
            "faculty_id": f["faculty"].id,
            "department_id": f["dept"].id,
            "max_teaching_load_hours": 15,
        },
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert res.status_code == 201
    lec_id = res.json()["id"]

    # 1. Lecturer updates allowed bio and office location -> 200 OK
    res = await client.put(
        f"/api/lecturers/{lec_id}",
        json={
            "bio": "Expert in distributed computing and networks.",
            "office_location": "Lab 4, Innovation Center",
            "publications": 12
        },
        headers={"Authorization": f"Bearer {f['lecturer1_token']}"}
    )
    assert res.status_code == 200
    assert res.json()["bio"] == "Expert in distributed computing and networks."
    assert res.json()["publications"] == 12

    # 2. Lecturer attempts privilege escalation (change status to on_leave or reduce workload limit) -> 403 Forbidden
    escalation_res = await client.put(
        f"/api/lecturers/{lec_id}",
        json={"employment_status": "on_leave"},
        headers={"Authorization": f"Bearer {f['lecturer1_token']}"}
    )
    assert escalation_res.status_code == 403

    load_escalation_res = await client.put(
        f"/api/lecturers/{lec_id}",
        json={"max_teaching_load_hours": 3},
        headers={"Authorization": f"Bearer {f['lecturer1_token']}"}
    )
    assert load_escalation_res.status_code == 403

    # 3. Dean updates designation and employment status -> 200 OK
    admin_update_res = await client.put(
        f"/api/lecturers/{lec_id}",
        json={
            "designation": "Associate Professor",
            "employment_status": "on_leave",
            "max_teaching_load_hours": 20
        },
        headers={"Authorization": f"Bearer {f['dean_token']}"}
    )
    assert admin_update_res.status_code == 200
    assert admin_update_res.json()["designation"] == "Associate Professor"
    assert admin_update_res.json()["employment_status"] == "on_leave"
    assert admin_update_res.json()["max_teaching_load_hours"] == 20


@pytest.mark.asyncio
async def test_lecturer_workload_calculation_and_filtering(client: AsyncClient, test_session: AsyncSession, staff_infra_fixture):
    """
    Verifies teaching workload calculation:
    - Assign multiple courses to a lecturer.
    - Check aggregate contact hours, enrolled student counts, and workload summary API.
    - Also verifies listing filters (department, designation, employment_status).
    """
    f = staff_infra_fixture

    # Provision lecturer
    res = await client.post(
        "/api/lecturers",
        json={
            "user_id": f["lecturer1"].id,
            "lecturer_id": "LEC-2026-003",
            "faculty": "Faculty of Computing",
            "department": "Computer Networks",
            "designation": "Senior Lecturer",
            "employment_status": "full_time",
            "campus_id": f["campus"].id,
            "faculty_id": f["faculty"].id,
            "department_id": f["dept"].id,
            "max_teaching_load_hours": 15,
        },
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert res.status_code == 201
    lec_id = res.json()["id"]

    # Assign 2 courses to this lecturer (3 credits and 4 credits -> total 7 contact hours)
    course1 = Course(
        institution_id=f["inst"].id,
        course_code="CN-101",
        title="Intro to Computer Networks",
        credits=3,
        faculty="Faculty of Computing",
        department="Computer Networks",
        semester=1,
        year=2026,
        lecturer_id=lec_id,
        is_active=True
    )
    course2 = Course(
        institution_id=f["inst"].id,
        course_code="CN-201",
        title="Advanced Routing and Switching",
        credits=4,
        faculty="Faculty of Computing",
        department="Computer Networks",
        semester=1,
        year=2026,
        lecturer_id=lec_id,
        is_active=True
    )
    test_session.add_all([course1, course2])
    await test_session.commit()
    await test_session.refresh(course1)
    await test_session.refresh(course2)

    # Enroll student in course1
    # Create student record for student_user
    student_rec = Student(
        user_id=f["student"].id,
        institution_id=f["inst"].id,
        student_id="STU-STAFF-01",
        faculty="Faculty of Computing",
        department="Computer Networks",
        program="BSc in Computer Networks",
        year_of_study=1,
        semester=1
    )
    test_session.add(student_rec)
    await test_session.commit()
    await test_session.refresh(student_rec)

    enrollment = Enrollment(student_id=student_rec.id, course_id=course1.id, status="active")
    test_session.add(enrollment)
    await test_session.commit()

    # Query Workload API
    workload_res = await client.get(
        f"/api/lecturers/{lec_id}/workload",
        headers={"Authorization": f"Bearer {f['lecturer1_token']}"}
    )
    assert workload_res.status_code == 200
    w = workload_res.json()
    assert w["lecturer_id"] == "LEC-2026-003"
    assert w["current_teaching_load_hours"] == 7  # 3 + 4 credits
    assert w["max_teaching_load_hours"] == 15
    assert w["assigned_courses_count"] == 2
    assert w["total_enrolled_students"] == 1
    assert len(w["courses"]) == 2

    # Query List API with filters
    list_res = await client.get(
        "/api/lecturers",
        params={"designation": "Senior Lecturer", "employment_status": "full_time"},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
    assert list_res.json()[0]["lecturer_id"] == "LEC-2026-003"
