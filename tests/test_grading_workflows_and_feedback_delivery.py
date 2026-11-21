from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    Assignment, AssignmentSubmission, AssignmentStatus,
    SubmissionAnnotation, GradeAppeal
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_grading_workflows_and_feedback_delivery(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Enrolled Student, Outsider Student
    admin_user = User(
        email="grading_admin@nsbm.ac.lk",
        username="grading_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Assessment Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="grading_lecturer@nsbm.ac.lk",
        username="grading_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Grace Hopper",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_user = User(
        email="grading_student@nsbm.ac.lk",
        username="grading_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Student Linus",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)

    outsider_user = User(
        email="grading_outsider@nsbm.ac.lk",
        username="grading_outsider",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Student Outsider",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(outsider_user)
    await test_session.commit()

    # Profiles
    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-GRADE-01",
        faculty="Computing",
        department="Software Engineering",
    )
    test_session.add(lecturer)

    student = Student(
        user_id=student_user.id,
        student_id="STU-GRADE-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc in Software Engineering",
        year_of_study=3,
        semester=1,
    )
    test_session.add(student)

    outsider = Student(
        user_id=outsider_user.id,
        student_id="STU-GRADE-02",
        faculty="Computing",
        department="Software Engineering",
        program="BSc in Software Engineering",
        year_of_study=3,
        semester=1,
    )
    test_session.add(outsider)
    await test_session.commit()

    # Course & Enrollment
    course = Course(
        course_code="CS501",
        title="Distributed Systems Engineering",
        description="Formal proofs and consensus mechanisms.",
        credits=4,
        faculty="Computing",
        department="Software Engineering",
        semester=1,
        year=3,
        lecturer_id=lecturer.id,
    )
    test_session.add(course)
    await test_session.commit()

    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        status="enrolled",
    )
    test_session.add(enrollment)

    # Assignment
    now = datetime.utcnow()
    assignment = Assignment(
        course_id=course.id,
        title="Consensus Protocols Implementation",
        description="Implement Raft or Paxos leader election",
        due_date=now + timedelta(days=7),
        max_marks=100.0,
        weightage_percentage=25.0,
        status="published",
        grades_released=False,
    )
    test_session.add(assignment)
    await test_session.commit()

    # Student Submission
    submission = AssignmentSubmission(
        assignment_id=assignment.id,
        student_id=student.id,
        file_url="https://github.com/student/raft-consensus",
        text_content="Raft consensus implementation source code",
        submitted_at=now,
        status=AssignmentStatus.SUBMITTED,
        attempt_number=1,
        submission_receipt="rcpt_raft_001",
    )
    test_session.add(submission)
    await test_session.commit()

    # Auth headers
    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": lecturer_user.role.value})
    student_token = create_access_token({"sub": str(student_user.id), "role": student_user.role.value})
    outsider_token = create_access_token({"sub": str(outsider_user.id), "role": outsider_user.role.value})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    # ─── 2. Speed-Grading Endpoint Tests ──────────────────────────────────────────
    # Student cannot grade
    res_student_grade = await client.post(
        f"/api/submissions/{submission.id}/grade",
        json={"marks": 92.5, "feedback": "Nice implementation"},
        headers=student_headers
    )
    assert res_student_grade.status_code == 403

    # Marks exceed maximum
    res_exceed = await client.post(
        f"/api/submissions/{submission.id}/grade",
        json={"marks": 105.0, "feedback": "Extra credit attempt"},
        headers=lecturer_headers
    )
    assert res_exceed.status_code == 400

    # Lecturer grades successfully
    res_grade = await client.post(
        f"/api/submissions/{submission.id}/grade",
        json={"marks": 88.0, "feedback": "Solid leader election, minor edge case in log replication."},
        headers=lecturer_headers
    )
    assert res_grade.status_code == 200
    grade_data = res_grade.json()
    assert grade_data["marks"] == 88.0
    assert "Solid leader election" in grade_data["feedback"]
    assert grade_data["status"] == "graded"
    assert grade_data["graded_by_id"] == lecturer_user.id

    # ─── 3. Inline Annotations Tests ─────────────────────────────────────────────
    # Lecturer creates inline annotation
    res_ann = await client.post(
        f"/api/submissions/{submission.id}/annotations",
        json={
            "page_number": 3,
            "coordinates": {"x": 120, "y": 340, "width": 80, "height": 20},
            "comment_text": "Heartbeat interval should be randomized to prevent split votes."
        },
        headers=lecturer_headers
    )
    assert res_ann.status_code == 201
    ann_data = res_ann.json()
    assert ann_data["page_number"] == 3
    assert ann_data["coordinates"]["x"] == 120
    assert "randomized" in ann_data["comment_text"]
    annotation_id = ann_data["id"]

    # Student owner can view annotations
    res_list_ann = await client.get(
        f"/api/submissions/{submission.id}/annotations",
        headers=student_headers
    )
    assert res_list_ann.status_code == 200
    assert len(res_list_ann.json()) == 1

    # Outsider cannot view annotations
    res_outsider_ann = await client.get(
        f"/api/submissions/{submission.id}/annotations",
        headers=outsider_headers
    )
    assert res_outsider_ann.status_code == 403

    # ─── 4. Grade Release Lifecycle Tests ─────────────────────────────────────────
    # Student cannot release grades
    res_rel_stud = await client.post(
        f"/api/assignments/{assignment.id}/release-grades",
        headers=student_headers
    )
    assert res_rel_stud.status_code == 403

    # Lecturer releases grades
    res_rel = await client.post(
        f"/api/assignments/{assignment.id}/release-grades",
        headers=lecturer_headers
    )
    assert res_rel.status_code == 200
    release_data = res_rel.json()
    assert release_data["grades_released"] is True
    assert release_data["submissions_graded_count"] == 1

    # ─── 5. Grade Appeal Workflow Tests ──────────────────────────────────────────
    # Student submits grade appeal
    res_appeal = await client.post(
        f"/api/submissions/{submission.id}/appeals",
        json={
            "reason": "Log replication handles network partitions correctly in test cases 4 and 5.",
            "requested_marks": 94.0
        },
        headers=student_headers
    )
    assert res_appeal.status_code == 201
    appeal_data = res_appeal.json()
    assert appeal_data["status"] == "pending"
    assert appeal_data["requested_marks"] == 94.0
    appeal_id = appeal_data["id"]

    # Lecturer lists appeals
    res_appeals_list = await client.get(
        f"/api/assignments/{assignment.id}/appeals",
        headers=lecturer_headers
    )
    assert res_appeals_list.status_code == 200
    assert len(res_appeals_list.json()) == 1

    # Lecturer resolves appeal and updates marks
    res_resolve = await client.post(
        f"/api/appeals/{appeal_id}/resolve",
        json={
            "status": "approved",
            "resolution_notes": "Reviewed test cases 4 and 5; adjusted marks from 88 to 93.",
            "adjusted_marks": 93.0
        },
        headers=lecturer_headers
    )
    assert res_resolve.status_code == 200
    resolve_data = res_resolve.json()
    assert resolve_data["status"] == "approved"
    assert "adjusted marks" in resolve_data["resolution_notes"]

    # Verify submission reflects updated marks
    await test_session.refresh(submission)
    assert submission.marks == 93.0
    assert "Regrade Resolution" in submission.feedback

    # ─── 6. Annotation Deletion Cleanup ──────────────────────────────────────────
    # Author deletes annotation
    res_del_ann = await client.delete(
        f"/api/submissions/{submission.id}/annotations/{annotation_id}",
        headers=lecturer_headers
    )
    assert res_del_ann.status_code == 204

    # Verify annotation deleted
    res_list_ann2 = await client.get(
        f"/api/submissions/{submission.id}/annotations",
        headers=lecturer_headers
    )
    assert res_list_ann2.status_code == 200
    assert len(res_list_ann2.json()) == 0
