"""
NSBM EduSphere — Standardized API Response Envelopes
RFC-inspired consistent success and error response schemas
"""
from datetime import datetime, timezone
from typing import Generic, TypeVar, Optional, Any, Dict, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized success response envelope for all API endpoints"""
    success: bool = Field(default=True, description="Indicates request success status")
    data: Optional[T] = Field(default=None, description="Response payload")
    message: Optional[str] = Field(default=None, description="Human-readable status or informational message")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of response generation",
    )
    correlation_id: Optional[str] = Field(default=None, description="Unique tracing request identifier")

    @classmethod
    def ok(cls, data: Optional[T] = None, message: Optional[str] = None, correlation_id: Optional[str] = None) -> "APIResponse[T]":
        return cls(
            success=True,
            data=data,
            message=message,
            correlation_id=correlation_id,
        )


class APIErrorDetails(BaseModel):
    code: str = Field(description="Machine-readable error classification code")
    message: str = Field(description="Clear human-readable error explanation")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional validation error details")


class APIErrorResponse(BaseModel):
    """Standardized error response envelope adhering to RFC 7807 principles with legacy detail support"""
    success: bool = Field(default=False, description="Always false for error envelopes")
    detail: str = Field(description="Human-readable error description for client toast notifications")
    error: APIErrorDetails = Field(description="Structured error details")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of error generation",
    )
    correlation_id: Optional[str] = Field(default=None, description="Unique tracing request identifier")

    @classmethod
    def build(cls, code: str, message: str, details: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> "APIErrorResponse":
        return cls(
            success=False,
            detail=message,
            error=APIErrorDetails(code=code, message=message, details=details),
            correlation_id=correlation_id,
        )
