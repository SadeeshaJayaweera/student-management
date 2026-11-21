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
async def test_assignment_submission_and_versioning_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Enrolled Student, and Outsider
    admin_user = User(
        email="sub_admin@nsbm.ac.lk",
        username="sub_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Assessment Registrar",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="sub_lecturer@nsbm.ac.lk",
        username="sub_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Barbara Liskov",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_user = User(
        email="sub_student@nsbm.ac.lk",
        username="sub_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Katherine Johnson",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)

    outsider_user = User(
        email="sub_outsider@nsbm.ac.lk",
        username="sub_outsider",
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
        lecturer_id="LEC-SUB-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add(lecturer)

    student = Student(
        user_id=student_user.id,
        student_id="STU-SUB-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=3,
        semester=1,
    )
    test_session.add(student)

    outsider = Student(
        user_id=outsider_user.id,
        student_id="STU-SUB-02",
        faculty="Business",
        department="Finance",
        program="BSc Finance",
        year_of_study=1,
        semester=1,
    )
    test_session.add(outsider)
    await test_session.commit()

    # Course
    course = Course(
        course_code="CS405",
        title="Concurrent & Distributed Systems",
        description="Concurrency primitives, actor models, and distributed state.",
        credits=4,
        faculty="Computing",
        department="Computer Science",
        semester=1,
        year=3,
        lecturer_id=lecturer.id,
    )
    test_session.add(course)
    await test_session.commit()

    # Enrollment
    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        status="active",
    )
    test_session.add(enrollment)

    # Assignment 1: 2 attempts max, on time
    now = datetime.utcnow()
    assignment = Assignment(
        course_id=course.id,
        creator_id=lecturer_user.id,
        title="Raft Distributed Consensus Implementation",
        description="Implement leader election, log replication, and heartbeat timers.",
        due_date=now + timedelta(days=7),
        available_from=now - timedelta(days=1),
        max_marks=100.0,
        max_attempts=2,
        allow_late_submissions=True,
        late_penalty_percentage_per_day=5.0,
        status="published",
    )
    test_session.add(assignment)

    # Assignment 2: Past due with late submissions initially disallowed
    past_due_assignment = Assignment(
        course_id=course.id,
        creator_id=lecturer_user.id,
        title="Paxos Laboratory Exercise",
        description="Paxos protocol simulation.",
        due_date=now - timedelta(days=2),
        available_from=now - timedelta(days=5),
        max_marks=50.0,
        max_attempts=1,
        allow_late_submissions=False,
        status="published",
    )
    test_session.add(past_due_assignment)
    await test_session.commit()

    # Auth tokens
    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": lecturer_user.role.value})
    student_token = create_access_token({"sub": str(student_user.id), "role": student_user.role.value})
    outsider_token = create_access_token({"sub": str(outsider_user.id), "role": outsider_user.role.value})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    # 2. Outsider student tries to submit attempt -> 403 Forbidden
    attempt_payload_1 = {
        "text_content": "Initial raft node implementation with leader election.",
        "file_url": "https://storage.nsbm.ac.lk/submissions/raft_v1.zip",
        "attachments": [
            {"filename": "raft_node.py", "url": "/files/raft_node.py", "size_bytes": 4096}
        ]
    }
    r = await client.post(f"/api/assignments/{assignment.id}/submissions", json=attempt_payload_1, headers=outsider_headers)
    assert r.status_code == 403

    # 3. Enrolled student submits Attempt 1
    r = await client.post(f"/api/assignments/{assignment.id}/submissions", json=attempt_payload_1, headers=student_headers)
    assert r.status_code == 201
    sub_1 = r.json()
    submission_id = sub_1["id"]
    assert sub_1["attempt_number"] == 1
    assert sub_1["is_late"] is False
    assert sub_1["submission_receipt"].startswith("NSBM-SUB-")
    assert len(sub_1["versions"]) == 1
    assert sub_1["versions"][0]["version_number"] == 1

    # 4. Enrolled student submits Attempt 2 (resubmission)
    attempt_payload_2 = {
        "text_content": "Revised raft node with log compaction and snapshotting.",
        "file_url": "https://storage.nsbm.ac.lk/submissions/raft_v2.zip",
        "attachments": [
            {"filename": "raft_node.py", "url": "/files/raft_node.py", "size_bytes": 6144},
            {"filename": "snapshot.py", "url": "/files/snapshot.py", "size_bytes": 2048}
        ]
    }
    r = await client.post(f"/api/assignments/{assignment.id}/submissions", json=attempt_payload_2, headers=student_headers)
    assert r.status_code == 201
    sub_2 = r.json()
    assert sub_2["id"] == submission_id
    assert sub_2["attempt_number"] == 2
    assert len(sub_2["versions"]) == 2
    assert sub_2["versions"][1]["version_number"] == 2

    # 5. Enrolled student tries Attempt 3 (exceeds max_attempts=2) -> 400 Bad Request
    attempt_payload_3 = {
        "text_content": "Third attempt which should be rejected by policy.",
    }
    r = await client.post(f"/api/assignments/{assignment.id}/submissions", json=attempt_payload_3, headers=student_headers)
    assert r.status_code == 400
    assert "Maximum attempt limit (2) reached" in r.json()["detail"]

    # 6. Student views their own submission with full version history
    r = await client.get(f"/api/assignments/{assignment.id}/submissions/my", headers=student_headers)
    assert r.status_code == 200
    my_sub = r.json()
    assert my_sub["id"] == submission_id
    assert my_sub["attempt_number"] == 2
    assert len(my_sub["versions"]) == 2

    # 7. Student retrieves verifiable digital submission receipt
    r = await client.get(f"/api/submissions/{submission_id}/receipt", headers=student_headers)
    assert r.status_code == 200
    receipt = r.json()
    assert receipt["submission_id"] == submission_id
    assert receipt["submission_receipt"].startswith("NSBM-SUB-")
    assert receipt["course_code"] == "CS405"
    assert receipt["assignment_title"] == "Raft Distributed Consensus Implementation"
    assert receipt["student_name"] == "Katherine Johnson"
    assert receipt["attempt_number"] == 2
    assert len(receipt["verification_hash"]) == 64  # SHA-256

    # 8. Outsider cannot view the receipt -> 403 Forbidden
    r = await client.get(f"/api/submissions/{submission_id}/receipt", headers=outsider_headers)
    assert r.status_code == 403

    # 9. Instructor lists all submissions for the assignment
    r = await client.get(f"/api/assignments/{assignment.id}/submissions", headers=lecturer_headers)
    assert r.status_code == 200
    all_subs = r.json()
    assert len(all_subs) == 1
    assert all_subs[0]["id"] == submission_id

    # 10. Late submission behavior: Past due assignment with late disallowed -> 400
    late_payload = {
        "text_content": "Late Paxos submission attempt.",
    }
    r = await client.post(f"/api/assignments/{past_due_assignment.id}/submissions", json=late_payload, headers=student_headers)
    assert r.status_code == 400
    assert "late submissions are not permitted" in r.json()["detail"]

    # 11. Allow late submissions on past due assignment and verify penalty tagging
    past_due_assignment.allow_late_submissions = True
    past_due_assignment.late_penalty_percentage_per_day = 10.0
    await test_session.commit()

    r = await client.post(f"/api/assignments/{past_due_assignment.id}/submissions", json=late_payload, headers=student_headers)
    assert r.status_code == 201
    late_sub = r.json()
    assert late_sub["is_late"] is True
    assert late_sub["days_late"] >= 1.9
    assert late_sub["late_penalty_applied"] >= 19.0
