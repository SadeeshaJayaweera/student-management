"""
NSBM EduSphere — OWASP Input Sanitization & Anti-XSS Engine
Protects against Cross-Site Scripting (XSS), script injection,
and malicious markup in user-supplied strings and rich text.
"""
import re
import html
from typing import Any, Union, Dict, List


# Regex pattern to identify dangerous HTML tags and script execution vectors
_DANGEROUS_TAGS_PATTERN = re.compile(
    r"<\s*(script|iframe|object|embed|applet|meta|link|style)[^>]*>.*?<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_DANGEROUS_EMPTY_TAGS_PATTERN = re.compile(
    r"<\s*(script|iframe|object|embed|applet|meta|link|style)[^>]*/>",
    re.IGNORECASE,
)
_INLINE_EVENT_HANDLERS_PATTERN = re.compile(
    r"\bon\w+\s*=\s*(?:'[^']*'|\"[^\"]*\"|[^\s>]+)",
    re.IGNORECASE,
)
_JAVASCRIPT_URI_PATTERN = re.compile(
    r"(?:javascript|vbscript|data):[^\s\"']*",
    re.IGNORECASE,
)


def escape_html(text: str) -> str:
    """Standard HTML entity escape (&, <, >, \", ')"""
    if not isinstance(text, str):
        return text
    return html.escape(text, quote=True)


def sanitize_html(text: str, strip_tags: bool = True) -> str:
    """
    Sanitizes user input string by stripping or neutralizing executable script tags,
    inline event handlers (e.g. onerror, onload), and javascript: pseudo-protocols.
    If strip_tags is True, also escapes any remaining HTML tags to render them inert.
    """
    if not isinstance(text, str):
        return text

    # Remove script/iframe blocks
    cleaned = _DANGEROUS_TAGS_PATTERN.sub("", text)
    cleaned = _DANGEROUS_EMPTY_TAGS_PATTERN.sub("", cleaned)
    # Remove inline event handlers (e.g., onload=..., onerror=...)
    cleaned = _INLINE_EVENT_HANDLERS_PATTERN.sub("", cleaned)
    # Remove javascript: protocols
    cleaned = _JAVASCRIPT_URI_PATTERN.sub("", cleaned)

    if strip_tags:
        # Strip all raw HTML tags or escape them
        cleaned = escape_html(cleaned)

    return cleaned.strip()


def sanitize_payload(payload: Union[Dict[str, Any], List[Any], str, Any]) -> Any:
    """
    Recursively inspects and sanitizes nested dictionary or list payloads,
    neutralizing malicious script injections in string values.
    """
    if isinstance(payload, str):
        return sanitize_html(payload)
    elif isinstance(payload, dict):
        return {k: sanitize_payload(v) for k, v in payload.items()}
    elif isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    return payload
