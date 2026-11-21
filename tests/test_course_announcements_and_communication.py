from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course, Student, Enrollment
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_course_announcements_lifecycle_and_acknowledgement(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin user
    admin_user = User(
        email="ann_admin@nsbm.ac.lk",
        username="ann_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Announcement Admin",
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
            "course_code": "CS410",
            "title": "Enterprise Cloud Architecture",
            "credits": 4,
            "semester": 1,
            "year": 4,
            "max_students": 60
        }
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    # 3. Post Announcements
    # Ann 1: Standard unpinned
    a1_res = await client.post(
        f"/api/courses/{course_id}/announcements",
        headers=admin_headers,
        json={
            "title": "Welcome to CS410",
            "content": "Please review the syllabus and join the discussion forum.",
            "priority": "normal",
            "is_pinned": False
        }
    )
    assert a1_res.status_code == 201
    ann1_id = a1_res.json()["id"]

    # Ann 2: Urgent pinned requiring acknowledgement
    a2_res = await client.post(
        f"/api/courses/{course_id}/announcements",
        headers=admin_headers,
        json={
            "title": "URGENT: Lab Exam Schedule Change",
            "content": "Lab Exam shifted to Thursday 10:00 AM. Attendance is mandatory.",
            "priority": "urgent",
            "is_pinned": True,
            "requires_acknowledgement": True
        }
    )
    assert a2_res.status_code == 201
    ann2_id = a2_res.json()["id"]

    # Ann 3: Scheduled in the future (drip)
    future_time = (datetime.utcnow() + timedelta(days=5)).isoformat()
    a3_res = await client.post(
        f"/api/courses/{course_id}/announcements",
        headers=admin_headers,
        json={
            "title": "Upcoming Guest Lecture",
            "content": "Guest lecture by industry architect.",
            "priority": "important",
            "published_at": future_time
        }
    )
    assert a3_res.status_code == 201
    ann3_id = a3_res.json()["id"]

    # 4. Setup Enrolled Student & Outsider Student
    enrolled_u = User(
        email="enrolled_ann@nsbm.ac.lk",
        username="enrolled_ann",
        hashed_password=hash_password("Pass123!"),
        full_name="Enrolled Student",
        role=UserRole.STUDENT,
        is_active=True
    )
    outsider_u = User(
        email="outsider_ann@nsbm.ac.lk",
        username="outsider_ann",
        hashed_password=hash_password("Pass123!"),
        full_name="Outsider Student",
        role=UserRole.STUDENT,
        is_active=True
    )
    test_session.add_all([enrolled_u, outsider_u])
    await test_session.commit()
    await test_session.refresh(enrolled_u)
    await test_session.refresh(outsider_u)

    stu_enrolled = Student(
        user_id=enrolled_u.id,
        student_id="STU-ANN-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Cloud Computing",
        academic_standing="good_standing"
    )
    stu_outsider = Student(
        user_id=outsider_u.id,
        student_id="STU-ANN-02",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Cloud Computing",
        academic_standing="good_standing"
    )
    test_session.add_all([stu_enrolled, stu_outsider])
    await test_session.commit()
    await test_session.refresh(stu_enrolled)
    await test_session.refresh(stu_outsider)

    enr = Enrollment(student_id=stu_enrolled.id, course_id=course_id, status="active")
    test_session.add(enr)
    await test_session.commit()

    enrolled_token = create_access_token({"sub": str(enrolled_u.id), "role": enrolled_u.role.value})
    enrolled_headers = {"Authorization": f"Bearer {enrolled_token}"}

    outsider_token = create_access_token({"sub": str(outsider_u.id), "role": outsider_u.role.value})
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    # 5. Student Feed & Ordering Verification
    feed_res = await client.get(f"/api/courses/{course_id}/announcements", headers=enrolled_headers)
    assert feed_res.status_code == 200
    feed = feed_res.json()
    # Student sees 2 published announcements (future scheduled one is hidden)
    assert len(feed) == 2
    # Pinned urgent announcement appears FIRST
    assert feed[0]["id"] == ann2_id
    assert feed[0]["is_pinned"] is True
    assert feed[0]["priority"] == "urgent"
    assert feed[0]["is_acknowledged"] is False
    assert feed[1]["id"] == ann1_id

    # Outsider student cannot access announcements
    out_res = await client.get(f"/api/courses/{course_id}/announcements", headers=outsider_headers)
    assert out_res.status_code == 403

    # 6. Student Acknowledges Urgent Announcement
    ack_res = await client.post(
        f"/api/announcements/{ann2_id}/acknowledge",
        headers=enrolled_headers
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["announcement_id"] == ann2_id
    assert ack_res.json()["student_id"] == stu_enrolled.id

    # Verify updated feed reflects is_acknowledged = True
    feed2_res = await client.get(f"/api/courses/{course_id}/announcements", headers=enrolled_headers)
    assert feed2_res.status_code == 200
    feed2 = feed2_res.json()
    assert feed2[0]["is_acknowledged"] is True
    assert feed2[0]["acknowledgements_count"] == 1

    # 7. Workspace Hub Feed Integration
    ws_res = await client.get(f"/api/courses/{course_id}/workspace", headers=enrolled_headers)
    assert ws_res.status_code == 200
    ws = ws_res.json()
    assert len(ws["recent_announcements"]) >= 1
    recent_ids = [a["id"] for a in ws["recent_announcements"]]
    assert ann2_id in recent_ids

    # 8. Student cannot create or delete announcements
    stu_create = await client.post(
        f"/api/courses/{course_id}/announcements",
        headers=enrolled_headers,
        json={"title": "Hacked", "content": "Fake news"}
    )
    assert stu_create.status_code == 403

    stu_del = await client.delete(f"/api/announcements/{ann1_id}", headers=enrolled_headers)
    assert stu_del.status_code == 403
