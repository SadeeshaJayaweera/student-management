"""
NSBM EduSphere — Sliding-Window Rate Limiting Engine
Defends endpoints against brute-force, DDoS, and credential-stuffing attacks.
"""
import time
from collections import defaultdict
from typing import Dict, List, Tuple, Callable
from fastapi import Request, HTTPException, status
from backend.config import settings


class InMemoryRateLimiter:
    """Thread-safe sliding-window request tracker"""
    def __init__(self):
        # Maps (key, action) -> list of timestamp floats
        self._history: Dict[Tuple[str, str], List[float]] = defaultdict(list)

    def is_allowed(
        self,
        key: str,
        action: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Evaluates whether a request is within allowable limits.
        Returns: (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        cutoff = now - window_seconds
        bucket = self._history[(key, action)]

        # Evict timestamps older than the active sliding window
        valid_timestamps = [ts for ts in bucket if ts > cutoff]
        self._history[(key, action)] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            earliest = valid_timestamps[0]
            retry_after = max(1, int(earliest + window_seconds - now))
            return False, 0, retry_after

        # Record this request
        valid_timestamps.append(now)
        remaining = max_requests - len(valid_timestamps)
        return True, remaining, 0

    def reset(self):
        """Clears all rate limit history"""
        self._history.clear()


# Global in-memory rate limiter instance
rate_limiter = InMemoryRateLimiter()


def rate_limit(
    max_requests: int = 60,
    window_seconds: int = 60,
    action: str = "default",
) -> Callable:
    """
    FastAPI dependency factory enforcing rate limits on endpoints.
    Identifies clients by authenticated user ID or remote client IP address.
    """
    async def dependency(request: Request):
        # In non-production environments, only enforce rate limiting when explicitly enabled for testing
        if not settings.is_production and request.headers.get("x-enable-rate-limit") != "true":
            return

        # Extract client key: check state.user or client host
        client_key = request.client.host if request.client else "unknown"
        if hasattr(request.state, "user") and request.state.user:
            client_key = f"user_{request.state.user.id}"

        endpoint_action = action if action != "default" else request.url.path

        allowed, remaining, retry_after = rate_limiter.is_allowed(
            key=client_key,
            action=endpoint_action,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} second(s).",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency

