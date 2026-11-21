"""
NSBM EduSphere — Academic Records and Transcript Management Tests
Validates grade posting, deterministic GPA/CGPA computation, academic standing auditing,
official transcript issuance, and public cryptographic verification.
"""
import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    User, UserRole, Institution, Program, Course, Semester, AcademicYear,
    Student, Lecturer, Grade, AcademicTermRecord, OfficialTranscript
)
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def academic_records_fixture(test_session: AsyncSession):
    """Sets up institution, program, semester, courses, lecturer, and students"""
    inst = Institution(name="NSBM University", code="NSBM-REC", is_active=True)
    test_session.add(inst)
    await test_session.commit()
    await test_session.refresh(inst)

    prog = Program(institution_id=inst.id, code="BSc-SE", name="BSc in Software Engineering", qualification="BSc")
    ay = AcademicYear(institution_id=inst.id, code="AY2026", name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    test_session.add_all([prog, ay])
    await test_session.commit()
    await test_session.refresh(prog)
    await test_session.refresh(ay)

    sem1 = Semester(
        institution_id=inst.id,
        academic_year_id=ay.id,
        code="SEM-1",
        name="Semester 1",
        term_number=1,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 5, 30),
        is_current=True
    )
    test_session.add(sem1)
    await test_session.commit()
    await test_session.refresh(sem1)

    # Users: Admin/Registrar, Lecturer, Student 1, Student 2
    admin_u = User(username="reg_officer", email="registrar@nsbm.ac.lk", full_name="Registrar Officer", hashed_password=hash_password("Pass@123"), role=UserRole.REGISTRAR, institution_id=inst.id, is_active=True)
    lec_u = User(username="prof_jones", email="jones@nsbm.ac.lk", full_name="Prof. Indiana Jones", hashed_password=hash_password("Pass@123"), role=UserRole.LECTURER, institution_id=inst.id, is_active=True)
    s1_u = User(username="rec_stu1", email="stu1@nsbm.ac.lk", full_name="Kasun Perera", hashed_password=hash_password("Pass@123"), role=UserRole.STUDENT, institution_id=inst.id, is_active=True)
    s2_u = User(username="rec_stu2", email="stu2@nsbm.ac.lk", full_name="Amali Silva", hashed_password=hash_password("Pass@123"), role=UserRole.STUDENT, institution_id=inst.id, is_active=True)
    test_session.add_all([admin_u, lec_u, s1_u, s2_u])
    await test_session.commit()
    for u in [admin_u, lec_u, s1_u, s2_u]:
        await test_session.refresh(u)

    lec = Lecturer(user_id=lec_u.id, institution_id=inst.id, lecturer_id="LEC-REC-01", faculty="Computing", department="SE")
    s1 = Student(user_id=s1_u.id, institution_id=inst.id, student_id="REC-STU-001", faculty="Computing", department="SE", program="BSc-SE", year_of_study=1, semester=1)
    s2 = Student(user_id=s2_u.id, institution_id=inst.id, student_id="REC-STU-002", faculty="Computing", department="SE", program="BSc-SE", year_of_study=1, semester=1)
    test_session.add_all([lec, s1, s2])
    await test_session.commit()
    await test_session.refresh(lec)
    await test_session.refresh(s1)
    await test_session.refresh(s2)

    # Courses
    c1 = Course(institution_id=inst.id, course_code="SE101", title="Software Engineering", credits=3, faculty="Computing", department="SE", semester=1, year=2026, lecturer_id=lec.id)
    c2 = Course(institution_id=inst.id, course_code="SE102", title="Data Structures", credits=4, faculty="Computing", department="SE", semester=1, year=2026, lecturer_id=lec.id)
    test_session.add_all([c1, c2])
    await test_session.commit()
    await test_session.refresh(c1)
    await test_session.refresh(c2)

    return {
        "inst": inst,
        "semester": sem1,
        "c1": c1,
        "c2": c2,
        "lec": lec,
        "s1": s1,
        "s2": s2,
        "admin_token": create_access_token({"sub": str(admin_u.id), "role": admin_u.role.value}),
        "lecturer_token": create_access_token({"sub": str(lec_u.id), "role": lec_u.role.value}),
        "s1_token": create_access_token({"sub": str(s1_u.id), "role": s1_u.role.value}),
        "s2_token": create_access_token({"sub": str(s2_u.id), "role": s2_u.role.value}),
    }


