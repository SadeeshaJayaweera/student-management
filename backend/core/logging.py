"""
NSBM EduSphere — Centralized Structured Logging & Data Redaction
Structured JSON/Console logging with automated sensitive data redaction and correlation ID propagation
"""
import logging
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Set

# Sensitive keywords that must be masked anywhere in logs
SENSITIVE_KEYS: Set[str] = {
    "password", "hashed_password", "token", "access_token", "refresh_token",
    "secret", "secret_key", "authorization", "api_key", "google_api_key",
    "cookie", "session", "credit_card", "card_number", "cvv"
}


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redacts values for sensitive keys in dictionaries or lists"""
    if isinstance(data, dict):
        redacted = {}
        for k, v in data.items():
            if any(sensitive in str(k).lower() for sensitive in SENSITIVE_KEYS):
                redacted[k] = "***REDACTED***"
            elif isinstance(v, (dict, list)):
                redacted[k] = redact_sensitive_data(v)
            else:
                redacted[k] = v
        return redacted
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    return data


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects with ISO timestamps and correlation IDs"""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include tracing and context attributes if attached
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_obj["correlation_id"] = record.correlation_id
        if hasattr(record, "path") and record.path:
            log_obj["path"] = record.path
        if hasattr(record, "method") and record.method:
            log_obj["method"] = record.method
        if hasattr(record, "duration_ms") and record.duration_ms is not None:
            log_obj["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code") and record.status_code:
            log_obj["status_code"] = record.status_code

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Redact any extra dictionary properties
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_obj["data"] = redact_sensitive_data(record.extra_data)

        return json.dumps(log_obj)


def setup_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """Configure root and application loggers"""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    if json_logs:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        fmt = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        handler.setFormatter(logging.Formatter(fmt))

    root_logger.addHandler(handler)

    # Tone down noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)


# Application root logger instance
logger = logging.getLogger("edusphere")
