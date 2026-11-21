from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    Assignment, AssignmentSubmission, AssignmentStatus,
    Quiz, QuizAttempt,
    GradebookCategory, GradeScale, GradebookOverride
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_gradebook_and_calculation_engine(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Student A, Student B, Outsider Student
    admin_user = User(
        email="gradebook_admin@nsbm.ac.lk",
        username="gradebook_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Academic Registrar",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="gradebook_lecturer@nsbm.ac.lk",
        username="gradebook_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Dr. Claude Shannon",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_a_user = User(
        email="student_a@nsbm.ac.lk",
        username="student_a",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Alice Lovelace",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_a_user)

    student_b_user = User(
        email="student_b@nsbm.ac.lk",
        username="student_b",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Bob Turing",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_b_user)

    outsider_user = User(
        email="gradebook_outsider@nsbm.ac.lk",
        username="gradebook_outsider",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Charlie Outsider",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(outsider_user)
    await test_session.commit()

    # Profiles
    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-GBK-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add(lecturer)

    student_a = Student(
        user_id=student_a_user.id,
        student_id="STU-GBK-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=2,
        semester=2,
    )
    test_session.add(student_a)

    student_b = Student(
        user_id=student_b_user.id,
        student_id="STU-GBK-02",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=2,
        semester=2,
    )
    test_session.add(student_b)

    outsider = Student(
        user_id=outsider_user.id,
        student_id="STU-GBK-03",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=2,
        semester=2,
    )
    test_session.add(outsider)
    await test_session.commit()

    # Course & Enrollments
    course = Course(
        course_code="CS310",
        title="Information Theory & Coding",
        description="Entropy, source coding, channel capacity.",
        credits=3,
        faculty="Computing",
        department="Computer Science",
        semester=2,
        year=2,
        lecturer_id=lecturer.id,
    )
    test_session.add(course)
    await test_session.commit()

    enr_a = Enrollment(student_id=student_a.id, course_id=course.id, status="enrolled")
    enr_b = Enrollment(student_id=student_b.id, course_id=course.id, status="enrolled")
    test_session.add_all([enr_a, enr_b])
    await test_session.commit()

    # Auth headers
    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": lecturer_user.role.value})
    student_a_token = create_access_token({"sub": str(student_a_user.id), "role": student_a_user.role.value})
    student_b_token = create_access_token({"sub": str(student_b_user.id), "role": student_b_user.role.value})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}
    student_a_headers = {"Authorization": f"Bearer {student_a_token}"}
    student_b_headers = {"Authorization": f"Bearer {student_b_token}"}

    # ─── 2. Category Configuration Tests ──────────────────────────────────────────
    # Student cannot create category
    res_stud_cat = await client.post(
        f"/api/courses/{course.id}/gradebook/categories",
        json={"name": "Labs", "weight_percentage": 20.0, "drop_lowest_count": 0},
        headers=student_a_headers
    )
    assert res_stud_cat.status_code == 403

    # Lecturer configures "Assignments" (50% weight, drop 1 lowest)
    res_cat1 = await client.post(
        f"/api/courses/{course.id}/gradebook/categories",
        json={"name": "Assignments", "weight_percentage": 50.0, "drop_lowest_count": 1},
        headers=lecturer_headers
    )
    assert res_cat1.status_code == 201
    cat_assignments = res_cat1.json()
    assert cat_assignments["name"] == "Assignments"
    assert cat_assignments["weight_percentage"] == 50.0
    assert cat_assignments["drop_lowest_count"] == 1
    cat_asg_id = cat_assignments["id"]

    # Lecturer configures "Quizzes" (50% weight, drop 0)
    res_cat2 = await client.post(
        f"/api/courses/{course.id}/gradebook/categories",
        json={"name": "Quizzes", "weight_percentage": 50.0, "drop_lowest_count": 0},
        headers=lecturer_headers
    )
    assert res_cat2.status_code == 201
    cat_quizzes = res_cat2.json()
    cat_quiz_id = cat_quizzes["id"]

    # Exceeding 100% total weight rejected
    res_cat_overflow = await client.post(
        f"/api/courses/{course.id}/gradebook/categories",
        json={"name": "Final Exam", "weight_percentage": 10.0, "drop_lowest_count": 0},
        headers=lecturer_headers
    )
    assert res_cat_overflow.status_code == 400

    # ─── 3. Assignments & Quizzes Setup ──────────────────────────────────────────
    now = datetime.utcnow()
    # Assignment 1 & 2 in Assignments category
    asg1 = Assignment(
        course_id=course.id,
        title="Huffman Coding Lab",
        max_marks=100.0,
        due_date=now + timedelta(days=5),
        category_id=cat_asg_id,
        status="published",
    )
    asg2 = Assignment(
        course_id=course.id,
        title="Shannon Entropy Proof",
        max_marks=100.0,
        due_date=now + timedelta(days=10),
        category_id=cat_asg_id,
        status="published",
    )
    # Quiz 1 in Quizzes category
    quiz1 = Quiz(
        course_id=course.id,
        title="Source Coding Quiz",
        total_points=50.0,
        due_date=now + timedelta(days=7),
        category_id=cat_quiz_id,
        status="published",
    )
    test_session.add_all([asg1, asg2, quiz1])
    await test_session.commit()

    # Submissions for Student A:
    # Asg 1: 60/100 (will be dropped as lowest!)
    # Asg 2: 80/100
    sub_a1 = AssignmentSubmission(
        assignment_id=asg1.id,
        student_id=student_a.id,
        marks=60.0,
        status=AssignmentStatus.GRADED,
    )
    sub_a2 = AssignmentSubmission(
        assignment_id=asg2.id,
        student_id=student_a.id,
        marks=80.0,
        status=AssignmentStatus.GRADED,
    )
    # Quiz 1 for Student A: 45/50 (90%)
    att_a1 = QuizAttempt(
        quiz_id=quiz1.id,
        student_id=student_a.id,
        attempt_number=1,
        total_score=45.0,
        max_score=50.0,
        percentage=90.0,
        is_passed=True,
        status="graded",
    )

    # Submissions for Student B:
    # Asg 1: 90/100
    # Asg 2: 85/100 (85 will be dropped as lowest for B)
    # Quiz 1: 40/50 (80%)
    sub_b1 = AssignmentSubmission(
        assignment_id=asg1.id,
        student_id=student_b.id,
        marks=90.0,
        status=AssignmentStatus.GRADED,
    )
    sub_b2 = AssignmentSubmission(
        assignment_id=asg2.id,
        student_id=student_b.id,
        marks=85.0,
        status=AssignmentStatus.GRADED,
    )
    att_b1 = QuizAttempt(
        quiz_id=quiz1.id,
        student_id=student_b.id,
        attempt_number=1,
        total_score=40.0,
        max_score=50.0,
        percentage=80.0,
        is_passed=True,
        status="graded",
    )

    test_session.add_all([sub_a1, sub_a2, att_a1, sub_b1, sub_b2, att_b1])
    await test_session.commit()

    # ─── 4. Full Course Gradebook Calculation Tests ───────────────────────────────
    # Student cannot view full course gradebook
    res_stud_gb = await client.get(
        f"/api/courses/{course.id}/gradebook",
        headers=student_a_headers
    )
    assert res_stud_gb.status_code == 403

    # Lecturer views full gradebook
    res_gb = await client.get(
        f"/api/courses/{course.id}/gradebook",
        headers=lecturer_headers
    )
    assert res_gb.status_code == 200
    gb_data = res_gb.json()
    assert gb_data["course_code"] == "CS310"
    assert gb_data["total_enrolled"] == 2
    assert len(gb_data["students"]) == 2

    # Check Student A's calculation:
    # Asg dropped = 60, remaining = 80 (80% * 0.5 = 40.0)
    # Quiz = 45/50 (90% * 0.5 = 45.0)
    # Total percentage = 85.0% -> Letter grade "A", GPA 4.0
    student_a_rec = next(s for s in gb_data["students"] if s["student_id"] == student_a.id)
    assert student_a_rec["calculated_percentage"] == 85.0
    assert student_a_rec["letter_grade"] == "A"
    assert student_a_rec["gpa_points"] == 4.0
    assert student_a_rec["final_percentage"] == 85.0

    # Verify dropped item on Student A
    asg_cat_summary = next(c for c in student_a_rec["category_scores"] if c["category_name"] == "Assignments")
    dropped_items = [it for it in asg_cat_summary["items"] if it["is_dropped"]]
    assert len(dropped_items) == 1
    assert dropped_items[0]["score"] == 60.0

    # ─── 5. Student Self-Service Grade View Tests ─────────────────────────────────
    # Student A views own summary
    res_self = await client.get(
        f"/api/courses/{course.id}/gradebook/student/{student_a.id}",
        headers=student_a_headers
    )
    assert res_self.status_code == 200
    self_data = res_self.json()
    assert self_data["calculated_percentage"] == 85.0
    assert self_data["letter_grade"] == "A"

    # Student B cannot view Student A's summary
    res_unauth = await client.get(
        f"/api/courses/{course.id}/gradebook/student/{student_a.id}",
        headers=student_b_headers
    )
    assert res_unauth.status_code == 403

    # ─── 6. Grade Override Tests ──────────────────────────────────────────────────
    # Lecturer applies grade override to Student B
    res_override = await client.post(
        f"/api/courses/{course.id}/gradebook/override",
        json={
            "student_id": student_b.id,
            "overridden_percentage": 95.0,
            "overridden_letter_grade": "A+",
            "overridden_gpa_points": 4.0,
            "override_reason": "Exceptional open-source contribution to consensus library."
        },
        headers=lecturer_headers
    )
    assert res_override.status_code == 200
    ov_data = res_override.json()
    assert ov_data["overridden_percentage"] == 95.0
    assert ov_data["overridden_letter_grade"] == "A+"

    # Verify updated gradebook reflects override for Student B
    res_gb2 = await client.get(
        f"/api/courses/{course.id}/gradebook",
        headers=lecturer_headers
    )
    assert res_gb2.status_code == 200
    student_b_rec = next(s for s in res_gb2.json()["students"] if s["student_id"] == student_b.id)
    assert student_b_rec["is_overridden"] is True
    assert student_b_rec["final_percentage"] == 95.0
    assert student_b_rec["final_letter_grade"] == "A+"
    assert student_b_rec["final_gpa_points"] == 4.0

    # ─── 7. Gradebook Export Tests ────────────────────────────────────────────────
    # JSON export
    res_exp_json = await client.get(
        f"/api/courses/{course.id}/gradebook/export?export_format=json",
        headers=lecturer_headers
    )
    assert res_exp_json.status_code == 200
    json_data = res_exp_json.json()
    assert json_data["format"] == "json"
    assert json_data["records_count"] == 2
    assert len(json_data["data"]) == 2

    # CSV export
    res_exp_csv = await client.get(
        f"/api/courses/{course.id}/gradebook/export?export_format=csv",
        headers=lecturer_headers
    )
    assert res_exp_csv.status_code == 200
    assert "text/csv" in res_exp_csv.headers["content-type"]
    assert "student_number" in res_exp_csv.text
    assert "Alice Lovelace" in res_exp_csv.text
