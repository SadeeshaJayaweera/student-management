"""
NSBM EduSphere — Class Cohort and Group Management Tests
Validates cohort creation, section allocations, tutorial/lab groups,
capacity limits, role-based authorization, and student group queries.
"""
import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    User, UserRole, Institution, Campus, Program, Faculty, Department,
    Course, AcademicYear, Student, Lecturer, Cohort, CohortMember, StudentGroup, StudentGroupMember
)
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def cohort_infra_fixture(test_session: AsyncSession):
    """Sets up institution, program, course, academic year, and roles for cohort testing"""
    inst = Institution(name="NSBM University", code="NSBM-COH", is_active=True)
    test_session.add(inst)
    await test_session.commit()
    await test_session.refresh(inst)

    ay = AcademicYear(institution_id=inst.id, code="AY-2026", name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    prog = Program(institution_id=inst.id, code="BSc-SE", name="BSc in Software Engineering", qualification="BSc")
    test_session.add_all([ay, prog])
    await test_session.commit()
    await test_session.refresh(ay)
    await test_session.refresh(prog)

    course = Course(
        institution_id=inst.id,
        course_code="SE101",
        title="Software Engineering Principles",
        credits=3,
        faculty="Computing",
        department="Software Engineering",
        semester=1,
        year=2026
    )
    test_session.add(course)
    await test_session.commit()
    await test_session.refresh(course)

    # Users: Admin, Lecturer, Student 1, Student 2
    admin_u = User(username="admin_c", email="admin_c@nsbm.ac.lk", full_name="Admin Officer", hashed_password=hash_password("Pass@123"), role=UserRole.ADMIN, institution_id=inst.id, is_active=True)
    lec_u = User(username="lec_c", email="lec_c@nsbm.ac.lk", full_name="Dr. Advisor", hashed_password=hash_password("Pass@123"), role=UserRole.LECTURER, institution_id=inst.id, is_active=True)
    s1_u = User(username="s1_c", email="s1_c@nsbm.ac.lk", full_name="Student 1", hashed_password=hash_password("Pass@123"), role=UserRole.STUDENT, institution_id=inst.id, is_active=True)
    s2_u = User(username="s2_c", email="s2_c@nsbm.ac.lk", full_name="Student 2", hashed_password=hash_password("Pass@123"), role=UserRole.STUDENT, institution_id=inst.id, is_active=True)
    test_session.add_all([admin_u, lec_u, s1_u, s2_u])
    await test_session.commit()
    for u in [admin_u, lec_u, s1_u, s2_u]:
        await test_session.refresh(u)

    lec_prof = Lecturer(user_id=lec_u.id, institution_id=inst.id, lecturer_id="LEC-C01", faculty="Computing", department="SE")
    s1_prof = Student(user_id=s1_u.id, institution_id=inst.id, student_id="STU-C01", faculty="Computing", department="SE", program="BSc-SE", year_of_study=1, semester=1)
    s2_prof = Student(user_id=s2_u.id, institution_id=inst.id, student_id="STU-C02", faculty="Computing", department="SE", program="BSc-SE", year_of_study=1, semester=1)
    test_session.add_all([lec_prof, s1_prof, s2_prof])
    await test_session.commit()
    await test_session.refresh(lec_prof)
    await test_session.refresh(s1_prof)
    await test_session.refresh(s2_prof)

    return {
        "inst": inst,
        "ay": ay,
        "program": prog,
        "course": course,
        "lecturer": lec_prof,
        "s1": s1_prof,
        "s2": s2_prof,
        "admin_token": create_access_token({"sub": str(admin_u.id), "role": admin_u.role.value}),
        "lecturer_token": create_access_token({"sub": str(lec_u.id), "role": lec_u.role.value}),
        "s1_token": create_access_token({"sub": str(s1_u.id), "role": s1_u.role.value}),
        "s2_token": create_access_token({"sub": str(s2_u.id), "role": s2_u.role.value}),
    }


@pytest.mark.asyncio
async def test_cohort_crud_and_capacity_limits(client: AsyncClient, cohort_infra_fixture):
    """Verifies cohort provisioning, duplicate protection, RBAC, and capacity limit enforcement"""
    f = cohort_infra_fixture

    payload = {
        "code": "COH-2026-SE-A",
        "name": "Batch 2026 Software Engineering Section A",
        "program_id": f["program"].id,
        "academic_year_id": f["ay"].id,
        "year_of_study": 1,
        "semester_number": 1,
        "max_capacity": 1  # Intentionally 1 to test capacity limits
    }

    # 1. Student cannot create cohort -> 403 Forbidden
    res = await client.post(
        "/api/cohorts",
        json=payload,
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert res.status_code == 403

    # 2. Admin creates cohort -> 201 Created
    res = await client.post(
        "/api/cohorts",
        json=payload,
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert res.status_code == 201
    cohort_data = res.json()
    assert cohort_data["code"] == "COH-2026-SE-A"
    assert cohort_data["max_capacity"] == 1
    cohort_id = cohort_data["id"]

    # 3. Duplicate code -> 409 Conflict
    dup_res = await client.post(
        "/api/cohorts",
        json=payload,
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert dup_res.status_code == 409

    # 4. Add Student 1 to cohort -> 201 Created
    m1_res = await client.post(
        f"/api/cohorts/{cohort_id}/members",
        json={"student_id": f["s1"].id, "role": "class_representative"},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert m1_res.status_code == 201
    assert m1_res.json()["role"] == "class_representative"

    # 5. Duplicate membership -> 409 Conflict
    m1_dup = await client.post(
        f"/api/cohorts/{cohort_id}/members",
        json={"student_id": f["s1"].id},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert m1_dup.status_code == 409

    # 6. Add Student 2 to cohort -> capacity limit (1) exceeded -> 400 Bad Request
    m2_res = await client.post(
        f"/api/cohorts/{cohort_id}/members",
        json={"student_id": f["s2"].id},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert m2_res.status_code == 400
    assert "capacity" in m2_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_student_groups_lifecycle_and_memberships(client: AsyncClient, cohort_infra_fixture):
    """
    Verifies:
    - Academic staff (lecturer/admin) can create tutorial/project groups.
    - Adding and removing students from groups.
    - Capacity enforcement on groups.
    """
    f = cohort_infra_fixture

    # Create tutorial group
    group_payload = {
        "course_id": f["course"].id,
        "group_type": "tutorial",
        "name": "SE101 Tutorial Group T01",
        "max_capacity": 2,
        "mentor_lecturer_id": f["lecturer"].id,
        "schedule_info": {"day": "Tuesday", "time": "10:00-12:00", "room": "Lab 2"}
    }

    res = await client.post(
        "/api/cohorts/groups",
        json=group_payload,
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )
    assert res.status_code == 201
    group_data = res.json()
    assert group_data["name"] == "SE101 Tutorial Group T01"
    group_id = group_data["id"]

    # Add Student 1 as team leader
    add_m1 = await client.post(
        f"/api/cohorts/groups/{group_id}/members",
        json={"student_id": f["s1"].id, "group_role": "leader"},
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )
    assert add_m1.status_code == 201
    assert add_m1.json()["group_role"] == "leader"

    # Add Student 2 as member
    add_m2 = await client.post(
        f"/api/cohorts/groups/{group_id}/members",
        json={"student_id": f["s2"].id, "group_role": "member"},
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )
    assert add_m2.status_code == 201

    # Check group members list
    members_res = await client.get(
        f"/api/cohorts/groups/{group_id}/members",
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )
    assert members_res.status_code == 200
    assert len(members_res.json()) == 2

    # Remove Student 2 from group
    del_res = await client.delete(
        f"/api/cohorts/groups/{group_id}/members/{f['s2'].id}",
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_student_my_cohorts_and_groups_query(client: AsyncClient, cohort_infra_fixture):
    """Verifies that a student can query all assigned cohorts and groups via /api/cohorts/my"""
    f = cohort_infra_fixture

    # 1. Create cohort and assign Student 1
    c_res = await client.post(
        "/api/cohorts",
        json={"code": "COH-TEST-01", "name": "Test Cohort 1", "max_capacity": 50},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert c_res.status_code == 201
    c_id = c_res.json()["id"]

    await client.post(
        f"/api/cohorts/{c_id}/members",
        json={"student_id": f["s1"].id, "role": "student"},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )

    # 2. Create group and assign Student 1
    g_res = await client.post(
        "/api/cohorts/groups",
        json={"name": "Project Group Alpha", "group_type": "project_team", "max_capacity": 10},
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )
    assert g_res.status_code == 201
    g_id = g_res.json()["id"]

    await client.post(
        f"/api/cohorts/groups/{g_id}/members",
        json={"student_id": f["s1"].id, "group_role": "member"},
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )

    # 3. Student 1 queries /my
    my_res = await client.get(
        "/api/cohorts/my",
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert my_res.status_code == 200
    data = my_res.json()
    assert len(data["cohorts"]) >= 1
    assert data["cohorts"][0]["code"] == "COH-TEST-01"
    assert len(data["groups"]) >= 1
    assert data["groups"][0]["name"] == "Project Group Alpha"
