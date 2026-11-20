"""
NSBM EduSphere — Authentication Service
Business logic layer for user registration, authentication, and credential management
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole
from backend.repositories.user_repository import UserRepository
from backend.schemas import UserCreate, Token
from backend.utils.security import hash_password, verify_password, create_access_token
from backend.core.exceptions import UnauthorizedException, ConflictException, ValidationException


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate(self, username: str, password: str) -> User:
        """Authenticate user credentials and return the active User entity"""
        user = await self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid username or password")
        if not user.is_active:
            raise UnauthorizedException("Account is disabled. Please contact administrator.")
        
        await self.user_repo.update_last_login(user.id)
        await self.db.commit()
        return user

    async def register(self, payload: UserCreate) -> User:
        """Register a new user with uniqueness checks"""
        existing = await self.user_repo.get_by_email_or_username(payload.username)
        if not existing and payload.email:
            existing = await self.user_repo.get_by_email(payload.email)
        if existing:
            raise ConflictException("Email or username is already registered")

        # Restrict self-registration to STUDENT or ALUMNI by default
        role = UserRole.STUDENT
        if payload.role in [UserRole.STUDENT.value, UserRole.ALUMNI.value]:
            role = UserRole(payload.role)

        user = User(
            email=payload.email,
            username=payload.username,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            phone=payload.phone,
            role=role,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user: User, old_password: str, new_password: str) -> None:
        """Validate current password and update to new password hash"""
        if not verify_password(old_password, user.hashed_password):
            raise ValidationException("Incorrect current password")
        if len(new_password) < 8:
            raise ValidationException("Password must be at least 8 characters long")
        user.hashed_password = hash_password(new_password)
        await self.db.commit()

    def generate_token(self, user: User) -> Token:
        """Generate JWT access token for user"""
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return Token(
            access_token=token,
            token_type="bearer",
            role=user.role,
            user_id=user.id,
            full_name=user.full_name,
        )
