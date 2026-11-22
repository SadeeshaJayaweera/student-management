from datetime import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, News, NewsCategory
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_campus_news_and_media_publication(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, and Student users
    admin_user = User(
        email="press_editor@nsbm.ac.lk",
        username="press_editor",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Prof. Press Director",
        role=UserRole.ADMIN,
        is_active=True,
    )
    student_user = User(
        email="student_reporter@nsbm.ac.lk",
        username="student_reporter",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Kasun Jayawardena",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([admin_user, student_user])
    await test_session.commit()

    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})
    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 2. Admin creates and publishes an official news article
    article_payload = {
        "title": "NSBM Wins National Green University Innovation Award 2026",
        "category": "academic",
        "summary": "NSBM Green University was recognized at the National Sustainable Architecture & Tech Awards.",
        "content": "Full article: The ceremony highlighted our net-zero campus infrastructure and AI-driven energy grid.",
        "target_audience": "all",
        "cover_image_url": "https://nsbm.ac.lk/images/green-award.jpg",
        "is_featured": True,
        "status": "published",
        "tags": ["sustainability", "awards", "innovation"],
    }
    res = await client.post("/api/news-publication/articles", json=article_payload, headers=admin_headers)
    assert res.status_code == 201
    art_data = res.json()
    assert art_data["title"] == article_payload["title"]
    assert art_data["status"] == "published"
    assert art_data["is_published"] is True
    assert art_data["is_featured"] is True
    article_id = art_data["id"]
    slug = art_data["slug"]

    # 3. Student reporter submits a draft story for review
    student_draft_payload = {
        "title": "Robotics Club Showcases Autonomous Drone Fleet",
        "category": "research",
        "summary": "Engineering students demonstrate obstacle-navigating drones in the quad.",
        "content": "Detailed overview of the flight control algorithms and telemetry sensors.",
        "target_audience": "students",
        "status": "published",  # Non-admin status should automatically become 'submitted'
        "is_featured": False,
    }
    draft_res = await client.post("/api/news-publication/articles", json=student_draft_payload, headers=student_headers)
    assert draft_res.status_code == 201
    draft_data = draft_res.json()
    assert draft_data["status"] == "submitted"
    assert draft_data["is_published"] is False
    draft_id = draft_data["id"]

    # 4. Admin approves and publishes the student's submission
    publish_res = await client.put(f"/api/news-publication/articles/{draft_id}/publish", headers=admin_headers)
    assert publish_res.status_code == 200
    assert publish_res.json()["status"] == "published"
    assert publish_res.json()["is_published"] is True

    # 5. Attach rich media gallery item to the published article
    media_payload = {
        "title": "Award Presentation Ceremony Photo",
        "media_type": "image",
        "media_url": "https://nsbm.ac.lk/media/award-ceremony.jpg",
        "caption": "Vice Chancellor receiving the trophy alongside faculty deans",
        "sort_order": 1,
    }
    media_res = await client.post(f"/api/news-publication/articles/{article_id}/media", json=media_payload, headers=admin_headers)
    assert media_res.status_code == 201
    assert media_res.json()["title"] == media_payload["title"]

    # 6. Student views the article by slug and view counter increments
    detail_res = await client.get(f"/api/news-publication/articles/{slug}", headers=student_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["views"] >= 1
    assert len(detail_res.json()["gallery"]) == 1

    # 7. Student reacts/applauds the article
    react_res = await client.post(f"/api/news-publication/articles/{article_id}/react?reaction_type=like", headers=student_headers)
    assert react_res.status_code == 200
    assert react_res.json()["liked"] is True
    assert react_res.json()["likes_count"] == 1

    # Toggling again unlikes
    react_res2 = await client.post(f"/api/news-publication/articles/{article_id}/react?reaction_type=like", headers=student_headers)
    assert react_res2.status_code == 200
    assert react_res2.json()["liked"] is False
    assert react_res2.json()["likes_count"] == 0

    # Toggle back on for stats
    await client.post(f"/api/news-publication/articles/{article_id}/react?reaction_type=like", headers=student_headers)

    # 8. Student posts a comment
    comment_payload = {"content": "Incredible milestone for NSBM! Well deserved recognition."}
    comment_res = await client.post(f"/api/news-publication/articles/{article_id}/comments", json=comment_payload, headers=student_headers)
    assert comment_res.status_code == 201
    assert comment_res.json()["content"] == comment_payload["content"]
    assert comment_res.json()["user_name"] == student_user.full_name

    # 9. List published articles with filters
    list_res = await client.get("/api/news-publication/articles?status_filter=published&category=academic", headers=student_headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(a["id"] == article_id for a in items)

    # 10. Check media publication stats
    stats_res = await client.get("/api/news-publication/stats", headers=student_headers)
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["total_articles"] >= 2
    assert stats_data["total_views"] >= 1
    assert stats_data["total_likes"] >= 1
    assert "academic" in stats_data["category_breakdown"]
