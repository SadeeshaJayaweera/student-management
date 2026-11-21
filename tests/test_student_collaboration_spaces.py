from datetime import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, Lecturer, Course, Enrollment,
    CollaborationWorkspace, CollaborationWorkspaceMember
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_collaboration_spaces_complete(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student A and Student B
    student_a_user = User(
        email="collab_a@nsbm.ac.lk",
        username="collab_a",
        hashed_password=hash_password("Pass123!"),
        full_name="Alice Developer",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student_b_user = User(
        email="collab_b@nsbm.ac.lk",
        username="collab_b",
        hashed_password=hash_password("Pass123!"),
        full_name="Bob Engineer",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([student_a_user, student_b_user])
    await test_session.commit()

    student_a = Student(
        user_id=student_a_user.id,
        student_id="STU-COL-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=1,
        gpa=3.8,
        credits_earned=75,
    )
    student_b = Student(
        user_id=student_b_user.id,
        student_id="STU-COL-02",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=1,
        gpa=3.6,
        credits_earned=75,
    )
    course = Course(
        course_code="SE315",
        title="Enterprise Architecture",
        description="Microservices and cloud systems",
        credits=3,
        department="Software Engineering",
        faculty="Computing",
        semester=1,
        year=3,
    )
    test_session.add_all([student_a, student_b, course])
    await test_session.commit()

    token_a = create_access_token({"sub": str(student_a_user.id), "role": "student"})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    token_b = create_access_token({"sub": str(student_b_user.id), "role": "student"})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. Student A creates a workspace
    create_resp = await client.post(
        "/api/collaboration/workspaces",
        json={
            "course_id": course.id,
            "name": "Cloud Microservices Capstone",
            "description": "Collaborative project space for distributed order processing",
            "topic": "Event-Driven Saga Pattern",
            "visibility": "course_public",
            "meeting_link": "https://meet.google.com/abc-defg-hij",
        },
        headers=headers_a,
    )
    assert create_resp.status_code == 201
    w_data = create_resp.json()
    assert w_data["name"] == "Cloud Microservices Capstone"
    assert w_data["owner_student_id"] == student_a.id
    assert w_data["members_count"] == 1
    join_code = w_data["join_code"]
    workspace_id = w_data["id"]

    # 3. Student B joins using the join code
    join_resp = await client.post(
        "/api/collaboration/workspaces/join",
        json={"join_code": join_code},
        headers=headers_b,
    )
    assert join_resp.status_code == 200
    joined_data = join_resp.json()
    assert joined_data["id"] == workspace_id
    assert joined_data["members_count"] == 2

    # 4. Student B posts a discussion message
    msg_resp = await client.post(
        f"/api/collaboration/workspaces/{workspace_id}/messages",
        json={
            "content": "Hey Alice! I have drafted the choreography diagram.",
            "pinned": True,
        },
        headers=headers_b,
    )
    assert msg_resp.status_code == 201
    msg_data = msg_resp.json()
    assert msg_data["content"] == "Hey Alice! I have drafted the choreography diagram."
    assert msg_data["sender_name"] == "Bob Engineer"

    # 5. Student A shares a code snippet asset
    asset_resp = await client.post(
        f"/api/collaboration/workspaces/{workspace_id}/assets",
        json={
            "title": "Kafka Producer Config",
            "asset_type": "code_snippet",
            "content": "bootstrap_servers='kafka:9092'\nacks='all'",
        },
        headers=headers_a,
    )
    assert asset_resp.status_code == 201
    asset_data = asset_resp.json()
    assert asset_data["title"] == "Kafka Producer Config"
    assert asset_data["asset_type"] == "code_snippet"

    # 6. Student A updates the shared whiteboard canvas
    whiteboard_resp = await client.put(
        f"/api/collaboration/workspaces/{workspace_id}/whiteboard",
        json={
            "whiteboard_data": {
                "nodes": [{"id": "n1", "label": "Order Service", "x": 100, "y": 200}],
                "notes": ["Remember idempotent consumer keys"],
            }
        },
        headers=headers_a,
    )
    assert whiteboard_resp.status_code == 200
    assert whiteboard_resp.json()["success"] is True

    # 7. Query Workspace Detail and verify all members, assets, messages, and whiteboard
    detail_resp = await client.get(
        f"/api/collaboration/workspaces/{workspace_id}",
        headers=headers_b,
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["members"]) == 2
    assert len(detail["assets"]) == 1
    assert len(detail["recent_messages"]) == 1
    assert detail["shared_whiteboard_data"]["nodes"][0]["label"] == "Order Service"
