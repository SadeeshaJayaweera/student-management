"""
NSBM EduSphere — Pagination Standards
Standard reusable pagination parameters and response envelopes
"""
from typing import Generic, TypeVar, List, Sequence
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: Sequence[T], total: int, params: PaginationParams) -> "PaginatedResponse[T]":
        pages = (total + params.size - 1) // params.size if params.size > 0 else 1
        return cls(
            items=list(items),
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
