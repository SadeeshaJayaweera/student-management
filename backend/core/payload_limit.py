"""
NSBM EduSphere — Request Payload Size Limiting Middleware
Guards against Denial of Service (DoS) and memory exhaustion from oversized request bodies.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int = 15 * 1024 * 1024):  # 15 MB default limit
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length_int = int(content_length)
                if length_int > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Request body size ({length_int} bytes) exceeds limit of {self.max_bytes} bytes.",
                            },
                            "detail": f"Request body exceeds {self.max_bytes // (1024 * 1024)}MB maximum limit.",
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)
