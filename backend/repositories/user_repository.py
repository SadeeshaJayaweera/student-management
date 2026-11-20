"""
NSBM EduSphere — User Repository
Data access operations for the User entity
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime
from backend.models import User
from backend.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_email_or_username(self, identifier: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(or_(User.email == identifier, User.username == identifier))
        )
        return result.scalar_one_or_none()

    async def update_last_login(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            await self.db.flush()
