from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    Assignment, AssignmentSubmission
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_academic_integrity_and_plagiarism_checks_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Student 1, Student 2, Student 3, and Outsider
    admin_user = User(
        email="plag_admin@nsbm.ac.lk",
        username="plag_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Academic Integrity Officer",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="plag_lecturer@nsbm.ac.lk",
        username="plag_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Leslie Lamport",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_1_user = User(
        email="plag_student1@nsbm.ac.lk",
        username="plag_student1",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Alice Author",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_1_user)

    student_2_user = User(
        email="plag_student2@nsbm.ac.lk",
        username="plag_student2",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Bob Colluder",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_2_user)

    student_3_user = User(
        email="plag_student3@nsbm.ac.lk",
        username="plag_student3",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Charlie Original",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_3_user)

    outsider_user = User(
        email="plag_outsider@nsbm.ac.lk",
        username="plag_outsider",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Outsider Johnson",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(outsider_user)
    await test_session.commit()

    # Profiles
    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-PLG-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add(lecturer)

    s1 = Student(
        user_id=student_1_user.id,
        student_id="STU-PLG-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=3,
        semester=1,
    )
    test_session.add(s1)

    s2 = Student(
        user_id=student_2_user.id,
        student_id="STU-PLG-02",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=3,
        semester=1,
    )
    test_session.add(s2)

    s3 = Student(
        user_id=student_3_user.id,
        student_id="STU-PLG-03",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=3,
        semester=1,
    )
    test_session.add(s3)

    outsider = Student(
        user_id=outsider_user.id,
        student_id="STU-PLG-04",
        faculty="Business",
        department="Law",
        program="BSc Law",
        year_of_study=1,
        semester=1,
    )
    test_session.add(outsider)
    await test_session.commit()

    # Course
    course = Course(
        course_code="CS420",
        title="Distributed Systems Foundations",
        description="Formal proofs and consensus mechanisms.",
        credits=4,
        faculty="Computing",
        department="Computer Science",
        semester=1,
        year=3,
        lecturer_id=lecturer.id,
    )
    test_session.add(course)
    await test_session.commit()

    # Enrollments
    test_session.add(Enrollment(student_id=s1.id, course_id=course.id, status="active"))
    test_session.add(Enrollment(student_id=s2.id, course_id=course.id, status="active"))
    test_session.add(Enrollment(student_id=s3.id, course_id=course.id, status="active"))

    # Assignment
    now = datetime.utcnow()
    assignment = Assignment(
        course_id=course.id,
        creator_id=lecturer_user.id,
        title="Consensus Protocol Comparative Research Paper",
        description="Submit an analytical essay evaluating Paxos vs Raft consensus.",
        due_date=now + timedelta(days=7),
        status="published",
    )
    test_session.add(assignment)
    await test_session.commit()

    # Submissions
    sub_1 = AssignmentSubmission(
        assignment_id=assignment.id,
        student_id=s1.id,
        text_content="Distributed consensus protocols like Raft decompose state machine replication into leader election, log replication, and safety invariants. In Raft, the elected leader has complete authority over client command log replication and commits only after majority quorum confirmation across nodes.",
    )
    test_session.add(sub_1)

    sub_2 = AssignmentSubmission(
        assignment_id=assignment.id,
        student_id=s2.id,
        text_content="Distributed consensus protocols like Raft decompose state machine replication into leader election, log replication, and safety invariants. In Raft, the elected leader has authority over client command log replication and commits after majority quorum confirmation across nodes.",
    )
    test_session.add(sub_2)

    sub_3 = AssignmentSubmission(
        assignment_id=assignment.id,
        student_id=s3.id,
        text_content="Quantum key distribution relies on Heisenberg uncertainty principle to establish cryptographically secure symmetric keys over optical fiber networks with entangled photon pairs.",
    )
    test_session.add(sub_3)
    await test_session.commit()

    # Auth tokens
    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": lecturer_user.role.value})
    student_1_token = create_access_token({"sub": str(student_1_user.id), "role": student_1_user.role.value})
    student_2_token = create_access_token({"sub": str(student_2_user.id), "role": student_2_user.role.value})
    outsider_token = create_access_token({"sub": str(outsider_user.id), "role": outsider_user.role.value})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}
    student_1_headers = {"Authorization": f"Bearer {student_1_token}"}
    student_2_headers = {"Authorization": f"Bearer {student_2_token}"}
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    # 2. Student cannot trigger plagiarism scans -> 403 Forbidden
    r = await client.post(f"/api/assignments/{assignment.id}/submissions/{sub_2.id}/plagiarism-scan", headers=student_2_headers)
    assert r.status_code == 403

    # 3. Lecturer triggers scan on sub_2 (colluder)
    r = await client.post(f"/api/assignments/{assignment.id}/submissions/{sub_2.id}/plagiarism-scan", headers=lecturer_headers)
    assert r.status_code == 200
    report_2 = r.json()
    report_id = report_2["id"]
    assert report_2["submission_id"] == sub_2.id
    assert report_2["similarity_score"] > 60.0  # High similarity with sub_1
    assert report_2["integrity_flag"] == "flagged"
    assert len(report_2["matched_sources"]) == 1
    assert report_2["matched_sources"][0]["source_submission_id"] == sub_1.id

    # Verify submission originality score updated
    await test_session.refresh(sub_2)
    assert sub_2.originality_score is not None
    assert sub_2.originality_score < 40.0

    # 4. Student 2 can view own plagiarism report
    r = await client.get(f"/api/submissions/{sub_2.id}/plagiarism-report", headers=student_2_headers)
    assert r.status_code == 200
    assert r.json()["similarity_score"] > 60.0

    # 5. Outsider cannot view the report -> 403 Forbidden
    r = await client.get(f"/api/submissions/{sub_2.id}/plagiarism-report", headers=outsider_headers)
    assert r.status_code == 403

    # 6. Lecturer runs bulk scan on the entire assignment
    r = await client.post(f"/api/assignments/{assignment.id}/plagiarism-scan-all", headers=lecturer_headers)
    assert r.status_code == 200
    bulk_result = r.json()
    assert bulk_result["submissions_scanned"] == 3
    assert bulk_result["flagged_count"] >= 2  # sub_1 and sub_2 match each other
    assert bulk_result["clean_count"] == 1    # sub_3 is clean quantum text

    # 7. Check sub_3 (clean student) report
    r = await client.get(f"/api/submissions/{sub_3.id}/plagiarism-report", headers=lecturer_headers)
    assert r.status_code == 200
    assert r.json()["similarity_score"] == 0.0
    assert r.json()["integrity_flag"] == "clean"

    # 8. Lecturer conducts review and resolves report
    review_payload = {
        "integrity_flag": "resolved",
        "instructor_notes": "Identified as authorized pair-programming research assignment with proper attribution."
    }
    r = await client.post(f"/api/plagiarism-reports/{report_id}/review", json=review_payload, headers=lecturer_headers)
    assert r.status_code == 200
    reviewed_report = r.json()
    assert reviewed_report["integrity_flag"] == "resolved"
    assert "authorized pair-programming" in reviewed_report["instructor_notes"]
    assert reviewed_report["reviewed_by_id"] == lecturer_user.id
