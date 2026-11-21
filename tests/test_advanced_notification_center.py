import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Notification, NotificationPreference
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_advanced_notification_center_complete(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student User, Lecturer User, and Admin User
    student_user = User(
        email="notif_student@nsbm.ac.lk",
        username="notif_student",
        hashed_password=hash_password("Pass123!"),
        full_name="Kasun Bandara",
        role=UserRole.STUDENT,
        is_active=True,
    )
    admin_user = User(
        email="notif_admin@nsbm.ac.lk",
        username="notif_admin",
        hashed_password=hash_password("Pass123!"),
        full_name="System Administrator",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add_all([student_user, admin_user])
    await test_session.commit()

    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})

    student_headers = {"Authorization": f"Bearer {student_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Check Preferences Defaults & Update
    prefs_res = await client.get("/api/notifications/preferences", headers=student_headers)
    assert prefs_res.status_code == 200
    prefs_data = prefs_res.json()
    assert prefs_data["in_app_enabled"] is True
    assert prefs_data["email_enabled"] is True
    assert prefs_data["quiet_hours_enabled"] is False

    # Update preferences
    pref_update_res = await client.put(
        "/api/notifications/preferences",
        headers=student_headers,
        json={
            "sms_enabled": True,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "23:00",
            "quiet_hours_end": "06:30",
        },
    )
    assert pref_update_res.status_code == 200
    updated_prefs = pref_update_res.json()
    assert updated_prefs["sms_enabled"] is True
    assert updated_prefs["quiet_hours_enabled"] is True
    assert updated_prefs["quiet_hours_start"] == "23:00"

    # 3. Create Notifications for Student
    n1_res = await client.post(
        "/api/notifications",
        headers=admin_headers,
        json={
            "user_id": student_user.id,
            "title": "Assignment 2 Due Tomorrow",
            "message": "Submit your coursework before 11:59 PM.",
            "notification_type": "warning",
            "category": "deadline",
            "priority": "urgent",
            "link": "/assignments/2",
        },
    )
    assert n1_res.status_code == 201
    n1_id = n1_res.json()["id"]

    n2_res = await client.post(
        "/api/notifications",
        headers=admin_headers,
        json={
            "user_id": student_user.id,
            "title": "Semester 1 Grades Published",
            "message": "Your results for Database Systems have been posted.",
            "notification_type": "info",
            "category": "academic",
            "priority": "normal",
            "link": "/grades",
        },
    )
    assert n2_res.status_code == 201
    n2_id = n2_res.json()["id"]

    # 4. Check Stats
    stats_res = await client.get("/api/notifications/stats", headers=student_headers)
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["total_unread"] == 2
    assert stats_data["unread_by_category"].get("deadline") == 1
    assert stats_data["unread_by_category"].get("academic") == 1
    assert stats_data["unread_by_priority"].get("urgent") == 1

    # 5. List with Category & Priority Filters
    list_all = await client.get("/api/notifications", headers=student_headers)
    assert list_all.status_code == 200
    assert len(list_all.json()) == 2
    # Urgent item should be sorted first
    assert list_all.json()[0]["priority"] == "urgent"

    list_deadline = await client.get("/api/notifications?category=deadline", headers=student_headers)
    assert list_deadline.status_code == 200
    assert len(list_deadline.json()) == 1
    assert list_deadline.json()[0]["id"] == n1_id

    list_urgent = await client.get("/api/notifications?priority=urgent", headers=student_headers)
    assert list_urgent.status_code == 200
    assert len(list_urgent.json()) == 1
    assert list_urgent.json()[0]["id"] == n1_id

    # 6. Mark Single or Batch Read
    batch_read_res = await client.post(
        "/api/notifications/batch-read",
        headers=student_headers,
        json={"notification_ids": [n1_id]},
    )
    assert batch_read_res.status_code == 200

    # Verify unread count decreased to 1
    stats_after_res = await client.get("/api/notifications/stats", headers=student_headers)
    assert stats_after_res.json()["total_unread"] == 1

    # Mark remaining read
    mark_all_res = await client.post("/api/notifications/batch-read", headers=student_headers)
    assert mark_all_res.status_code == 200
    stats_empty_res = await client.get("/api/notifications/stats", headers=student_headers)
    assert stats_empty_res.json()["total_unread"] == 0

    # 7. Delete Notification Item
    del_res = await client.delete(f"/api/notifications/{n1_id}", headers=student_headers)
    assert del_res.status_code == 200
    assert del_res.json()["deleted_id"] == n1_id

    # 8. Broadcast Notification (Admin sends to all students)
    # Student cannot broadcast (forbidden)
    student_broadcast_res = await client.post(
        "/api/notifications/broadcast",
        headers=student_headers,
        json={
            "title": "Unauthorized Alert",
            "message": "Testing permission denial",
        },
    )
    assert student_broadcast_res.status_code == 403

    # Admin broadcasts successfully
    admin_broadcast_res = await client.post(
        "/api/notifications/broadcast",
        headers=admin_headers,
        json={
            "title": "Campus Closed for Sports Festival",
            "message": "All lectures tomorrow will be held online.",
            "notification_type": "info",
            "category": "announcement",
            "priority": "high",
            "target_role": "student",
            "link": "/sports",
        },
    )
    assert admin_broadcast_res.status_code == 201
    assert admin_broadcast_res.json()["status"] == "broadcast_sent"
    assert admin_broadcast_res.json()["recipients_count"] >= 1

    # Student now receives the broadcast announcement
    student_notifs_after = await client.get("/api/notifications?category=announcement", headers=student_headers)
    assert student_notifs_after.status_code == 200
    assert any("Sports Festival" in item["title"] for item in student_notifs_after.json())
