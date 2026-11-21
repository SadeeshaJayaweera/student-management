from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Course, Student, Lecturer, Enrollment,
    QuestionCategory, QuestionBankItem
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_question_bank_and_question_types_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Enrolled Student, and Outsider
    admin_user = User(
        email="qb_admin@nsbm.ac.lk",
        username="qb_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Assessment Controller",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="qb_lecturer@nsbm.ac.lk",
        username="qb_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Niklaus Wirth",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_user = User(
        email="qb_student@nsbm.ac.lk",
        username="qb_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Margaret Hamilton",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)

    outsider_user = User(
        email="qb_outsider@nsbm.ac.lk",
        username="qb_outsider",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Outsider User",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(outsider_user)
    await test_session.commit()

    # Profiles
    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-QB-01",
        faculty="Computing",
        department="Computer Science",
    )
    test_session.add(lecturer)

    student = Student(
        user_id=student_user.id,
        student_id="STU-QB-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=2,
        semester=1,
    )
    test_session.add(student)

    outsider = Student(
        user_id=outsider_user.id,
        student_id="STU-QB-02",
        faculty="Business",
        department="Economics",
        program="BSc Economics",
        year_of_study=1,
        semester=1,
    )
    test_session.add(outsider)
    await test_session.commit()

    # Course
    course = Course(
        course_code="CS202",
        title="Data Structures & Algorithms",
        description="Linear and non-linear data structures, trees, and graphs.",
        credits=4,
        faculty="Computing",
        department="Computer Science",
        semester=1,
        year=2,
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

    # 2. Student cannot browse or manage question categories -> 403 Forbidden
    category_payload = {
        "name": "Balanced Search Trees",
        "description": "AVL trees, Red-Black trees, and B-trees.",
        "display_order": 1,
    }
    r = await client.post(f"/api/courses/{course.id}/question-categories", json=category_payload, headers=student_headers)
    assert r.status_code == 403

    # 3. Lecturer creates question category
    r = await client.post(f"/api/courses/{course.id}/question-categories", json=category_payload, headers=lecturer_headers)
    assert r.status_code == 201
    cat_data = r.json()
    category_id = cat_data["id"]
    assert cat_data["name"] == "Balanced Search Trees"

    # 4. Student cannot browse categories -> 403
    r = await client.get(f"/api/courses/{course.id}/question-categories", headers=student_headers)
    assert r.status_code == 403

    # 5. Lecturer lists categories
    r = await client.get(f"/api/courses/{course.id}/question-categories", headers=lecturer_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # 6. Invalid question creation: single_choice with no correct option -> 400
    invalid_mcq = {
        "category_id": category_id,
        "title": "Invalid Tree Question",
        "prompt": "Which node is root?",
        "question_type": "single_choice",
        "options": [
            {"id": "opt_1", "text": "Node A", "is_correct": False},
            {"id": "opt_2", "text": "Node B", "is_correct": False}
        ]
    }
    r = await client.post(f"/api/courses/{course.id}/questions", json=invalid_mcq, headers=lecturer_headers)
    assert r.status_code == 400
    assert "at least one correct option" in r.json()["detail"]

    # 7. Lecturer creates valid Single Choice Question
    mcq_payload = {
        "category_id": category_id,
        "title": "AVL Search Complexity",
        "prompt": "What is the worst-case time complexity of searching in an AVL tree containing n nodes?",
        "question_type": "single_choice",
        "difficulty_level": "intermediate",
        "default_points": 2.0,
        "tags": ["trees", "complexity", "avl"],
        "options": [
            {"id": "opt_a", "text": "O(1)", "is_correct": False, "feedback": "Search requires tree traversal."},
            {"id": "opt_b", "text": "O(log n)", "is_correct": True, "feedback": "AVL trees guarantee logarithmic height."},
            {"id": "opt_c", "text": "O(n)", "is_correct": False, "feedback": "Unbalanced trees may degrade to O(n), but AVL is balanced."},
            {"id": "opt_d", "text": "O(n log n)", "is_correct": False, "feedback": "O(n log n) is sorting complexity."}
        ]
    }
    r = await client.post(f"/api/courses/{course.id}/questions", json=mcq_payload, headers=lecturer_headers)
    assert r.status_code == 201
    q1 = r.json()
    q1_id = q1["id"]
    assert q1["question_type"] == "single_choice"
    assert q1["default_points"] == 2.0
    assert len(q1["options"]) == 4

    # 8. Lecturer creates Multiple Choice (Multi-Select) Question
    multi_mcq = {
        "category_id": category_id,
        "title": "Self Balancing Trees",
        "prompt": "Which of the following data structures are self-balancing search trees? (Select all that apply)",
        "question_type": "multiple_choice",
        "difficulty_level": "advanced",
        "default_points": 3.0,
        "tags": ["trees", "balanced"],
        "options": [
            {"id": "opt_1", "text": "Red-Black Tree", "is_correct": True},
            {"id": "opt_2", "text": "AVL Tree", "is_correct": True},
            {"id": "opt_3", "text": "Linked List", "is_correct": False},
            {"id": "opt_4", "text": "Binary Heap", "is_correct": False}
        ]
    }
    r = await client.post(f"/api/courses/{course.id}/questions", json=multi_mcq, headers=lecturer_headers)
    assert r.status_code == 201
    q2 = r.json()
    assert q2["question_type"] == "multiple_choice"

    # 9. Lecturer creates Numerical Question
    num_payload = {
        "category_id": category_id,
        "title": "Max Nodes in Binary Tree",
        "prompt": "What is the maximum number of nodes in a full binary tree of depth 4 (counting root at depth 0)?",
        "question_type": "numerical",
        "difficulty_level": "intermediate",
        "default_points": 2.5,
        "tags": ["trees", "math"],
        "answer_key": {"target_value": 31.0, "tolerance": 0.0}
    }
    r = await client.post(f"/api/courses/{course.id}/questions", json=num_payload, headers=lecturer_headers)
    assert r.status_code == 201
    q3 = r.json()
    assert q3["question_type"] == "numerical"

    # 10. Student cannot list question bank -> 403 Forbidden
    r = await client.get(f"/api/courses/{course.id}/questions", headers=student_headers)
    assert r.status_code == 403

    # 11. Lecturer queries question bank with filters
    # Filter by question_type
    r = await client.get(f"/api/courses/{course.id}/questions?question_type=single_choice", headers=lecturer_headers)
    assert r.status_code == 200
    single_choice_items = r.json()
    assert len(single_choice_items) == 1
    assert single_choice_items[0]["id"] == q1_id

    # Filter by tag
    r = await client.get(f"/api/courses/{course.id}/questions?tag=avl", headers=lecturer_headers)
    assert r.status_code == 200
    tag_items = r.json()
    assert len(tag_items) == 1
    assert tag_items[0]["id"] == q1_id

    # Filter by search keyword
    r = await client.get(f"/api/courses/{course.id}/questions?search=complexity", headers=lecturer_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # 12. Lecturer updates question item
    update_payload = {
        "title": "AVL Tree Search Time Complexity (Updated)",
        "default_points": 3.0,
    }
    r = await client.patch(f"/api/questions/{q1_id}", json=update_payload, headers=lecturer_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "AVL Tree Search Time Complexity (Updated)"
    assert r.json()["default_points"] == 3.0

    # 13. Lecturer bulk imports questions
    bulk_payload = [
        {
            "category_id": category_id,
            "title": "B-Tree Branching",
            "prompt": "What is the primary motivation for using B-Trees in database index engines?",
            "question_type": "essay",
            "difficulty_level": "advanced",
            "default_points": 5.0,
            "tags": ["b-tree", "database"]
        },
        {
            "category_id": category_id,
            "title": "BST Inorder Traversal Property",
            "prompt": "In-order traversal of a valid Binary Search Tree produces elements in sorted order.",
            "question_type": "true_false",
            "difficulty_level": "beginner",
            "default_points": 1.0,
            "tags": ["bst", "traversal"],
            "options": [
                {"id": "t", "text": "True", "is_correct": True},
                {"id": "f", "text": "False", "is_correct": False}
            ]
        }
    ]
    r = await client.post(f"/api/courses/{course.id}/questions/bulk-import", json=bulk_payload, headers=lecturer_headers)
    assert r.status_code == 201
    assert len(r.json()) == 2

    # 14. Lecturer deletes a question item
    r = await client.delete(f"/api/questions/{q1_id}", headers=lecturer_headers)
    assert r.status_code == 204

    # Verify deleted question is gone
    r = await client.get(f"/api/questions/{q1_id}", headers=lecturer_headers)
    assert r.status_code == 404
