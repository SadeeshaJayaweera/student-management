import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course, CourseModule, CourseLesson, Student, Enrollment
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_student_progress_and_completion_tracking_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin user
    admin_user = User(
        email="prog_admin@nsbm.ac.lk",
        username="prog_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Progress Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)
    await test_session.commit()
    await test_session.refresh(admin_user)

    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create Course with Sequential Modules
    c_res = await client.post(
        "/api/courses",
        headers=admin_headers,
        json={
            "course_code": "CS408",
            "title": "Cloud Native Microservices",
            "credits": 4,
            "semester": 2,
            "year": 4,
            "max_students": 40
        }
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    # Module 1 (Foundations, 2 lessons)
    m1_res = await client.post(
        f"/api/courses/{course_id}/modules",
        headers=admin_headers,
        json={
            "order_index": 1,
            "title": "Module 1: Container Orchestration",
            "status": "published"
        }
    )
    assert m1_res.status_code == 201
    mod1_id = m1_res.json()["id"]

    l1_res = await client.post(
        f"/api/modules/{mod1_id}/lessons",
        headers=admin_headers,
        json={"title": "Lesson 1.1: Kubernetes Architecture", "order_index": 1, "is_published": True}
    )
    l2_res = await client.post(
        f"/api/modules/{mod1_id}/lessons",
        headers=admin_headers,
        json={"title": "Lesson 1.2: Pods and Services", "order_index": 2, "is_published": True}
    )
    lesson1_id = l1_res.json()["id"]
    lesson2_id = l2_res.json()["id"]

    # Module 2 (Advanced, prerequisite = Module 1, 1 lesson)
    m2_res = await client.post(
        f"/api/courses/{course_id}/modules",
        headers=admin_headers,
        json={
            "order_index": 2,
            "title": "Module 2: Service Mesh & Istio",
            "prerequisite_module_id": mod1_id,
            "status": "published"
        }
    )
    assert m2_res.status_code == 201
    mod2_id = m2_res.json()["id"]

    l3_res = await client.post(
        f"/api/modules/{mod2_id}/lessons",
        headers=admin_headers,
        json={"title": "Lesson 2.1: Istio Traffic Management", "order_index": 1, "is_published": True}
    )
    lesson3_id = l3_res.json()["id"]

    # 3. Setup Enrolled Student
    student_user = User(
        email="student_cs408@nsbm.ac.lk",
        username="student_cs408",
        hashed_password=hash_password("Pass123!"),
        full_name="Cloud Student",
        role=UserRole.STUDENT,
        is_active=True
    )
    test_session.add(student_user)
    await test_session.commit()
    await test_session.refresh(student_user)

    student = Student(
        user_id=student_user.id,
        student_id="STU-CS408",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Cloud Computing",
        academic_standing="good_standing"
    )
    test_session.add(student)
    await test_session.commit()
    await test_session.refresh(student)

    enrollment = Enrollment(student_id=student.id, course_id=course_id, status="active")
    test_session.add(enrollment)
    await test_session.commit()

    student_token = create_access_token({"sub": str(student_user.id), "role": student_user.role.value})
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 4. Check Initial Progress Report
    initial_rep = await client.get(f"/api/courses/{course_id}/progress", headers=student_headers)
    assert initial_rep.status_code == 200
    rep1 = initial_rep.json()
    assert rep1["overall_progress_percentage"] == 0.0
    assert rep1["completed_lessons_count"] == 0
    assert rep1["total_lessons_count"] == 3
    assert rep1["is_course_completed"] is False
    # Module 1 unlocked, Module 2 locked due to prerequisite
    m1_state = next(m for m in rep1["modules"] if m["module_id"] == mod1_id)
    m2_state = next(m for m in rep1["modules"] if m["module_id"] == mod2_id)
    assert m1_state["is_locked"] is False
    assert m2_state["is_locked"] is True

    # 5. Complete Lesson 1 of Module 1
    p1 = await client.post(
        f"/api/lessons/{lesson1_id}/progress",
        headers=student_headers,
        json={"status": "completed", "time_spent_seconds": 900}
    )
    assert p1.status_code == 200

    mid_rep = await client.get(f"/api/courses/{course_id}/progress", headers=student_headers)
    assert mid_rep.status_code == 200
    rep2 = mid_rep.json()
    assert rep2["completed_lessons_count"] == 1
    assert rep2["total_time_spent_seconds"] == 900
    m1_mid = next(m for m in rep2["modules"] if m["module_id"] == mod1_id)
    assert m1_mid["progress_percentage"] == 50.0
    assert m1_mid["status"] == "in_progress"

    # 6. Complete Lesson 2 of Module 1 -> Completes Module 1 and unlocks Module 2!
    p2 = await client.post(
        f"/api/lessons/{lesson2_id}/progress",
        headers=student_headers,
        json={"status": "completed", "time_spent_seconds": 1200}
    )
    assert p2.status_code == 200

    unlock_rep = await client.get(f"/api/courses/{course_id}/progress", headers=student_headers)
    assert unlock_rep.status_code == 200
    rep3 = unlock_rep.json()
    m1_unlocked = next(m for m in rep3["modules"] if m["module_id"] == mod1_id)
    m2_unlocked = next(m for m in rep3["modules"] if m["module_id"] == mod2_id)
    assert m1_unlocked["status"] == "completed"
    assert m1_unlocked["progress_percentage"] == 100.0
    # Dynamic unlock of Module 2!
    assert m2_unlocked["is_locked"] is False

    # 7. Complete Lesson 3 in Module 2 -> Course 100% Complete!
    p3 = await client.post(
        f"/api/lessons/{lesson3_id}/progress",
        headers=student_headers,
        json={"status": "completed", "time_spent_seconds": 1500}
    )
    assert p3.status_code == 200

    final_rep = await client.get(f"/api/courses/{course_id}/progress", headers=student_headers)
    assert final_rep.status_code == 200
    rep4 = final_rep.json()
    assert rep4["overall_progress_percentage"] == 100.0
    assert rep4["completed_lessons_count"] == 3
    assert rep4["is_course_completed"] is True
    assert rep4["total_time_spent_seconds"] == 3600

    # 8. Faculty/Admin Roster and Individual Progress Inspection
    roster_res = await client.get(f"/api/courses/{course_id}/progress/roster", headers=admin_headers)
    assert roster_res.status_code == 200
    roster = roster_res.json()
    assert len(roster) == 1
    assert roster[0]["student_id"] == student.id
    assert roster[0]["progress_percentage"] == 100.0
    assert roster[0]["is_completed"] is True

    # Faculty inspects individual student
    stu_detail = await client.get(
        f"/api/courses/{course_id}/students/{student.id}/progress",
        headers=admin_headers
    )
    assert stu_detail.status_code == 200
    assert stu_detail.json()["is_course_completed"] is True

    # Student cannot view course roster
    stu_roster_forbidden = await client.get(
        f"/api/courses/{course_id}/progress/roster",
        headers=student_headers
    )
    assert stu_roster_forbidden.status_code == 403
