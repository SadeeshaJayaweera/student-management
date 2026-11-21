"""
NSBM EduSphere — Stage 05 Assessment & Grading Architecture End-to-End Review Test
Comprehensive verification of all 9 Stage 05 capabilities:
- Assignment Lifecycle Architecture (Change 41)
- Rubric-Based Assessment Engine (Change 42)
- Assignment Submission and Versioning (Change 43)
- Question Bank and Question Types (Change 44)
- Automated Quiz and Assessment Engine (Change 45)
- Timed Examinations and Proctoring Controls (Change 46)
- Academic Integrity and Plagiarism Checks (Change 47)
- Grading Workflows and Feedback Delivery (Change 48)
- Gradebook and Calculation Engine (Change 49)
"""
from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    Assignment, AssignmentSubmission, AssignmentStatus,
    Rubric, RubricCriterion, RubricLevel,
    QuestionCategory, QuestionBankItem,
    Quiz, QuizQuestion, QuizAttempt,
    ExamProctoringSession,
    PlagiarismScanReport,
    SubmissionAnnotation, GradeAppeal,
    GradebookCategory, GradeScale, GradebookOverride
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_stage_05_assessment_architecture_end_to_end_review(
    client: AsyncClient,
    test_session: AsyncSession
):
    # ─── 1. Setup Academic Actors & Course ────────────────────────────────────────
    admin_user = User(
        email="stage05_admin@nsbm.ac.lk",
        username="stage05_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Assessment Director",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="stage05_lecturer@nsbm.ac.lk",
        username="stage05_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Donald Knuth",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_a_user = User(
        email="stage05_student_a@nsbm.ac.lk",
        username="stage05_student_a",
        hashed_password=hash_password("StudentPass123!"),
        full_name="John von Neumann",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_a_user)

    student_b_user = User(
        email="stage05_student_b@nsbm.ac.lk",
        username="stage05_student_b",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Alonzo Church",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_b_user)

    outsider_user = User(
        email="stage05_outsider@nsbm.ac.lk",
        username="stage05_outsider",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Outsider Person",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(outsider_user)
    await test_session.commit()

    # Profiles
    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-STG5-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add(lecturer)

    student_a = Student(
        user_id=student_a_user.id,
        student_id="STU-STG5-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=3,
        semester=1,
    )
    test_session.add(student_a)

    student_b = Student(
        user_id=student_b_user.id,
        student_id="STU-STG5-02",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=3,
        semester=1,
    )
    test_session.add(student_b)

    outsider = Student(
        user_id=outsider_user.id,
        student_id="STU-STG5-03",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=3,
        semester=1,
    )
    test_session.add(outsider)
    await test_session.commit()

    # Course
    course = Course(
        course_code="CS601",
        title="Compilers and Formal Automata",
        description="Parsing, semantic analysis, intermediate representation, and code generation.",
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
    enr_a = Enrollment(student_id=student_a.id, course_id=course.id, status="enrolled")
    enr_b = Enrollment(student_id=student_b.id, course_id=course.id, status="enrolled")
    test_session.add_all([enr_a, enr_b])
    await test_session.commit()

    # Tokens & Headers
    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": lecturer_user.role.value})
    student_a_token = create_access_token({"sub": str(student_a_user.id), "role": student_a_user.role.value})
    student_b_token = create_access_token({"sub": str(student_b_user.id), "role": student_b_user.role.value})
    outsider_token = create_access_token({"sub": str(outsider_user.id), "role": outsider_user.role.value})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}
    student_a_headers = {"Authorization": f"Bearer {student_a_token}"}
    student_b_headers = {"Authorization": f"Bearer {student_b_token}"}
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    # ─── 2. Gradebook Categories Setup (Change 49) ────────────────────────────────
    res_cat_asg = await client.post(
        f"/api/courses/{course.id}/gradebook/categories",
        json={"name": "Assignments", "weight_percentage": 60.0, "drop_lowest_count": 0},
        headers=lecturer_headers
    )
    assert res_cat_asg.status_code == 201
    cat_asg_id = res_cat_asg.json()["id"]

    res_cat_quiz = await client.post(
        f"/api/courses/{course.id}/gradebook/categories",
        json={"name": "Quizzes", "weight_percentage": 40.0, "drop_lowest_count": 0},
        headers=lecturer_headers
    )
    assert res_cat_quiz.status_code == 201
    cat_quiz_id = res_cat_quiz.json()["id"]

    # ─── 3. Rubric Authoring & Binding (Change 42) ────────────────────────────────
    res_rubric = await client.post(
        f"/api/courses/{course.id}/rubrics",
        json={
            "title": "Lexer & Parser Design Rubric",
            "description": "Evaluation framework for recursive descent compiler frontend.",
            "max_points": 100.0,
            "criteria": [
                {
                    "title": "Grammar Correctness",
                    "description": "Elimination of left recursion and proper precedence.",
                    "max_points": 50.0,
                    "order_index": 1,
                    "levels": [
                        {"title": "Exemplary", "description": "LL(1) compliant grammar with zero conflicts", "point_value": 50.0, "order_index": 1},
                        {"title": "Competent", "description": "Minor ambiguity in operator precedence", "point_value": 35.0, "order_index": 2},
                        {"title": "Needs Improvement", "description": "Left recursion present", "point_value": 15.0, "order_index": 3}
                    ]
                },
                {
                    "title": "AST Construction",
                    "description": "Clean typed abstract syntax tree nodes.",
                    "max_points": 50.0,
                    "order_index": 2,
                    "levels": [
                        {"title": "Exemplary", "description": "Complete typed AST with visitor pattern", "point_value": 50.0, "order_index": 1},
                        {"title": "Competent", "description": "Basic AST without visitor pattern", "point_value": 35.0, "order_index": 2}
                    ]
                }
            ]
        },
        headers=lecturer_headers
    )
    assert res_rubric.status_code == 201
    rubric_data = res_rubric.json()
    rubric_id = rubric_data["id"]
    crit1_id = rubric_data["criteria"][0]["id"]
    crit2_id = rubric_data["criteria"][1]["id"]

    # ─── 4. Assignment Lifecycle & Authoring (Change 41) ──────────────────────────
    now = datetime.utcnow()
    res_asg = await client.post(
        f"/api/courses/{course.id}/assignments",
        json={
            "course_id": course.id,
            "title": "Recursive Descent Parser Project",
            "description": "Build an LL(1) parser for a typed imperative grammar.",
            "due_date": (now + timedelta(days=7)).isoformat(),
            "available_from": (now - timedelta(hours=1)).isoformat(),
            "cutoff_date": (now + timedelta(days=10)).isoformat(),
            "max_marks": 100.0,
            "weightage_percentage": 60.0,
            "max_attempts": 3,
            "allow_late_submissions": True,
            "late_penalty_percentage_per_day": 5.0,
            "rubric_id": rubric_id,
            "status": "published",
        },
        headers=lecturer_headers
    )
    assert res_asg.status_code == 201
    asg_data = res_asg.json()
    assignment_id = asg_data["id"]

    # Attach rubric to assignment
    res_attach = await client.post(
        f"/api/assignments/{assignment_id}/rubric/{rubric_id}",
        headers=lecturer_headers
    )
    assert res_attach.status_code == 200

    # Link assignment to category
    res_asg_obj = await test_session.execute(select(Assignment).where(Assignment.id == assignment_id))
    asg_obj = res_asg_obj.scalar_one()
    asg_obj.category_id = cat_asg_id
    asg_obj.grades_released = False
    await test_session.commit()

    # ─── 5. Submissions and Versioning (Change 43) ────────────────────────────────
    # Student A submits attempt 1
    res_sub_a = await client.post(
        f"/api/assignments/{assignment_id}/submissions",
        json={
            "file_url": "https://storage.nsbm.ac.lk/submissions/student_a_parser_v1.zip",
            "text_content": "Initial complete implementation of parser with visitor pattern AST.",
            "attachments": [{"filename": "parser.py", "url": "https://storage/parser.py", "size_bytes": 1024}]
        },
        headers=student_a_headers
    )
    assert res_sub_a.status_code == 201
    sub_a_data = res_sub_a.json()
    sub_a_id = sub_a_data["id"]
    assert sub_a_data["attempt_number"] == 1
    assert sub_a_data["submission_receipt"] is not None

    # Student B submits attempt 1
    res_sub_b = await client.post(
        f"/api/assignments/{assignment_id}/submissions",
        json={
            "file_url": "https://storage.nsbm.ac.lk/submissions/student_b_parser_v1.zip",
            "text_content": "Implementation of LL(1) parser with visitor pattern AST.",
            "attachments": [{"filename": "parser_b.py", "url": "https://storage/parser_b.py", "size_bytes": 1024}]
        },
        headers=student_b_headers
    )
    assert res_sub_b.status_code == 201
    sub_b_data = res_sub_b.json()
    sub_b_id = sub_b_data["id"]

    # ─── 6. Academic Integrity & Plagiarism Check (Change 47) ─────────────────────
    # Run scan on Student A's submission against cohort
    res_scan = await client.post(
        f"/api/assignments/{assignment_id}/submissions/{sub_a_id}/plagiarism-scan",
        headers=lecturer_headers
    )
    assert res_scan.status_code == 200
    scan_data = res_scan.json()
    assert scan_data["status"] == "completed"
    assert "similarity_score" in scan_data
    assert scan_data["integrity_flag"] in {"clean", "suspicious", "flagged"}

    # ─── 7. Question Bank & Taxonomy (Change 44) ──────────────────────────────────
    res_qcat = await client.post(
        f"/api/courses/{course.id}/question-categories",
        json={"name": "Grammar & Automata", "description": "Context-free grammars and pushdown automata"},
        headers=lecturer_headers
    )
    assert res_qcat.status_code == 201
    qcat_id = res_qcat.json()["id"]

    res_q1 = await client.post(
        f"/api/courses/{course.id}/questions",
        json={
            "category_id": qcat_id,
            "title": "LL(1) Precedence",
            "prompt": "Which technique resolves operator precedence in LL(1) grammars?",
            "question_type": "single_choice",
            "difficulty_level": "intermediate",
            "default_points": 25.0,
            "options": [
                {"id": "opt1", "text": "Stratified non-terminals", "is_correct": True},
                {"id": "opt2", "text": "Direct left recursion", "is_correct": False},
                {"id": "opt3", "text": "Shift-reduce tables", "is_correct": False}
            ]
        },
        headers=lecturer_headers
    )
    assert res_q1.status_code == 201
    q1_id = res_q1.json()["id"]

    res_q2 = await client.post(
        f"/api/courses/{course.id}/questions",
        json={
            "category_id": qcat_id,
            "title": "Chomsky Hierarchy",
            "prompt": "A context-free grammar can be parsed by which automaton?",
            "question_type": "single_choice",
            "difficulty_level": "intermediate",
            "default_points": 25.0,
            "options": [
                {"id": "opt1", "text": "Non-deterministic Pushdown Automaton", "is_correct": True},
                {"id": "opt2", "text": "Deterministic Finite Automaton", "is_correct": False}
            ]
        },
        headers=lecturer_headers
    )
    assert res_q2.status_code == 201
    q2_id = res_q2.json()["id"]

    # ─── 8. Automated Quiz & Proctoring Controls (Changes 45 & 46) ───────────────
    res_quiz = await client.post(
        f"/api/courses/{course.id}/quizzes",
        json={
            "title": "Formal Language Foundations Quiz",
            "description": "Assess parsing theory and grammars",
            "due_date": (now + timedelta(days=5)).isoformat(),
            "time_limit_minutes": 30,
            "passing_score_percentage": 50.0,
            "status": "published",
        },
        headers=lecturer_headers
    )
    assert res_quiz.status_code == 201
    quiz_id = res_quiz.json()["id"]

    # Link quiz to category
    res_quiz_obj = await test_session.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz_obj = res_quiz_obj.scalar_one()
    quiz_obj.category_id = cat_quiz_id
    await test_session.commit()

    # Add questions to quiz
    await client.post(f"/api/quizzes/{quiz_id}/questions", json={"question_item_id": q1_id, "points": 25.0, "order_index": 1}, headers=lecturer_headers)
    await client.post(f"/api/quizzes/{quiz_id}/questions", json={"question_item_id": q2_id, "points": 25.0, "order_index": 2}, headers=lecturer_headers)

    # Student A starts quiz attempt with proctoring
    res_start_quiz = await client.post(f"/api/quizzes/{quiz_id}/start", headers=student_a_headers)
    assert res_start_quiz.status_code == 201
    attempt_a_data = res_start_quiz.json()
    attempt_a_id = attempt_a_data["attempt_id"]

    # Start proctoring session for Student A
    res_proc = await client.post(
        f"/api/exams/{quiz_id}/proctoring/start",
        json={"attempt_id": attempt_a_id},
        headers=student_a_headers
    )
    assert res_proc.status_code == 201
    session_token = res_proc.json()["session_token"]

    # Proctoring heartbeat keep-alive
    res_heartbeat = await client.post(
        f"/api/proctoring/{session_token}/heartbeat",
        headers=student_a_headers
    )
    assert res_heartbeat.status_code == 200

    # Student A submits quiz with correct answers
    res_submit_quiz = await client.post(
        f"/api/quizzes/{quiz_id}/attempts/{attempt_a_id}/submit",
        json={
            "answers": [
                {"question_id": q1_id, "selected_option_ids": ["opt1"]},
                {"question_id": q2_id, "selected_option_ids": ["opt1"]}
            ]
        },
        headers=student_a_headers
    )
    assert res_submit_quiz.status_code == 200
    quiz_result = res_submit_quiz.json()
    assert quiz_result["total_score"] == 50.0
    assert quiz_result["percentage"] == 100.0
    assert quiz_result["is_passed"] is True

    # ─── 9. Speed-Grading, Rubrics & Feedback Annotations (Change 48) ─────────────
    # Lecturer evaluates Student A's submission with rubric
    res_eval = await client.post(
        f"/api/assignments/{assignment_id}/rubric-evaluations",
        json={
            "submission_id": sub_a_id,
            "criteria_scores": [
                {"criterion_id": crit1_id, "points": 50.0, "comment": "Flawless grammar construction."},
                {"criterion_id": crit2_id, "points": 45.0, "comment": "Well-structured AST with minor visitor redundancy."}
            ],
            "feedback": "Outstanding compiler frontend work overall."
        },
        headers=lecturer_headers
    )
    assert res_eval.status_code == 201
    eval_data = res_eval.json()
    assert eval_data["total_score"] == 95.0

    # Lecturer grades submission to 95.0
    res_grade = await client.post(
        f"/api/submissions/{sub_a_id}/grade",
        json={"marks": 95.0, "feedback": "Exemplary work; clean typed AST."},
        headers=lecturer_headers
    )
    assert res_grade.status_code == 200

    # Lecturer grades Student B's submission to 80.0
    res_grade_b = await client.post(
        f"/api/submissions/{sub_b_id}/grade",
        json={"marks": 80.0, "feedback": "Good effort; missing full AST typing."},
        headers=lecturer_headers
    )
    assert res_grade_b.status_code == 200

    # Lecturer adds inline document annotation
    res_ann = await client.post(
        f"/api/submissions/{sub_a_id}/annotations",
        json={
            "page_number": 1,
            "coordinates": {"x": 50, "y": 100, "width": 200, "height": 30},
            "comment_text": "Consider optimizing token lookahead buffer for performance."
        },
        headers=lecturer_headers
    )
    assert res_ann.status_code == 201

    # Release grades
    res_release = await client.post(
        f"/api/assignments/{assignment_id}/release-grades",
        headers=lecturer_headers
    )
    assert res_release.status_code == 200
    assert res_release.json()["grades_released"] is True

    # Student B submits a grade appeal
    res_appeal = await client.post(
        f"/api/submissions/{sub_b_id}/appeals",
        json={"reason": "The AST typing is included in types.py module. Please re-check.", "requested_marks": 88.0},
        headers=student_b_headers
    )
    assert res_appeal.status_code == 201
    appeal_id = res_appeal.json()["id"]

    # Lecturer resolves appeal and adjusts Student B marks to 86.0
    res_resolve = await client.post(
        f"/api/appeals/{appeal_id}/resolve",
        json={
            "status": "approved",
            "resolution_notes": "Reviewed types.py; adjusted marks to 86.0.",
            "adjusted_marks": 86.0
        },
        headers=lecturer_headers
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "approved"

    # ─── 10. Gradebook Calculation & Export Verification (Change 49) ──────────────
    res_gb = await client.get(
        f"/api/courses/{course.id}/gradebook",
        headers=lecturer_headers
    )
    assert res_gb.status_code == 200
    gb_data = res_gb.json()
    assert gb_data["course_code"] == "CS601"
    assert gb_data["total_enrolled"] == 2
    assert len(gb_data["categories"]) == 2

    # Verify Student A calculation:
    # Assignment: 95/100 (95% * 0.6 = 57.0)
    # Quiz: 50/50 (100% * 0.4 = 40.0)
    # Total percentage = 97.0% -> Letter grade "A+", GPA 4.0
    student_a_rec = next(s for s in gb_data["students"] if s["student_id"] == student_a.id)
    assert student_a_rec["calculated_percentage"] == 97.0
    assert student_a_rec["letter_grade"] == "A+"
    assert student_a_rec["gpa_points"] == 4.0

    # Student A can view own summary
    res_self = await client.get(
        f"/api/courses/{course.id}/gradebook/student/{student_a.id}",
        headers=student_a_headers
    )
    assert res_self.status_code == 200
    assert res_self.json()["final_letter_grade"] == "A+"

    # Outsider cannot view gradebook or student grades
    res_out_gb = await client.get(f"/api/courses/{course.id}/gradebook", headers=outsider_headers)
    assert res_out_gb.status_code == 403

    # Export gradebook as JSON
    res_export = await client.get(
        f"/api/courses/{course.id}/gradebook/export?export_format=json",
        headers=lecturer_headers
    )
    assert res_export.status_code == 200
    assert res_export.json()["records_count"] == 2
