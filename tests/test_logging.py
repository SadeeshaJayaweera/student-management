"""
NSBM EduSphere — Centralized Logging & Redaction Tests
Verifies sensitive data masking, JSON formatting, and request tracing
"""
import json
import logging
from backend.core.logging import redact_sensitive_data, StructuredJsonFormatter


def test_sensitive_data_redaction():
    """Verify sensitive fields like passwords, tokens, and secrets are masked"""
    payload = {
        "username": "student01",
        "password": "SuperSecretPassword123",
        "email": "student@nsbm.ac.lk",
        "nested": {
            "access_token": "jwt.token.here",
            "api_key": "secret_api_key_value",
            "public_info": "safe_data"
        },
        "items": [
            {"card_number": "4111222233334444", "name": "Visa"}
        ]
    }
    redacted = redact_sensitive_data(payload)
    assert redacted["username"] == "student01"
    assert redacted["password"] == "***REDACTED***"
    assert redacted["email"] == "student@nsbm.ac.lk"
    assert redacted["nested"]["access_token"] == "***REDACTED***"
    assert redacted["nested"]["api_key"] == "***REDACTED***"
    assert redacted["nested"]["public_info"] == "safe_data"
    assert redacted["items"][0]["card_number"] == "***REDACTED***"
    assert redacted["items"][0]["name"] == "Visa"


def test_structured_json_formatter():
    """Verify StructuredJsonFormatter outputs valid parseable JSON with required attributes"""
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="edusphere.auth",
        level=logging.INFO,
        pathname="auth_service.py",
        lineno=42,
        msg="User authenticated successfully",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "trace-uuid-1234"
    record.path = "/api/auth/login"
    record.method = "POST"
    record.duration_ms = 45.2
    record.status_code = 200

    formatted_str = formatter.format(record)
    parsed = json.loads(formatted_str)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "edusphere.auth"
    assert parsed["message"] == "User authenticated successfully"
    assert parsed["correlation_id"] == "trace-uuid-1234"
    assert parsed["path"] == "/api/auth/login"
    assert parsed["method"] == "POST"
    assert parsed["duration_ms"] == 45.2
    assert parsed["status_code"] == 200
    assert "timestamp" in parsed
