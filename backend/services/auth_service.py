"""
NSBM EduSphere — Secure Authentication Service
Enterprise authentication service with brute-force defense, lockout management,
password complexity enforcement, and session tracking
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, UserSession
from backend.repositories.user_repository import UserRepository
from backend.schemas import UserCreate, Token
from backend.utils.security import (
    hash_password, verify_password, create_access_token, validate_password_strength
)
from backend.core.exceptions import UnauthorizedException, ConflictException, ValidationException


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """
        Authenticate user credentials with brute-force protection and lockout enforcement.
        Creates an active UserSession upon success.
        """
        user = await self.user_repo.get_by_username(username)
        if not user:
            raise UnauthorizedException("Invalid username or password.")

        # Check account lockout status
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if user.locked_until and user.locked_until > now:
            remaining_mins = max(1, int((user.locked_until - now).total_seconds() // 60))
            raise UnauthorizedException(
                f"Account is temporarily locked due to excessive failed attempts. Try again in {remaining_mins} minute(s)."
            )

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=15)
            await self.db.commit()
            raise UnauthorizedException("Invalid username or password.")

        if not user.is_active:
            raise UnauthorizedException("Account is disabled. Please contact your institutional administrator.")

        # Reset failed attempts and clear lockout on successful authentication
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = now

        # Create active session record
        session = UserSession(
            user_id=user.id,
            session_token=secrets.token_urlsafe(32),
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            expires_at=now + timedelta(days=7),
            last_activity_at=now,
        )
        self.db.add(session)
        await self.db.commit()
        return user

    async def register(self, payload: UserCreate) -> User:
        """
        Register a new user with password complexity checks and privilege escalation defense.
        Self-registration of administrative or faculty roles is strictly prohibited.
        """
        # Enforce password strength
        try:
            validate_password_strength(payload.password)
        except ValueError as err:
            raise ValidationException(str(err))

        # Check for privilege escalation
        elevated_roles = {UserRole.ADMIN.value, UserRole.LECTURER.value, UserRole.LIBRARIAN.value}
        if payload.role and payload.role.lower() in elevated_roles:
            raise ValidationException("Elevated roles (admin, lecturer, librarian) cannot be self-assigned.")

        existing = await self.user_repo.get_by_email_or_username(payload.username)
        if not existing and payload.email:
            existing = await self.user_repo.get_by_email(payload.email)
        if existing:
            raise ConflictException("Email or username is already registered.")

        role = UserRole.STUDENT
        if payload.role and payload.role.lower() == UserRole.ALUMNI.value:
            role = UserRole.ALUMNI

        user = User(
            email=payload.email,
            username=payload.username,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            phone=payload.phone,
            role=role,
            is_active=True,
            is_verified=False,
            failed_login_attempts=0,
            password_changed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user: User, old_password: str, new_password: str) -> None:
        """Validate current credentials and apply password policy to new password"""
        if not verify_password(old_password, user.hashed_password):
            raise ValidationException("Incorrect current password.")

        try:
            validate_password_strength(new_password)
        except ValueError as err:
            raise ValidationException(str(err))

        user.hashed_password = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc).replace(tzinfo=None)
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
