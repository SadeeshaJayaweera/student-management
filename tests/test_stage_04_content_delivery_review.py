"""
NSBM EduSphere — Stage 04 Content Delivery Architecture End-to-End Review Test
Comprehensive verification of all 9 Stage 04 capabilities:
- Course Workspace Architecture (Change 31)
- Structured Course Module Delivery (Change 32)
- Rich Learning Content Authoring & Versioning (Change 33)
- Document & Media Management (Change 34)
- Video Learning Delivery & Playback Tracking (Change 35)
- Student Progress & Prerequisite Unlocking (Change 36)
- Course Announcements & Acknowledgements (Change 37)
- Collaborative Discussion Forums (Change 38)
- Virtual Classrooms & Live Session Attendance (Change 39)
"""
from datetime import datetime, timedelta
import io
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Lecturer, Student, Enrollment
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_stage_04_content_delivery_end_to_end_review(
    client: AsyncClient,
    test_session: AsyncSession
):
    # ── 1. Setup Academic Actors & Authorization ──────────────────────────────
    admin_user = User(
        email="stage04_admin@nsbm.ac.lk",
        username="stage04_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Stage 04 Administrator",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)

    lecturer_user = User(
        email="stage04_lecturer@nsbm.ac.lk",
        username="stage04_lecturer",
        hashed_password=hash_password("LecturerPass123!"),
        full_name="Prof. Delivery Architect",
        role=UserRole.LECTURER,
        is_active=True,
    )
    test_session.add(lecturer_user)

    student_user = User(
        email="stage04_student@nsbm.ac.lk",
        username="stage04_student",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Sophia Learner",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student_user)

    outsider_user = User(
        email="stage04_outsider@nsbm.ac.lk",
        username="stage04_outsider",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Lucas Outsider",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(outsider_user)
    await test_session.commit()

    lecturer = Lecturer(
        user_id=lecturer_user.id,
        lecturer_id="LEC-STAGE04-01",
        faculty="Computing",
        department="Software Engineering",
    )
    test_session.add(lecturer)

    student = Student(
        user_id=student_user.id,
        student_id="STU-STAGE04-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc SE",
        year_of_study=3,
        semester=2,
    )
    test_session.add(student)
    await test_session.commit()

    # JWT Tokens
    admin_headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}
    lecturer_headers = {"Authorization": f"Bearer {create_access_token({'sub': str(lecturer_user.id), 'role': lecturer_user.role.value})}"}
    student_headers = {"Authorization": f"Bearer {create_access_token({'sub': str(student_user.id), 'role': student_user.role.value})}"}
    outsider_headers = {"Authorization": f"Bearer {create_access_token({'sub': str(outsider_user.id), 'role': outsider_user.role.value})}"}

    # ── 2. Course Creation & Unified Workspace ────────────────────────────────
    c_res = await client.post(
        "/api/courses",
        headers=admin_headers,
        json={
            "course_code": "SE450",
            "title": "Enterprise Cloud Architecture Masterclass",
            "credits": 4,
            "semester": 2,
            "year": 4,
            "lecturer_id": lecturer.id,
        }
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    enrollment = Enrollment(student_id=student.id, course_id=course_id, status="active")
    test_session.add(enrollment)
    await test_session.commit()

    # Workspace BOLA check: outsider gets 403
    out_ws = await client.get(f"/api/courses/{course_id}/workspace", headers=outsider_headers)
    assert out_ws.status_code == 403

    # Student accesses initial workspace
    stu_ws = await client.get(f"/api/courses/{course_id}/workspace", headers=student_headers)
    assert stu_ws.status_code == 200
    assert stu_ws.json()["course_code"] == "SE450"

    # ── 3. Structured Module Delivery & Drip Lock Prerequisites ───────────────
    # Module 1 (Foundations)
    m1_res = await client.post(
        f"/api/courses/{course_id}/modules",
        headers=lecturer_headers,
        json={"title": "Module 1: Cloud Native Fundamentals", "order_index": 1, "status": "published"}
    )
    assert m1_res.status_code == 201
    m1_id = m1_res.json()["id"]

    # Lesson 1 in Module 1
    l1_res = await client.post(
        f"/api/modules/{m1_id}/lessons",
        headers=lecturer_headers,
        json={"title": "Container Orchestration Internals", "lesson_type": "text", "order_index": 1, "is_required": True}
    )
    assert l1_res.status_code == 201
    l1_id = l1_res.json()["id"]

    # Module 2 (Advanced) with Prerequisite = Module 1
    m2_res = await client.post(
        f"/api/courses/{course_id}/modules",
        headers=lecturer_headers,
        json={
            "title": "Module 2: Advanced Service Meshes",
            "order_index": 2,
            "status": "published",
            "prerequisite_module_id": m1_id,
        }
    )
    assert m2_res.status_code == 201
    m2_id = m2_res.json()["id"]

    # Check that Module 2 is initially locked for student
    m2_check = await client.get(f"/api/courses/{course_id}/modules", headers=student_headers)
    assert m2_check.status_code == 200
    modules_list = m2_check.json()
    m2_item = next(m for m in modules_list if m["id"] == m2_id)
    assert m2_item["is_locked"] is True

    # ── 4. Rich Content Authoring with Anti-XSS and Version Rollback ──────────
    # Authoring rich content with script injection attempts
    rich_res1 = await client.post(
        f"/api/lessons/{l1_id}/content",
        headers=lecturer_headers,
        json={
            "raw_content": "<h1>Core Principles</h1><p>Kubernetes scheduler selects nodes.</p><script>alert('xss')</script>",
            "content_format": "markdown",
            "change_summary": "Initial specification"
        }
    )
    assert rich_res1.status_code == 201
    cleaned_html = rich_res1.json()["rendered_content"]
    assert "<script>" not in cleaned_html
    assert "Kubernetes scheduler selects nodes." in cleaned_html

    # Authoring version 2
    rich_res2 = await client.post(
        f"/api/lessons/{l1_id}/content",
        headers=lecturer_headers,
        json={
            "raw_content": "<h1>Core Principles (v2)</h1><p>Updated scheduler algorithms.</p>",
            "content_format": "markdown",
            "change_summary": "Updated scheduler logic"
        }
    )
    assert rich_res2.status_code == 201
    assert rich_res2.json()["version_number"] == 2

    # Rollback to version 1
    rollback_res = await client.post(
        f"/api/lessons/{l1_id}/content/rollback/1",
        headers=lecturer_headers
    )
    assert rollback_res.status_code == 200
    assert "Kubernetes scheduler selects nodes." in rollback_res.json()["rendered_content"]

    # ── 5. Document & Media Management ────────────────────────────────────────
    doc_content = b"%PDF-1.4 Mock Kubernetes Architecture Blueprint Reference Document"
    doc_upload = await client.post(
        f"/api/courses/{course_id}/documents/upload",
        headers=lecturer_headers,
        files={"file": ("k8s-blueprint.pdf", io.BytesIO(doc_content), "application/pdf")},
        data={"title": "K8s Blueprint Guide", "module_id": str(m1_id), "lesson_id": str(l1_id)}
    )
    assert doc_upload.status_code == 201
    doc_id = doc_upload.json()["id"]

    # Student downloads document
    doc_dl = await client.get(f"/api/documents/{doc_id}/download", headers=student_headers)
    assert doc_dl.status_code == 200
    assert doc_dl.content == doc_content
    assert doc_dl.headers.get("x-content-type-options") == "nosniff"

    # ── 6. Video Learning Delivery & Playback Analytics ───────────────────────
    v_res = await client.post(
        f"/api/courses/{course_id}/videos",
        headers=lecturer_headers,
        json={
            "title": "Control Plane Deep Dive Video",
            "video_url": "https://cdn.nsbm.ac.lk/videos/k8s-control-plane.mp4",
            "provider": "self_hosted",
            "module_id": m1_id,
            "lesson_id": l1_id,
            "duration_seconds": 600,
            "required_watch_percentage": 90.0
        }
    )
    assert v_res.status_code == 201
    video_id = v_res.json()["id"]

    # Student plays video and reports 95% progress
    prog_res = await client.post(
        f"/api/videos/{video_id}/progress",
        headers=student_headers,
        json={"position_seconds": 570, "add_bookmark": {"time": 120, "note": "etcd quorum"}}
    )
    assert prog_res.status_code == 200
    assert prog_res.json()["is_completed"] is True
    assert prog_res.json()["watch_percentage"] >= 95.0

    # ── 7. Student Progress Rollup & Dynamic Prerequisite Unlocking ───────────
    # Complete Lesson 1
    les_prog = await client.post(
        f"/api/lessons/{l1_id}/progress",
        headers=student_headers,
        json={"status": "completed", "time_spent_seconds": 600}
    )
    assert les_prog.status_code == 200
    assert les_prog.json()["status"] == "completed"

    # Check overall course progress
    c_prog = await client.get(f"/api/courses/{course_id}/progress", headers=student_headers)
    assert c_prog.status_code == 200
    assert c_prog.json()["completed_lessons_count"] >= 1

    # Now verify that Module 2 was automatically unlocked by prerequisite rollup!
    m2_recheck = await client.get(f"/api/courses/{course_id}/modules", headers=student_headers)
    assert m2_recheck.status_code == 200
    m2_updated = next(m for m in m2_recheck.json() if m["id"] == m2_id)
    assert m2_updated["is_locked"] is False

    # ── 8. Announcements & Acknowledgements ───────────────────────────────────
    ann_res = await client.post(
        f"/api/courses/{course_id}/announcements",
        headers=lecturer_headers,
        json={
            "title": "URGENT: Architecture Exam Readiness Review",
            "content": "All students must review the blueprint document before Friday.",
            "priority": "urgent",
            "is_pinned": True,
            "requires_acknowledgement": True,
        }
    )
    assert ann_res.status_code == 201
    ann_id = ann_res.json()["id"]

    # Student acknowledges
    ack_res = await client.post(
        f"/api/announcements/{ann_id}/acknowledge",
        headers=student_headers
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["announcement_id"] == ann_id

    # ── 9. Discussion Forums with Threaded Answers & Solution ────────────────
    # Category
    fcat_res = await client.post(
        f"/api/courses/{course_id}/forums/categories",
        headers=lecturer_headers,
        json={"title": "Technical Q&A", "description": "Course technical discussions"}
    )
    assert fcat_res.status_code == 201
    cat_id = fcat_res.json()["id"]

    # Thread by Student
    fthread_res = await client.post(
        f"/api/courses/{course_id}/forums/threads",
        headers=student_headers,
        json={
            "category_id": cat_id,
            "title": "Optimizing etcd Disk I/O Latency",
            "content": "How do we ensure fsync latency remains under 10ms in high-scale deployments?",
        }
    )
    assert fthread_res.status_code == 201
    thread_id = fthread_res.json()["id"]

    # Reply by Lecturer
    fpost_res = await client.post(
        f"/api/forums/threads/{thread_id}/posts",
        headers=lecturer_headers,
        json={"content": "Mount the etcd data directory on a dedicated high-IOPS NVMe drive."}
    )
    assert fpost_res.status_code == 201
    post_id = fpost_res.json()["id"]

    # Endorse by Lecturer
    fendorse = await client.post(f"/api/forums/posts/{post_id}/endorse", headers=lecturer_headers)
    assert fendorse.status_code == 200
    assert fendorse.json()["is_endorsed_by_instructor"] is True

    # Mark as solution by Student (thread author)
    fsol = await client.post(f"/api/forums/posts/{post_id}/solution", headers=student_headers)
    assert fsol.status_code == 200
    assert fsol.json()["is_solution"] is True

    # ── 10. Virtual Classrooms & Live Session Synchronization ─────────────────
    session_start = (datetime.utcnow() + timedelta(days=1)).isoformat()
    session_end = (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat()

    vc_res = await client.post(
        f"/api/courses/{course_id}/live-sessions",
        headers=lecturer_headers,
        json={
            "title": "Live Interactive Lab: Service Mesh Chaos Testing",
            "provider": "google_meet",
            "join_url": "https://meet.google.com/xyz-abcd-efg",
            "host_url": "https://meet.google.com/xyz-abcd-efg?authuser=admin",
            "start_time": session_start,
            "end_time": session_end,
        }
    )
    assert vc_res.status_code == 201
    vc_id = vc_res.json()["id"]

    # Student joins session
    vc_join = await client.post(f"/api/live-sessions/{vc_id}/join", headers=student_headers)
    assert vc_join.status_code == 200
    assert vc_join.json()["join_url"] == "https://meet.google.com/xyz-abcd-efg"

    # Student leaves session
    vc_leave = await client.post(f"/api/live-sessions/{vc_id}/leave", headers=student_headers)
    assert vc_leave.status_code == 200
    assert vc_leave.json()["duration_minutes"] >= 1

    # Final Workspace check verifies all aggregates are present
    final_ws = await client.get(f"/api/courses/{course_id}/workspace", headers=student_headers)
    assert final_ws.status_code == 200
    final_data = final_ws.json()
    assert len(final_data["modules"]) == 2
    assert len(final_data["recent_announcements"]) >= 1
    assert len(final_data["upcoming_live_sessions"]) >= 1
