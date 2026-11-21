"""
NSBM EduSphere — Course Registration and Enrollment Workflows Tests
Validates course registration, prerequisite enforcement, capacity limits,
automated waitlisting, waitlist promotion on drops, and role-based permissions.
"""
import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    User, UserRole, Institution, Campus, Program, Faculty, Department,
    Course, CoursePrerequisite, Semester, AcademicYear, Student, Enrollment, Grade
)
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def enrollment_infra_fixture(test_session: AsyncSession):
    """Sets up institution, academic terms, courses with prerequisites, and student accounts"""
    inst = Institution(name="NSBM University", code="NSBM-ENR", is_active=True)
    test_session.add(inst)
    await test_session.commit()
    await test_session.refresh(inst)

    ay = AcademicYear(institution_id=inst.id, code="AY2026", name="Academic Year 2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), is_current=True)
    test_session.add(ay)
    await test_session.commit()
    await test_session.refresh(ay)

    today = date.today()
    sem = Semester(
        institution_id=inst.id,
        academic_year_id=ay.id,
        code="SEM-2026-1",
        name="Semester 1 2026",
        term_number=1,
        start_date=today - timedelta(days=10),
        end_date=today + timedelta(days=90),
        registration_start_date=today - timedelta(days=20),
        registration_end_date=today + timedelta(days=30),
        add_drop_deadline=today + timedelta(days=14),
        is_current=True
    )
    test_session.add(sem)
    await test_session.commit()
    await test_session.refresh(sem)

    # Courses: Intro to Programming (PREREQ) -> Data Structures (ADVANCED)
    course_intro = Course(
        institution_id=inst.id,
        course_code="CS101",
        title="Introduction to Programming",
        credits=3,
        faculty="Computing",
        department="Software Engineering",
        semester=1,
        year=2026,
        max_students=50,
        is_active=True
    )
    course_advanced = Course(
        institution_id=inst.id,
        course_code="CS201",
        title="Data Structures and Algorithms",
        credits=4,
        faculty="Computing",
        department="Software Engineering",
        semester=1,
        year=2026,
        max_students=1,  # Small capacity for waitlist testing
        is_active=True
    )
    test_session.add_all([course_intro, course_advanced])
    await test_session.commit()
    await test_session.refresh(course_intro)
    await test_session.refresh(course_advanced)

    # Add prerequisite: CS101 is mandatory for CS201
    prereq = CoursePrerequisite(
        course_id=course_advanced.id,
        prerequisite_course_id=course_intro.id,
        is_mandatory=True,
        minimum_grade="C"
    )
    test_session.add(prereq)
    await test_session.commit()

    # Users: Admin, Student 1, Student 2, Student 3
    admin_u = User(
        username="reg_admin",
        email="admin@nsbm.ac.lk",
        full_name="Registrar Admin",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.ADMIN,
        institution_id=inst.id,
        is_active=True
    )
    s1_u = User(
        username="student_alpha",
        email="alpha@nsbm.ac.lk",
        full_name="Student Alpha",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.STUDENT,
        institution_id=inst.id,
        is_active=True
    )
    s2_u = User(
        username="student_beta",
        email="beta@nsbm.ac.lk",
        full_name="Student Beta",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.STUDENT,
        institution_id=inst.id,
        is_active=True
    )
    s3_u = User(
        username="student_gamma",
        email="gamma@nsbm.ac.lk",
        full_name="Student Gamma",
        hashed_password=hash_password("Pass@123"),
        role=UserRole.STUDENT,
        institution_id=inst.id,
        is_active=True
    )
    test_session.add_all([admin_u, s1_u, s2_u, s3_u])
    await test_session.commit()
    for u in [admin_u, s1_u, s2_u, s3_u]:
        await test_session.refresh(u)

    # Student profiles
    s1 = Student(user_id=s1_u.id, institution_id=inst.id, student_id="STU-001", faculty="Computing", department="SE", program="BSc SE", year_of_study=1, semester=1)
    s2 = Student(user_id=s2_u.id, institution_id=inst.id, student_id="STU-002", faculty="Computing", department="SE", program="BSc SE", year_of_study=1, semester=1)
    s3 = Student(user_id=s3_u.id, institution_id=inst.id, student_id="STU-003", faculty="Computing", department="SE", program="BSc SE", year_of_study=1, semester=1)
    test_session.add_all([s1, s2, s3])
    await test_session.commit()
    await test_session.refresh(s1)
    await test_session.refresh(s2)
    await test_session.refresh(s3)

    return {
        "inst": inst,
        "semester": sem,
        "course_intro": course_intro,
        "course_advanced": course_advanced,
        "admin": admin_u,
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "admin_token": create_access_token({"sub": str(admin_u.id), "role": admin_u.role.value}),
        "s1_token": create_access_token({"sub": str(s1_u.id), "role": s1_u.role.value}),
        "s2_token": create_access_token({"sub": str(s2_u.id), "role": s2_u.role.value}),
        "s3_token": create_access_token({"sub": str(s3_u.id), "role": s3_u.role.value}),
    }


@pytest.mark.asyncio
async def test_course_registration_prerequisite_enforcement(client: AsyncClient, test_session: AsyncSession, enrollment_infra_fixture):
    """Verifies that attempting to register for a course without passing prerequisites is rejected with 400"""
    f = enrollment_infra_fixture

    # Student 1 attempts to register directly for CS201 (prerequisite CS101 not yet completed) -> 400
    res = await client.post(
        "/api/enrollments/register",
        json={"course_id": f["course_advanced"].id, "semester_id": f["semester"].id},
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert res.status_code == 400
    assert "prerequisite" in res.json()["detail"].lower()

    # Now assign passing grade in CS101 to Student 1
    grade = Grade(
        student_id=f["s1"].id,
        course_id=f["course_intro"].id,
        letter_grade="A",
        grade_points=4.0,
        total=85.0
    )
    test_session.add(grade)
    await test_session.commit()

    # Retry registration for CS201 -> 201 Created
    success_res = await client.post(
        "/api/enrollments/register",
        json={"course_id": f["course_advanced"].id, "semester_id": f["semester"].id},
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert success_res.status_code == 201
    assert success_res.json()["status"] == "active"
    assert success_res.json()["waitlist_position"] is None


@pytest.mark.asyncio
async def test_capacity_limits_waitlist_and_promotion_flow(client: AsyncClient, test_session: AsyncSession, enrollment_infra_fixture):
    """
    Verifies:
    - First student gets active enrollment.
    - Subsequent students exceed capacity (max_students=1) and are assigned sequential waitlist positions.
    - Dropping active enrollment automatically promotes top waitlisted student to active.
    """
    f = enrollment_infra_fixture

    # Give all 3 students passing grades for the prerequisite CS101
    for s in [f["s1"], f["s2"], f["s3"]]:
        test_session.add(Grade(student_id=s.id, course_id=f["course_intro"].id, letter_grade="B", grade_points=3.0, total=70.0))
    await test_session.commit()

    # 1. Student 1 registers for CS201 (capacity: 1) -> active
    r1 = await client.post(
        "/api/enrollments/register",
        json={"course_id": f["course_advanced"].id, "semester_id": f["semester"].id},
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert r1.status_code == 201
    e1 = r1.json()
    assert e1["status"] == "active"
    assert e1["waitlist_position"] is None

    # Duplicate registration check for Student 1 -> 409 Conflict
    dup = await client.post(
        "/api/enrollments/register",
        json={"course_id": f["course_advanced"].id, "semester_id": f["semester"].id},
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert dup.status_code == 409

    # 2. Student 2 registers for CS201 -> full! -> waitlisted at position 1
    r2 = await client.post(
        "/api/enrollments/register",
        json={"course_id": f["course_advanced"].id, "semester_id": f["semester"].id},
        headers={"Authorization": f"Bearer {f['s2_token']}"}
    )
    assert r2.status_code == 201
    e2 = r2.json()
    assert e2["status"] == "waitlisted"
    assert e2["waitlist_position"] == 1

    # 3. Student 3 registers for CS201 -> full! -> waitlisted at position 2
    r3 = await client.post(
        "/api/enrollments/register",
        json={"course_id": f["course_advanced"].id, "semester_id": f["semester"].id},
        headers={"Authorization": f"Bearer {f['s3_token']}"}
    )
    assert r3.status_code == 201
    e3 = r3.json()
    assert e3["status"] == "waitlisted"
    assert e3["waitlist_position"] == 2

    # 4. Student 1 drops the course -> triggers automatic waitlist promotion for Student 2!
    drop_res = await client.post(
        f"/api/enrollments/{e1['id']}/drop",
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert drop_res.status_code == 200
    assert drop_res.json()["status"] == "dropped"

    # 5. Check Student 2 enrollment -> now promoted to 'active'
    s2_list = await client.get(
        "/api/enrollments/my",
        headers={"Authorization": f"Bearer {f['s2_token']}"}
    )
    assert s2_list.status_code == 200
    s2_enr = next(item for item in s2_list.json() if item["id"] == e2["id"])
    assert s2_enr["status"] == "active"
    assert s2_enr["waitlist_position"] is None

    # 6. Check Student 3 enrollment -> waitlist position shifted from 2 to 1
    s3_list = await client.get(
        "/api/enrollments/my",
        headers={"Authorization": f"Bearer {f['s3_token']}"}
    )
    assert s3_list.status_code == 200
    s3_enr = next(item for item in s3_list.json() if item["id"] == e3["id"])
    assert s3_enr["status"] == "waitlisted"
    assert s3_enr["waitlist_position"] == 1


@pytest.mark.asyncio
async def test_enrollment_administrative_actions_and_rbac(client: AsyncClient, test_session: AsyncSession, enrollment_infra_fixture):
    """
    Verifies:
    - Admin can update enrollment status (e.g. approve/reject).
    - Students cannot drop another student's enrollment (403 Forbidden).
    - Invalid status update is rejected with 400.
    """
    f = enrollment_infra_fixture

    # Give Student 1 passing prerequisite grade
    test_session.add(Grade(student_id=f["s1"].id, course_id=f["course_intro"].id, letter_grade="A", grade_points=4.0, total=85.0))
    await test_session.commit()

    reg_res = await client.post(
        "/api/enrollments/register",
        json={"course_id": f["course_intro"].id, "semester_id": f["semester"].id},
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert reg_res.status_code == 201
    enr_id = reg_res.json()["id"]

    # Student 2 tries to drop Student 1's enrollment -> 403 Forbidden
    unauth_drop = await client.post(
        f"/api/enrollments/{enr_id}/drop",
        headers={"Authorization": f"Bearer {f['s2_token']}"}
    )
    assert unauth_drop.status_code == 403

    # Admin updates enrollment status to completed -> 200 OK
    admin_patch = await client.patch(
        f"/api/enrollments/{enr_id}/status",
        json={"status": "completed", "remarks": "Successfully completed term curriculum."},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert admin_patch.status_code == 200
    assert admin_patch.json()["status"] == "completed"

    # Invalid status update -> 400
    invalid_patch = await client.patch(
        f"/api/enrollments/{enr_id}/status",
        json={"status": "non_existent_status"},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert invalid_patch.status_code == 400
