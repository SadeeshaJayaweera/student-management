"""
NSBM EduSphere — Account Lifecycle Service
Manages account invitations, invitation acceptance, password resets,
account suspension, and reactivation workflows.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.models import (
    User,
    UserRole,
    UserSession,
    RefreshToken,
    UserInvitation,
    InvitationStatus,
    PasswordResetToken,
    UserAccountStatus,
)
from backend.repositories.user_repository import UserRepository
from backend.utils.security import (
    hash_password,
    hash_token,
    validate_password_strength,
)
from backend.core.exceptions import (
    ValidationException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)


class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def invite_user(
        self,
        email: str,
        role: str,
        institution_id: Optional[int],
        invited_by_id: int,
    ) -> Tuple[UserInvitation, str]:
        """
        Generates an institutional account invitation with a cryptographically secure token.
        """
        # Validate role
        try:
            user_role = UserRole(role.lower())
        except ValueError:
            raise ValidationException(f"Invalid user role: {role}")

        # Check if email is already registered
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictException(f"User with email '{email}' is already registered.")

        # Invalidate any previous pending invitations for this email
        await self.db.execute(
            update(UserInvitation)
            .where(
                UserInvitation.email == email,
                UserInvitation.status == InvitationStatus.PENDING,
            )
            .values(status=InvitationStatus.REVOKED)
        )

        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = now + timedelta(days=7)

        invitation = UserInvitation(
            email=email,
            role=user_role,
            institution_id=institution_id,
            token_hash=token_hash,
            invited_by_id=invited_by_id,
            status=InvitationStatus.PENDING,
            created_at=now,
            expires_at=expires_at,
        )
        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)
        return invitation, raw_token

    async def accept_invitation(
        self,
        token: str,
        username: str,
        password: str,
        full_name: str,
    ) -> User:
        """
        Accepts invitation token, verifies password complexity, and activates user account.
        """
        token_hash = hash_token(token)
        res = await self.db.execute(
            select(UserInvitation).where(UserInvitation.token_hash == token_hash)
        )
        invitation = res.scalar_one_or_none()
        if not invitation:
            raise ValidationException("Invalid or unrecognized invitation token.")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if invitation.status != InvitationStatus.PENDING or invitation.expires_at < now:
            if invitation.status == InvitationStatus.PENDING:
                invitation.status = InvitationStatus.EXPIRED
                await self.db.commit()
            raise ValidationException("Invitation token has expired or is no longer valid.")

        # Validate password
        try:
            validate_password_strength(password)
        except ValueError as err:
            raise ValidationException(str(err))

        # Check uniqueness of username
        existing_user = await self.user_repo.get_by_username(username)
        if existing_user:
            raise ConflictException(f"Username '{username}' is already taken.")

        # Create active user
        user = User(
            email=invitation.email,
            username=username,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=invitation.role,
            institution_id=invitation.institution_id,
            is_active=True,
            is_verified=True,
            account_status=UserAccountStatus.ACTIVE,
            failed_login_attempts=0,
            password_changed_at=now,
        )
        self.db.add(user)
        invitation.status = InvitationStatus.ACCEPTED
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def request_password_reset(self, email: str) -> Optional[str]:
        """
        Requests a password reset token.
        Always returns generic message to client to prevent user enumeration.
        """
        user = await self.user_repo.get_by_email(email)
        if not user or not user.is_active:
            return None

        # Invalidate existing unused reset tokens for this user
        await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user.id, PasswordResetToken.is_used == False)
            .values(is_used=True)
        )

        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = now + timedelta(hours=1)

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            is_used=False,
            created_at=now,
            expires_at=expires_at,
        )
        self.db.add(reset_record)
        await self.db.commit()
        return raw_token

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        """
        Confirms reset token, updates password, and revokes all existing sessions/tokens.
        """
        token_hash = hash_token(token)
        res = await self.db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        reset_token = res.scalar_one_or_none()
        if not reset_token or reset_token.is_used:
            raise ValidationException("Invalid or expired password reset token.")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if reset_token.expires_at < now:
            reset_token.is_used = True
            await self.db.commit()
            raise ValidationException("Password reset token has expired.")

        try:
            validate_password_strength(new_password)
        except ValueError as err:
            raise ValidationException(str(err))

        user = await self.user_repo.get_by_id(reset_token.user_id)
        if not user or not user.is_active:
            raise ValidationException("User account not found or disabled.")

        # Update password
        user.hashed_password = hash_password(new_password)
        user.password_changed_at = now
        user.failed_login_attempts = 0
        user.locked_until = None
        reset_token.is_used = True

        # Invalidate all active sessions and refresh tokens for security
        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id)
            .values(is_active=False)
        )
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id)
            .values(is_revoked=True)
        )
        await self.db.commit()

    async def suspend_account(self, user_id: int, reason: str, admin_user: User) -> User:
        """
        Suspends an account, instantly terminating all active sessions and refresh tokens.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)

        if user.id == admin_user.id:
            raise ValidationException("Administrators cannot suspend their own account.")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        user.account_status = UserAccountStatus.SUSPENDED
        user.is_active = False
        user.suspended_at = now
        user.suspended_reason = reason
        user.suspended_by_id = admin_user.id

        # Invalidate all active sessions and refresh tokens
        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id)
            .values(is_active=False)
        )
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id)
            .values(is_revoked=True)
        )
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def reactivate_account(self, user_id: int, admin_user: User) -> User:
        """Reactivates a previously suspended or deactivated account"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)

        user.account_status = UserAccountStatus.ACTIVE
        user.is_active = True
        user.suspended_at = None
        user.suspended_reason = None
        user.suspended_by_id = None
        user.failed_login_attempts = 0
        user.locked_until = None

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def list_invitations(self, institution_id: Optional[int] = None) -> List[UserInvitation]:
        """Lists pending and historical invitations"""
        query = select(UserInvitation).order_by(UserInvitation.created_at.desc())
        if institution_id:
            query = query.where(UserInvitation.institution_id == institution_id)
        res = await self.db.execute(query)
        return list(res.scalars().all())
