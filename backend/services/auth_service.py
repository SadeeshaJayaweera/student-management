"""
NSBM EduSphere — Secure Authentication Service
Enterprise authentication service with brute-force defense, lockout management,
password complexity enforcement, session tracking, and cryptographic token lifecycle management
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.config import settings
from backend.models import User, UserRole, UserSession, RefreshToken
from backend.repositories.user_repository import UserRepository
from backend.schemas import UserCreate, Token, TokenPair, UserSessionOut
from backend.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_token,
    validate_password_strength,
)
from backend.core.exceptions import (
    UnauthorizedException,
    ConflictException,
    ValidationException,
    NotFoundException,
)


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
    ) -> Tuple[User, UserSession]:
        """
        Authenticate user credentials with brute-force protection and lockout enforcement.
        Creates an active UserSession upon success.
        Returns: (user, session)
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
        await self.db.refresh(session)
        return user, session

    async def issue_token_pair(
        self,
        user: User,
        session: Optional[UserSession] = None,
        family_id: Optional[str] = None,
    ) -> TokenPair:
        """
        Generates access token and refresh token, persisting the hashed refresh token.
        """
        raw_refresh, jti, family, expires_at = create_refresh_token(
            user_id=user.id, family_id=family_id
        )
        refresh_record = RefreshToken(
            user_id=user.id,
            session_id=session.id if session else None,
            jti=jti,
            token_hash=hash_token(raw_refresh),
            family_id=family,
            is_revoked=False,
            expires_at=expires_at,
        )
        self.db.add(refresh_record)
        await self.db.commit()

        access_token = create_access_token({"sub": str(user.id), "role": user.role})
        return TokenPair(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            role=user.role,
            user_id=user.id,
            full_name=user.full_name,
        )

    async def rotate_refresh_token(
        self,
        refresh_token_str: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenPair:
        """
        Rotates refresh token using cryptographic family tracking and replay attack detection.
        """
        payload = decode_refresh_token(refresh_token_str)
        token_hash = hash_token(refresh_token_str)
        user_id = int(payload.get("sub"))
        family_id = payload.get("family")

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            raise UnauthorizedException("Invalid refresh token.")

        # Replay Attack Detection:
        # If an already revoked token is submitted, the token family has been compromised!
        if token_record.is_revoked:
            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == family_id)
                .values(is_revoked=True)
            )
            if token_record.session_id:
                await self.db.execute(
                    update(UserSession)
                    .where(UserSession.id == token_record.session_id)
                    .values(is_active=False)
                )
            await self.db.commit()
            raise UnauthorizedException(
                "Refresh token reuse detected. Token family invalidated for security."
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if token_record.expires_at < now:
            token_record.is_revoked = True
            await self.db.commit()
            raise UnauthorizedException("Refresh token has expired.")

        # Invalidate current token
        token_record.is_revoked = True

        # Generate new token in the same family
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User account not found or disabled.")

        new_raw_refresh, new_jti, family, expires_at = create_refresh_token(
            user_id=user.id, family_id=family_id
        )
        token_record.replaced_by = new_jti

        new_refresh_record = RefreshToken(
            user_id=user.id,
            session_id=token_record.session_id,
            jti=new_jti,
            token_hash=hash_token(new_raw_refresh),
            family_id=family,
            is_revoked=False,
            expires_at=expires_at,
        )
        self.db.add(new_refresh_record)

        # Update session activity
        if token_record.session_id:
            sess_result = await self.db.execute(
                select(UserSession).where(UserSession.id == token_record.session_id)
            )
            session = sess_result.scalar_one_or_none()
            if session:
                session.last_activity_at = now
                if ip_address:
                    session.ip_address = ip_address
                if user_agent:
                    session.user_agent = user_agent

        await self.db.commit()

        access_token = create_access_token({"sub": str(user.id), "role": user.role})
        return TokenPair(
            access_token=access_token,
            refresh_token=new_raw_refresh,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            role=user.role,
            user_id=user.id,
            full_name=user.full_name,
        )

    async def logout(self, user_id: int, refresh_token_str: Optional[str] = None) -> None:
        """Revokes the given refresh token and deactivates its session"""
        if refresh_token_str:
            token_hash = hash_token(refresh_token_str)
            result = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.user_id == user_id,
                )
            )
            token_record = result.scalar_one_or_none()
            if token_record:
                token_record.is_revoked = True
                if token_record.session_id:
                    sess_res = await self.db.execute(
                        select(UserSession).where(UserSession.id == token_record.session_id)
                    )
                    sess = sess_res.scalar_one_or_none()
                    if sess:
                        sess.is_active = False
                await self.db.commit()

    async def revoke_session(self, user_id: int, session_id: int) -> bool:
        """Revokes a specific session and its associated refresh tokens"""
        sess_res = await self.db.execute(
            select(UserSession).where(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
            )
        )
        session = sess_res.scalar_one_or_none()
        if not session:
            return False

        session.is_active = False
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.session_id == session_id)
            .values(is_revoked=True)
        )
        await self.db.commit()
        return True

    async def revoke_all_sessions(self, user_id: int) -> int:
        """Revokes all sessions and refresh tokens for user"""
        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .values(is_active=False)
        )
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.commit()
        return True

    async def list_user_sessions(self, user_id: int) -> List[UserSession]:
        """Lists active user sessions"""
        res = await self.db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_active == True)
            .order_by(UserSession.last_activity_at.desc())
        )
        return list(res.scalars().all())

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
