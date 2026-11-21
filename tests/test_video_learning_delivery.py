import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course, CourseModule, CourseLesson, Student, Enrollment
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_video_learning_delivery_and_telemetry(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin user
    admin_user = User(
        email="video_admin@nsbm.ac.lk",
        username="video_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Video Admin",
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
            "course_code": "CS405",
            "title": "Full-Stack System Design",
            "credits": 4,
            "semester": 1,
            "year": 4,
            "max_students": 50
        }
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    # 3. Create Video with Chapters and Captions
    v_res = await client.post(
        f"/api/courses/{course_id}/videos",
        headers=admin_headers,
        json={
            "title": "Lecture 1: Cache Coherence & Write Invalidation",
            "description": "Deep-dive into MESI protocol and cache invalidation patterns.",
            "provider": "hls",
            "video_url": "https://stream.nsbm.ac.lk/hls/cs405-lec1/master.m3u8",
            "duration_seconds": 3600,
            "thumbnail_url": "https://stream.nsbm.ac.lk/thumbs/cs405-lec1.jpg",
            "captions_track": [
                {"label": "English", "srclang": "en", "src": "https://stream.nsbm.ac.lk/captions/cs405-en.vtt"}
            ],
            "chapters": [
                {"timestamp_seconds": 0, "title": "Overview and Hardware Caches"},
                {"timestamp_seconds": 600, "title": "The MESI Protocol States"},
                {"timestamp_seconds": 1800, "title": "Write-through vs Write-back Analysis"}
            ],
            "is_published": True
        }
    )
    assert v_res.status_code == 201
    video_data = v_res.json()
    video_id = video_data["id"]
    assert video_data["duration_seconds"] == 3600
    assert len(video_data["chapters"]) == 3
    assert len(video_data["captions_track"]) == 1

    # 4. Setup Enrolled Student & Non-enrolled Student
    enrolled_u = User(
        email="enrolled_v@nsbm.ac.lk",
        username="enrolled_v",
        hashed_password=hash_password("Pass123!"),
        full_name="Enrolled Video Student",
        role=UserRole.STUDENT,
        is_active=True
    )
    outsider_u = User(
        email="outsider_v@nsbm.ac.lk",
        username="outsider_v",
        hashed_password=hash_password("Pass123!"),
        full_name="Outsider Video Student",
        role=UserRole.STUDENT,
        is_active=True
    )
    test_session.add_all([enrolled_u, outsider_u])
    await test_session.commit()
    await test_session.refresh(enrolled_u)
    await test_session.refresh(outsider_u)

    stu_enrolled = Student(
        user_id=enrolled_u.id,
        student_id="STU-VID-01",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        academic_standing="good_standing"
    )
    stu_outsider = Student(
        user_id=outsider_u.id,
        student_id="STU-VID-02",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
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

    # 5. Access Verification
    # Enrolled student can list videos
    list_res = await client.get(f"/api/courses/{course_id}/videos", headers=enrolled_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Outsider student gets 403
    out_list = await client.get(f"/api/courses/{course_id}/videos", headers=outsider_headers)
    assert out_list.status_code == 403

    # 6. Playback Progress Telemetry Tracking
    # Progress update 1: watch up to 600 seconds, add bookmark
    prog1_res = await client.post(
        f"/api/videos/{video_id}/progress",
        headers=enrolled_headers,
        json={
            "position_seconds": 600,
            "add_bookmark": {"timestamp_seconds": 600, "title": "MESI start"}
        }
    )
    assert prog1_res.status_code == 200
    prog1 = prog1_res.json()
    assert prog1["last_position_seconds"] == 600
    assert prog1["max_watched_seconds"] == 600
    assert prog1["is_completed"] is False
    assert len(prog1["bookmarks"]) == 1

    # Progress update 2: watch up to 3420 seconds (95% of 3600), add note -> triggers auto-completion
    prog2_res = await client.post(
        f"/api/videos/{video_id}/progress",
        headers=enrolled_headers,
        json={
            "position_seconds": 3420,
            "add_note": {"timestamp_seconds": 1800, "note": "Check write-back queue latency"}
        }
    )
    assert prog2_res.status_code == 200
    prog2 = prog2_res.json()
    assert prog2["last_position_seconds"] == 3420
    assert prog2["max_watched_seconds"] == 3420
    assert prog2["watch_percentage"] >= 95.0
    assert prog2["is_completed"] is True
    assert prog2["completed_at"] is not None
    assert len(prog2["notes"]) == 1

    # Check student video details returns populated playback progress
    detail_res = await client.get(f"/api/videos/{video_id}", headers=enrolled_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["playback_progress"] is not None
    assert detail["playback_progress"]["is_completed"] is True

    # 7. Student cannot delete or create video
    stu_del = await client.delete(f"/api/videos/{video_id}", headers=enrolled_headers)
    assert stu_del.status_code == 403

    stu_create = await client.post(
        f"/api/courses/{course_id}/videos",
        headers=enrolled_headers,
        json={"title": "Hacked Video", "video_url": "https://evil.com/video.mp4"}
    )
    assert stu_create.status_code == 403
