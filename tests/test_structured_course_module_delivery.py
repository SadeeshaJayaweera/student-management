import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course, CourseModule, CourseLesson, Lecturer, Enrollment, Student
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_structured_course_module_and_lesson_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin user
    admin_user = User(
        email="module_admin@nsbm.ac.lk",
        username="module_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Module Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)
    await test_session.commit()
    await test_session.refresh(admin_user)

    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create Course
    c_res = await client.post(
        "/api/courses",
        headers=admin_headers,
        json={
            "course_code": "CS401",
            "title": "Advanced Distributed Systems",
            "credits": 4,
            "semester": 1,
            "year": 4,
            "max_students": 50
        }
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    # 3. Create Modules (Module 1: published, Module 2: draft, Module 3: drip locked)
    m1_res = await client.post(
        f"/api/courses/{course_id}/modules",
        headers=admin_headers,
        json={
            "order_index": 1,
            "title": "Module 1: Foundations of Distributed Consensus",
            "description": "Introduction to Paxos and Raft",
            "estimated_hours": 8.0,
            "status": "published"
        }
    )
    assert m1_res.status_code == 201
    mod1_id = m1_res.json()["id"]

    future_unlock = (datetime.utcnow() + timedelta(days=7)).isoformat()
    m2_res = await client.post(
        f"/api/courses/{course_id}/modules",
        headers=admin_headers,
        json={
            "order_index": 2,
            "title": "Module 2: Byzantine Fault Tolerance",
            "description": "PBFT and Tendermint protocols",
            "estimated_hours": 12.0,
            "status": "published",
            "unlock_at": future_unlock,
            "prerequisite_module_id": mod1_id
        }
    )
    assert m2_res.status_code == 201
    mod2_id = m2_res.json()["id"]

    m3_res = await client.post(
        f"/api/courses/{course_id}/modules",
        headers=admin_headers,
        json={
            "order_index": 3,
            "title": "Module 3: Advanced Vector Clocks (Draft)",
            "description": "Internal drafting",
            "estimated_hours": 6.0,
            "status": "draft"
        }
    )
    assert m3_res.status_code == 201
    mod3_id = m3_res.json()["id"]

    # 4. Add Lessons to Module 1
    l1_res = await client.post(
        f"/api/modules/{mod1_id}/lessons",
        headers=admin_headers,
        json={
            "title": "Lecture 1: State Machine Replication",
            "lesson_type": "reading",
            "content": "State machine replication is a general technique for implementing fault-tolerant services.",
            "estimated_minutes": 30,
            "order_index": 1,
            "is_required": True,
            "is_published": True
        }
    )
    assert l1_res.status_code == 201
    lesson1_id = l1_res.json()["id"]

    l2_res = await client.post(
        f"/api/modules/{mod1_id}/lessons",
        headers=admin_headers,
        json={
            "title": "Lecture 2: Raft Leader Election",
            "lesson_type": "video",
            "resource_url": "https://stream.nsbm.ac.lk/raft-lecture.mp4",
            "estimated_minutes": 45,
            "order_index": 2,
            "is_required": True,
            "is_published": True
        }
    )
    assert l2_res.status_code == 201
    lesson2_id = l2_res.json()["id"]

    # Unpublished draft lesson in Module 1
    l3_res = await client.post(
        f"/api/modules/{mod1_id}/lessons",
        headers=admin_headers,
        json={
            "title": "Draft Quiz: Consensus Fundamentals",
            "lesson_type": "quiz",
            "estimated_minutes": 20,
            "order_index": 3,
            "is_required": False,
            "is_published": False
        }
    )
    assert l3_res.status_code == 201
    lesson3_id = l3_res.json()["id"]

    # 5. Reorder Lessons within Module 1
    reorder_res = await client.put(
        f"/api/modules/{mod1_id}/lessons/reorder",
        headers=admin_headers,
        json={"lesson_ids": [lesson2_id, lesson1_id, lesson3_id]}
    )
    assert reorder_res.status_code == 200
    assert reorder_res.json()["reordered_count"] == 3

    # Check updated lesson order
    lessons_list = await client.get(f"/api/modules/{mod1_id}/lessons", headers=admin_headers)
    assert lessons_list.status_code == 200
    ordered_ids = [l["id"] for l in lessons_list.json()]
    assert ordered_ids == [lesson2_id, lesson1_id, lesson3_id]

    # 6. Reorder Modules within Course
    reorder_mod_res = await client.put(
        f"/api/courses/{course_id}/modules/reorder",
        headers=admin_headers,
        json={"module_ids": [mod2_id, mod1_id, mod3_id]}
    )
    assert reorder_mod_res.status_code == 200

    # 7. Test Student Access & Drip Lock Filtering
    student_user = User(
        email="student_cs401@nsbm.ac.lk",
        username="student_cs401",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Active Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)
    await test_session.commit()
    await test_session.refresh(student_user)

    student = Student(
        user_id=student_user.id,
        student_id="STU-CS401",
        faculty="Computing",
        department="Computer Science",
        program="BSc Software Engineering",
        academic_standing="good_standing"
    )
    test_session.add(student)
    await test_session.commit()
    await test_session.refresh(student)

    # Enroll student in course
    enrollment = Enrollment(student_id=student.id, course_id=course_id, status="active")
    test_session.add(enrollment)
    await test_session.commit()

    student_token = create_access_token({"sub": str(student_user.id), "role": student_user.role.value})
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Student listing modules:
    # - Draft module (mod3) should NOT be present.
    # - Published module (mod2) should have is_locked=True because unlock_at is in future.
    # - In mod1, draft lesson should NOT be visible.
    student_mods_res = await client.get(f"/api/courses/{course_id}/modules", headers=student_headers)
    assert student_mods_res.status_code == 200
    student_mods = student_mods_res.json()
    mod_ids = [m["id"] for m in student_mods]
    assert mod3_id not in mod_ids
    assert mod1_id in mod_ids
    assert mod2_id in mod_ids

    # Find mod2 in student response
    student_mod2 = next(m for m in student_mods if m["id"] == mod2_id)
    assert student_mod2["is_locked"] is True
    assert "Unlocks on" in student_mod2["lock_reason"]

    # Student listing lessons for mod1 should only see published lessons
    student_lessons_res = await client.get(f"/api/modules/{mod1_id}/lessons", headers=student_headers)
    assert student_lessons_res.status_code == 200
    s_lessons = student_lessons_res.json()
    assert len(s_lessons) == 2
    assert all(l["is_published"] for l in s_lessons)
    assert lesson3_id not in [l["id"] for l in s_lessons]

    # Student attempting to reorder should receive 403 Forbidden
    forbidden_reorder = await client.put(
        f"/api/courses/{course_id}/modules/reorder",
        headers=student_headers,
        json={"module_ids": [mod1_id, mod2_id]}
    )
    assert forbidden_reorder.status_code == 403
