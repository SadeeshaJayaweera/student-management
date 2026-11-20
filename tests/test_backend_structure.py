"""
NSBM EduSphere — Backend Structure & Core Integration Tests
Verifies health check, modular core dependencies, and service-backed authentication
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Verify system health endpoint returns 200 and valid JSON"""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "app" in data


@pytest.mark.asyncio
async def test_auth_login_success(client: AsyncClient, seeded_user):
    """Verify login works through modernized AuthService and returns bearer token"""
    response = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_auth_login_invalid_password(client: AsyncClient, seeded_user):
    """Verify login fails with invalid credentials"""
    response = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "WrongPassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_register_and_login(client: AsyncClient):
    """Verify user registration and subsequent login workflow"""
    register_payload = {
        "email": "newstudent@nsbm.ac.lk",
        "username": "newstudent",
        "password": "SecurePassword@123",
        "full_name": "New Student",
        "role": "student",
    }
    reg_response = await client.post("/api/auth/register", json=register_payload)
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert reg_data["username"] == "newstudent"
    assert reg_data["role"] == "student"

    # Now login with the newly created account
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "newstudent", "password": "SecurePassword@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
