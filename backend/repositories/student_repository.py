"""
NSBM EduSphere — Student Repository
Data access operations for Student entities and related records
"""
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.models import Student, User, Enrollment, Grade, Attendance, BorrowRecord
from backend.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    def __init__(self, db: AsyncSession):
        super().__init__(Student, db)

    async def get_by_user_id(self, user_id: int) -> Optional[Student]:
        result = await self.db.execute(
            select(Student).where(Student.user_id == user_id).options(selectinload(Student.user))
        )
        return result.scalar_one_or_none()

    async def get_by_student_id(self, student_id: str) -> Optional[Student]:
        result = await self.db.execute(
            select(Student).where(Student.student_id == student_id).options(selectinload(Student.user))
        )
        return result.scalar_one_or_none()

    async def count_active_enrollments(self, student_id: int) -> int:
        result = await self.db.execute(
            select(func.count(Enrollment.id)).where(
                and_(Enrollment.student_id == student_id, Enrollment.status == "active")
            )
        )
        return result.scalar() or 0

    async def get_student_grades(self, student_id: int, limit: int = 10) -> Sequence[Grade]:
        result = await self.db.execute(
            select(Grade).where(Grade.student_id == student_id)
            .options(selectinload(Grade.course))
            .limit(limit)
        )
        return result.scalars().all()
