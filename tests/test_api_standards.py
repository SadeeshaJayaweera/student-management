"""
NSBM EduSphere — API Standards & Versioning Integration Tests
Verifies correlation IDs, v1 versioning, response envelopes, and error formatting
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_correlation_id_generated_and_propagated(client: AsyncClient):
    """Verify X-Correlation-ID is automatically generated and returned in headers"""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert "x-correlation-id" in response.headers
    cid = response.headers["x-correlation-id"]
    assert len(cid) > 10

    # Also check envelope has the matching correlation_id
    body = response.json()
    assert body["success"] is True
    assert body["correlation_id"] == cid


@pytest.mark.asyncio
async def test_custom_correlation_id_preserved(client: AsyncClient):
    """Verify custom X-Correlation-ID supplied by client is echoed back"""
    custom_cid = "client-trace-id-abc-123"
    response = await client.get("/api/health", headers={"X-Correlation-ID": custom_cid})
    assert response.status_code == 200
    assert response.headers["x-correlation-id"] == custom_cid
    body = response.json()
    assert body["correlation_id"] == custom_cid


@pytest.mark.asyncio
async def test_v1_versioned_endpoint(client: AsyncClient):
    """Verify API v1 routes are available under /api/v1 prefix"""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"
    assert "environment" in body["data"]


@pytest.mark.asyncio
async def test_standardized_error_format_on_unauthorized(client: AsyncClient):
    """Verify 401 Unauthorized returns standardized APIErrorResponse schema"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent", "password": "WrongPassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert "error" in body
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "Invalid username" in body["error"]["message"]
    assert "detail" in body  # backward compatibility field
    assert "correlation_id" in body
    assert "timestamp" in body


@pytest.mark.asyncio
async def test_standardized_validation_error_format(client: AsyncClient):
    """Verify 422 RequestValidationError returns standardized APIErrorResponse schema"""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email"},  # missing required fields
    )
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in body["error"]
    assert "errors" in body["error"]["details"]
