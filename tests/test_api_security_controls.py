"""
NSBM EduSphere — API Security Controls Unit & Integration Tests
Tests OWASP secure headers, body payload size limiting (413),
and sliding-window rate limiting (429 Too Many Requests).
"""
import pytest
from httpx import AsyncClient

from backend.core.rate_limit import rate_limiter


@pytest.mark.asyncio
async def test_security_headers_present_on_responses(client: AsyncClient):
    """Verify responses include OWASP-compliant security headers and strip server banner"""
    response = await client.get("/api/health")
    assert response.status_code == 200

    # Mandatory security headers
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in response.headers.get("content-security-policy", "")
    assert "camera=()" in response.headers.get("permissions-policy", "")

    # Server banner suppression
    assert "server" not in response.headers
    assert "x-powered-by" not in response.headers


@pytest.mark.asyncio
async def test_oversized_payload_rejected_with_413(client: AsyncClient):
    """Verify oversized requests exceeding payload limit are rejected with 413 Payload Too Large"""
    # Simulate a 25MB body via Content-Length header
    fake_large_length = str(25 * 1024 * 1024)
    response = await client.post(
        "/api/auth/login",
        headers={"Content-Length": fake_large_length, "Content-Type": "application/json"},
        content=b"{}",
    )
    assert response.status_code == 413
    data = response.json()
    assert "exceeds" in data["detail"].lower()


@pytest.mark.asyncio
async def test_rate_limiter_sliding_window_enforcement():
    """Verify InMemoryRateLimiter sliding window tracking and 429 threshold"""
    rate_limiter.reset()

    # Allow 3 requests in a 10 second window
    key = "192.168.1.100"
    action = "test_action"

    allowed1, rem1, _ = rate_limiter.is_allowed(key, action, max_requests=3, window_seconds=10)
    assert allowed1 is True
    assert rem1 == 2

    allowed2, rem2, _ = rate_limiter.is_allowed(key, action, max_requests=3, window_seconds=10)
    assert allowed2 is True
    assert rem2 == 1

    allowed3, rem3, _ = rate_limiter.is_allowed(key, action, max_requests=3, window_seconds=10)
    assert allowed3 is True
    assert rem3 == 0

    # 4th request must be denied
    allowed4, rem4, retry_after = rate_limiter.is_allowed(key, action, max_requests=3, window_seconds=10)
    assert allowed4 is False
    assert rem4 == 0
    assert retry_after > 0


@pytest.mark.asyncio
async def test_endpoint_rate_limiting_http_behavior(client: AsyncClient):
    """Verify HTTP endpoint returns 429 when rate limit is active and exceeded"""
    rate_limiter.reset()

    # Hit /api/auth/login with x-enable-rate-limit header 21 times (limit is 20)
    for _ in range(20):
        await client.post(
            "/api/auth/login",
            data={"username": "dummy", "password": "dummypassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded", "X-Enable-Rate-Limit": "true"},
        )

    # 21st call must be 429 Too Many Requests
    resp21 = await client.post(
        "/api/auth/login",
        data={"username": "dummy", "password": "dummypassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Enable-Rate-Limit": "true"},
    )
    assert resp21.status_code == 429
    assert "retry-after" in resp21.headers

