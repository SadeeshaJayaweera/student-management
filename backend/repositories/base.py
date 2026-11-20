"""
NSBM EduSphere — Base Repository Pattern
Provides generic async CRUD data access operations for SQLAlchemy models
"""
from typing import Generic, TypeVar, Type, Optional, Sequence, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, update
from backend.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository providing standard data access methods"""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def list_all(self, offset: int = 0, limit: int = 50) -> Sequence[ModelType]:
        result = await self.db.execute(select(self.model).offset(offset).limit(limit))
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(self.model.id)))
        return result.scalar() or 0

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete_by_id(self, id: Any) -> bool:
        result = await self.db.execute(delete(self.model).where(self.model.id == id))
        return result.rowcount > 0