@pytest.mark.asyncio
async def test_grade_posting_and_automatic_letter_conversion(client: AsyncClient, academic_records_fixture):
    """Verifies grade posting, automatic score-to-letter conversion, and credit accumulation"""
    f = academic_records_fixture

    # 1. Student attempting to post grades -> 403 Forbidden
    res = await client.post(
        "/api/academic-records/grades",
        json={"student_id": f["s1"].id, "course_id": f["c1"].id, "total": 86.0},
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert res.status_code == 403

    # 2. Lecturer posts grade with total score 86.0 -> automatically converts to 'A' and 4.0 points
    post_res = await client.post(
        "/api/academic-records/grades",
        json={
            "student_id": f["s1"].id,
            "course_id": f["c1"].id,
            "semester_id": f["semester"].id,
            "total": 86.0,
            "remarks": "Excellent project and examination performance."
        },
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )
    assert post_res.status_code == 201
    g = post_res.json()
    assert g["letter_grade"] == "A"
    assert g["grade_points"] == 4.0
    assert g["total"] == 86.0


@pytest.mark.asyncio
async def test_deterministic_gpa_cgpa_and_standing_calculation(client: AsyncClient, academic_records_fixture):
    """
    Verifies deterministic GPA engine calculation:
    - Course 1 (3 cr): A (4.0) -> QP = 12.0
    - Course 2 (4 cr): B (3.0) -> QP = 12.0
    - Total QP = 24.0, Total Attempted = 7, Total Earned = 7
    - Expected GPA = round(24.0 / 7, 2) = 3.43
    - Evaluated standing: good_standing
    """
    f = academic_records_fixture

    # Post Course 1 grade: 3 credits, A (4.0)
    await client.post(
        "/api/academic-records/grades",
        json={"student_id": f["s1"].id, "course_id": f["c1"].id, "semester_id": f["semester"].id, "letter_grade": "A", "grade_points": 4.0, "total": 85.0},
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )

    # Post Course 2 grade: 4 credits, B (3.0)
    await client.post(
        "/api/academic-records/grades",
        json={"student_id": f["s1"].id, "course_id": f["c2"].id, "semester_id": f["semester"].id, "letter_grade": "B", "grade_points": 3.0, "total": 72.0},
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )

    # Calculate Term GPA
    calc_res = await client.post(
        "/api/academic-records/calculate-term-gpa",
        params={"student_id": f["s1"].id, "semester_id": f["semester"].id},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert calc_res.status_code == 200
    calc = calc_res.json()
    assert calc["term_gpa"] == 3.43
    assert calc["cgpa"] == 3.43
    assert calc["credits_attempted"] == 7
    assert calc["credits_earned"] == 7
    assert calc["academic_standing"] == "good_standing"
    assert len(calc["course_grades"]) == 2


@pytest.mark.asyncio
async def test_official_transcript_issuance_and_public_verification(client: AsyncClient, academic_records_fixture):
    """
    Verifies:
    - Official transcript issuance with cryptographic digital signature.
    - Public / third-party transcript verification endpoint.
    - Rejection of invalid verification tokens.
    """
    f = academic_records_fixture

    # Post passing grade
    await client.post(
        "/api/academic-records/grades",
        json={"student_id": f["s1"].id, "course_id": f["c1"].id, "semester_id": f["semester"].id, "letter_grade": "A", "grade_points": 4.0, "total": 88.0},
        headers={"Authorization": f"Bearer {f['lecturer_token']}"}
    )

    # Issue Official Transcript
    issue_res = await client.post(
        "/api/academic-records/transcript/issue",
        json={"student_id": f["s1"].id, "recipient_name": "Stanford University Graduate Admissions", "issue_type": "official"},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert issue_res.status_code == 201
    t = issue_res.json()
    assert t["status"] == "valid"
    assert len(t["verification_code"]) > 10
    assert len(t["digital_signature_hash"]) == 64  # SHA-256
    v_code = t["verification_code"]

    # Public verification of transcript
    verify_res = await client.get(f"/api/academic-records/transcript/verify/{v_code}")
    assert verify_res.status_code == 200
    v = verify_res.json()
    assert v["is_valid"] is True
    assert v["student_name"] == "Kasun Perera"
    assert v["student_id"] == "REC-STU-001"
    assert v["verification_code"] == v_code

    # Invalid code verification -> 404
    invalid_verify = await client.get("/api/academic-records/transcript/verify/NON-EXISTENT-CODE")
    assert invalid_verify.status_code == 404


@pytest.mark.asyncio
async def test_transcript_student_privacy_and_access_control(client: AsyncClient, academic_records_fixture):
    """Verifies that students can view their own transcript, but cannot access peer records (BOLA defense)"""
    f = academic_records_fixture

    # Student 1 views own transcript -> 200 OK
    s1_view = await client.get(
        f"/api/academic-records/transcript/student/{f['s1'].id}",
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert s1_view.status_code == 200
    assert s1_view.json()["student_id"] == "REC-STU-001"

    # Student 2 tries to view Student 1's transcript -> 403 Forbidden
    s2_view = await client.get(
        f"/api/academic-records/transcript/student/{f['s1'].id}",
        headers={"Authorization": f"Bearer {f['s2_token']}"}
    )
    assert s2_view.status_code == 403
