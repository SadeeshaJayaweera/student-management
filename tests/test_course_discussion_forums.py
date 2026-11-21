import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course, Student, Lecturer, Enrollment
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_course_discussion_forums_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, Enrolled Student, and Unenrolled Student
    admin_user = User(
        email="forum_admin@nsbm.ac.lk",
        username="forum_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Forum Administrator",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="forum_lecturer@nsbm.ac.lk",
        username="forum_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Forum Master",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student1_user = User(
        email="forum_student1@nsbm.ac.lk",
        username="forum_student1",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Alice Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student1_user)

    student2_user = User(
        email="forum_student2@nsbm.ac.lk",
        username="forum_student2",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Bob Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student2_user)

    unenrolled_user = User(
        email="forum_outsider@nsbm.ac.lk",
        username="forum_outsider",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Charlie Outsider",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(unenrolled_user)
    await test_session.commit()

    # Create Lecturer and Student profiles
    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-FORUM-01",
        faculty="Computing",
        department="Software Engineering",
    )
    test_session.add(lecturer)

    student1 = Student(
        user_id=student1_user.id,
        student_id="STU-FORUM-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc SE",
        year_of_study=3,
        semester=1,
    )
    test_session.add(student1)

    student2 = Student(
        user_id=student2_user.id,
        student_id="STU-FORUM-02",
        faculty="Computing",
        department="Software Engineering",
        program="BSc SE",
        year_of_study=3,
        semester=1,
    )
    test_session.add(student2)
    await test_session.commit()

    # Auth headers
    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": lecturer_user.role.value})
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}

    student1_token = create_access_token({"sub": str(student1_user.id), "role": student1_user.role.value})
    student1_headers = {"Authorization": f"Bearer {student1_token}"}

    student2_token = create_access_token({"sub": str(student2_user.id), "role": student2_user.role.value})
    student2_headers = {"Authorization": f"Bearer {student2_token}"}

    outsider_token = create_access_token({"sub": str(unenrolled_user.id), "role": unenrolled_user.role.value})
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    # 2. Create Course and enroll student1 & student2
    c_res = await client.post(
        "/api/courses",
        headers=admin_headers,
        json={
            "course_code": "CS420",
            "title": "Distributed Systems & Cloud",
            "credits": 4,
            "semester": 1,
            "year": 4,
            "lecturer_id": lecturer.id,
        }
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    e1 = Enrollment(student_id=student1.id, course_id=course_id, status="active")
    e2 = Enrollment(student_id=student2.id, course_id=course_id, status="active")
    test_session.add_all([e1, e2])
    await test_session.commit()

    # 3. Category Management
    # Student attempts to create category -> 403 Forbidden
    cat_fail = await client.post(
        f"/api/courses/{course_id}/forums/categories",
        headers=student1_headers,
        json={"title": "Unauthorized Category", "description": "Should fail"}
    )
    assert cat_fail.status_code == 403

    # Lecturer creates Category 1 (General) & Category 2 (Project Q&A)
    cat1_res = await client.post(
        f"/api/courses/{course_id}/forums/categories",
        headers=lecturer_headers,
        json={"title": "General Q&A", "description": "General course discussions", "display_order": 1}
    )
    assert cat1_res.status_code == 201
    cat1_id = cat1_res.json()["id"]

    cat2_res = await client.post(
        f"/api/courses/{course_id}/forums/categories",
        headers=lecturer_headers,
        json={"title": "Assignments", "description": "Coursework help", "display_order": 2}
    )
    assert cat2_res.status_code == 201
    cat2_id = cat2_res.json()["id"]

    # 4. Thread Creation with Anti-XSS Sanitization
    # Student1 creates thread in General Q&A with XSS attempt
    xss_payload = "<script>alert('xss');</script>How does raft consensus prevent split-brain?<iframe src='bad.com'></iframe>"
    t1_res = await client.post(
        f"/api/courses/{course_id}/forums/threads",
        headers=student1_headers,
        json={
            "category_id": cat1_id,
            "title": "Raft Consensus and Split-Brain Protection",
            "content": xss_payload,
        }
    )
    assert t1_res.status_code == 201
    t1_data = t1_res.json()
    thread1_id = t1_data["id"]
    assert t1_data["is_pinned"] is False
    assert t1_data["author_name"] == "Alice Student"

    # Verify anti-XSS sanitized output in thread detail
    t1_detail = await client.get(
        f"/api/forums/threads/{thread1_id}",
        headers=student1_headers,
    )
    assert t1_detail.status_code == 200
    cleaned_content = t1_detail.json()["content"]
    assert "<script>" not in cleaned_content
    assert "<iframe>" not in cleaned_content
    assert "raft consensus" in cleaned_content

    # Lecturer pins Thread 1
    pin_res = await client.patch(
        f"/api/forums/threads/{thread1_id}",
        headers=lecturer_headers,
        json={"is_pinned": True}
    )
    assert pin_res.status_code == 200
    assert pin_res.json()["is_pinned"] is True

    # 5. Replies (Posts), Nested Comments, Instructor Endorsement & Solution Marking
    # Student2 replies to Thread 1
    post1_res = await client.post(
        f"/api/forums/threads/{thread1_id}/posts",
        headers=student2_headers,
        json={"content": "Split-brain is avoided because a leader requires a quorum of nodes (N/2 + 1) to commit logs."}
    )
    assert post1_res.status_code == 201
    post1_id = post1_res.json()["id"]

    # Student1 posts a nested reply thanking Student2
    post2_res = await client.post(
        f"/api/forums/threads/{thread1_id}/posts",
        headers=student1_headers,
        json={"content": "Thanks Bob, that makes complete sense!", "parent_post_id": post1_id}
    )
    assert post2_res.status_code == 201
    assert post2_res.json()["parent_post_id"] == post1_id

    # Lecturer endorses Student2's post as authoritative
    endorse_res = await client.post(
        f"/api/forums/posts/{post1_id}/endorse",
        headers=lecturer_headers,
    )
    assert endorse_res.status_code == 200
    assert endorse_res.json()["is_endorsed_by_instructor"] is True

    # Student1 (thread author) marks Student2's post as the accepted solution
    sol_res = await client.post(
        f"/api/forums/posts/{post1_id}/solution",
        headers=student1_headers,
    )
    assert sol_res.status_code == 200
    assert sol_res.json()["is_solution"] is True

    # 6. Reactions (Likes / Upvotes)
    # Alice upvotes Bob's post
    react_res = await client.post(
        f"/api/forums/posts/{post1_id}/react?reaction_type=like",
        headers=student1_headers,
    )
    assert react_res.status_code == 200
    assert react_res.json()["upvotes"] == 1
    assert react_res.json()["user_has_reacted"] is True

    # Alice clicks like again (toggle off)
    unreact_res = await client.post(
        f"/api/forums/posts/{post1_id}/react?reaction_type=like",
        headers=student1_headers,
    )
    assert unreact_res.status_code == 200
    assert unreact_res.json()["upvotes"] == 0
    assert unreact_res.json()["user_has_reacted"] is False

    # 7. Thread Locking Enforcement
    # Lecturer locks the thread
    lock_res = await client.patch(
        f"/api/forums/threads/{thread1_id}",
        headers=lecturer_headers,
        json={"is_locked": True}
    )
    assert lock_res.status_code == 200
    assert lock_res.json()["is_locked"] is True

    # Student attempts to post reply to locked thread -> 400 Bad Request
    locked_reply = await client.post(
        f"/api/forums/threads/{thread1_id}/posts",
        headers=student2_headers,
        json={"content": "Trying to reply to locked thread"}
    )
    assert locked_reply.status_code == 400

    # 8. BOLA Authorization Checks
    # Unenrolled outsider cannot access course forums
    out_cat = await client.get(
        f"/api/courses/{course_id}/forums/categories",
        headers=outsider_headers,
    )
    assert out_cat.status_code == 403

    out_thread = await client.get(
        f"/api/forums/threads/{thread1_id}",
        headers=outsider_headers,
    )
    assert out_thread.status_code == 403
