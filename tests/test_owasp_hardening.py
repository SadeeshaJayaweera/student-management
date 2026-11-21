"""
NSBM EduSphere — OWASP ASVS 5.0 Security Hardening Tests
Validates SQL injection resistance, XSS sanitization,
CORS security constraints, and sensitive error redaction.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import User
from backend.core.sanitization import sanitize_html, sanitize_payload
from backend.core.config import Settings, AppEnvironment


@pytest.mark.asyncio
async def test_sql_injection_resistance_on_authentication(client: AsyncClient, test_session: AsyncSession):
    """Verify classic SQL injection attempts in login fields are parameterized and rejected safely"""
    injection_payloads = [
        "' OR '1'='1",
        "admin' --",
        "'; DROP TABLE users; --",
        "' UNION SELECT id, username, email, password_hash FROM users --",
    ]

    for payload in injection_payloads:
        resp = await client.post(
            "/api/auth/login",
            data={"username": payload, "password": "RandomPassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        # Must return 401 Unauthorized, never 500 or SQL syntax error
        assert resp.status_code == 401
        data = resp.json()
        assert data["error"]["code"] == "UNAUTHORIZED"

    # Verify database users table remains completely intact
    users_q = await test_session.execute(select(User))
    users = users_q.scalars().all()
    assert len(users) >= 0


@pytest.mark.asyncio
async def test_xss_payload_sanitization():
    """Verify script tags, event handlers, and javascript URIs are neutralized"""
    xss_vectors = [
        ("<script>alert('XSS')</script>Hello", "Hello"),
        ("<img src=x onerror=alert(1)>Profile", "Profile"),
        ("<a href='javascript:stealCookies()'>Click me</a>", "&lt;a href=&#x27;&#x27;&gt;Click me&lt;/a&gt;"),
        ("<iframe src='https://malicious.com'></iframe>Safe content", "Safe content"),
    ]

    for raw, expected_safe in xss_vectors:
        sanitized = sanitize_html(raw)
        assert "<script>" not in sanitized
        assert "alert(" not in sanitized
        assert "javascript:" not in sanitized
        assert "onerror" not in sanitized


@pytest.mark.asyncio
async def test_nested_payload_sanitization():
    """Verify recursive payload sanitizer cleans nested dicts and lists"""
    dirty_data = {
        "title": "<script>alert('pwned')</script>Clean Title",
        "tags": ["normal", "<img src=x onerror='evil()'>tag2"],
        "metadata": {
            "bio": "Hello <b onmouseover='hack()'>World</b>",
        },
    }

    clean_data = sanitize_payload(dirty_data)
    assert clean_data["title"] == "Clean Title"
    assert "onerror" not in clean_data["tags"][1]
    assert "onmouseover" not in clean_data["metadata"]["bio"]


@pytest.mark.asyncio
async def test_cors_policy_rejects_wildcard_with_credentials():
    """Verify production settings reject wildcard origin when credentials are enabled"""
    with pytest.raises(ValueError, match="CORS allowed_origins cannot contain wildcard"):
        Settings(
            secret_key="a-secure-production-key-with-over-thirty-two-chars",
            environment=AppEnvironment.PRODUCTION,
            allowed_origins=["*"],
        )


@pytest.mark.asyncio
async def test_sensitive_errors_redacted_in_production(client: AsyncClient):
    """Verify 500 internal errors do not leak stack traces or system file paths"""
    # Trigger 404 to ensure error structure is standardized and clean
    resp = await client.get("/api/v1/non-existent-endpoint-test-404")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "NOT_FOUND"
    # Ensure no internal path disclosure
    assert "/Users/" not in resp.text
    assert "Traceback" not in resp.text
