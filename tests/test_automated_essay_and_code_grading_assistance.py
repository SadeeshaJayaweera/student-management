from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User,
    UserRole,
    Student,
    Course,
    Assignment,
    AssignmentSubmission,
    AssignmentStatus,
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_automated_essay_and_code_grading_assistance(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Lecturer and Student users
    lecturer_user = User(
        email="grading_prof@nsbm.ac.lk",
        username="grading_prof",
        hashed_password=hash_password("ProfPass123!"),
        full_name="Prof. Edsger Dijkstra",
        role=UserRole.LECTURER,
        is_active=True,
    )
    student_user = User(
        email="grading_student@nsbm.ac.lk",
        username="grading_student",
        hashed_password=hash_password("StuPass123!"),
        full_name="Niklaus Wirth",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([lecturer_user, student_user])
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-GRADE-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc (Hons) Computer Science",
        year_of_study=3,
        semester=1,
        gpa=3.75,
        credits_earned=68,
    )
    test_session.add(student)
    await test_session.commit()

    # 2. Setup Course and Assignments
    course = Course(
        course_code="CS309",
        title="Algorithms & Computational Complexity",
        description="Formal complexity analysis, divide-and-conquer, dynamic programming, and greedy algorithms.",
        faculty="Computing",
        department="Computer Science",
        credits=3,
        semester=1,
        year=3,
        is_active=True,
    )
    test_session.add(course)
    await test_session.commit()

    essay_assignment = Assignment(
        course_id=course.id,
        title="P vs NP Theoretical Essay",
        description="Write an analytical essay assessing the implications of polynomial-time verification.",
        due_date=datetime.utcnow() + timedelta(days=7),
        max_marks=100.0,
        status="published",
    )
    code_assignment = Assignment(
        course_id=course.id,
        title="Merge Sort Optimization Code Lab",
        description="Implement an in-place merge sort algorithm minimizing allocation overhead.",
        due_date=datetime.utcnow() + timedelta(days=7),
        max_marks=100.0,
        status="published",
    )
    test_session.add_all([essay_assignment, code_assignment])
    await test_session.commit()

    # 3. Create Submissions
    essay_content = (
        "The P versus NP problem represents one of the foremost open questions in theoretical computer science. "
        "A decision problem is in class P if it can be solved by a deterministic Turing machine in polynomial time. "
        "Conversely, NP encompasses problems whose positive solutions can be verified in polynomial time. "
        "If P equals NP, cryptographic algorithms like RSA and elliptic-curve cryptography would become computationally vulnerable. "
        "NP-completeness, formalized by Cook and Levin, proves that any polynomial-time algorithm for SAT implies P equals NP."
    )
    essay_sub = AssignmentSubmission(
        assignment_id=essay_assignment.id,
        student_id=student.id,
        text_content=essay_content,
        status=AssignmentStatus.SUBMITTED,
    )

    code_content = (
        "def merge_sort(arr):\n"
        "    \"\"\"Divide and conquer recursive merge sort implementation.\"\"\"\n"
        "    if len(arr) <= 1:\n"
        "        return arr\n"
        "    mid = len(arr) // 2\n"
        "    left = merge_sort(arr[:mid])\n"
        "    right = merge_sort(arr[mid:])\n"
        "    return merge(left, right)\n\n"
        "def merge(left, right):\n"
        "    res = []\n"
        "    i = j = 0\n"
        "    while i < len(left) and j < len(right):\n"
        "        if left[i] <= right[j]:\n"
        "            res.append(left[i])\n"
        "            i += 1\n"
        "        else:\n"
        "            res.append(right[j])\n"
        "            j += 1\n"
        "    res.extend(left[i:])\n"
        "    res.extend(right[j:])\n"
        "    return res\n"
    )
    code_sub = AssignmentSubmission(
        assignment_id=code_assignment.id,
        student_id=student.id,
        text_content=code_content,
        status=AssignmentStatus.SUBMITTED,
    )
    test_session.add_all([essay_sub, code_sub])
    await test_session.commit()

    lec_token = create_access_token({"sub": str(lecturer_user.id), "role": "lecturer"})
    lec_headers = {"Authorization": f"Bearer {lec_token}"}
    stu_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    # 4. RBAC Check: Student cannot run evaluation
    res_forbidden = await client.post(
        f"/api/ai/grading/submissions/{essay_sub.id}/evaluate",
        json={"submission_type": "essay"},
        headers=stu_headers
    )
    assert res_forbidden.status_code == 403

    # 5. Lecturer evaluates Essay Submission
    res_essay = await client.post(
        f"/api/ai/grading/submissions/{essay_sub.id}/evaluate",
        json={"submission_type": "essay"},
        headers=lec_headers
    )
    assert res_essay.status_code == 201
    essay_review = res_essay.json()
    assert essay_review["status"] == "ai_draft"
    assert essay_review["ai_suggested_score"] >= 70.0
    assert len(essay_review["rubric_breakdown_json"]) == 4
    criteria_names = [r["criterion"] for r in essay_review["rubric_breakdown_json"]]
    assert any("Thesis" in c for c in criteria_names)

    # 6. Lecturer evaluates Code Submission
    res_code = await client.post(
        f"/api/ai/grading/submissions/{code_sub.id}/evaluate",
        json={"submission_type": "code_snippet"},
        headers=lec_headers
    )
    assert res_code.status_code == 201
    code_review = res_code.json()
    assert code_review["code_analysis_json"]["syntax_valid"] is True
    assert "complexity_score" in code_review["code_analysis_json"]
    assert code_review["ai_suggested_score"] > 0
    code_review_id = code_review["id"]

    # 7. Lecturer approves with score override and commentary
    # Override from AI suggested score (e.g. ~87) to 92.0
    res_approve = await client.post(
        f"/api/ai/grading/reviews/{code_review_id}/approve",
        json={
            "final_score": 92.0,
            "lecturer_feedback": "Excellent recursive decomposition. In future implementations, consider in-place array buffer reuse."
        },
        headers=lec_headers
    )
    assert res_approve.status_code == 200
    approved_review = res_approve.json()
    assert approved_review["final_score"] == 92.0
    assert approved_review["status"] == "overridden"
    assert approved_review["score_delta"] != 0.0
    assert approved_review["reviewed_at"] is not None

    # Verify official submission status updated to GRADED
    await test_session.refresh(code_sub)
    assert code_sub.marks == 92.0
    assert code_sub.status == AssignmentStatus.GRADED
    assert "In future implementations" in code_sub.feedback

    # 8. Course Grading Audit Statistics
    res_audit = await client.get(
        f"/api/ai/grading/courses/{course.id}/audit",
        headers=lec_headers
    )
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert audit_data["total_reviews"] == 2
    assert audit_data["overridden_count"] == 1
    assert audit_data["course_id"] == course.id
