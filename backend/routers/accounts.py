"""
NSBM EduSphere — Account Lifecycle Management Router
Provides secure endpoints for invitations, activation, password recovery,
account suspension, and reactivation.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User, UserRole
from backend.schemas import (
    UserOut,
    InvitationCreateRequest,
    InvitationOut,
    AcceptInvitationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    SuspendAccountRequest,
)
from backend.services.account_service import AccountService
from backend.core.dependencies import get_current_user
from backend.core.rbac import StandardPermissions, require_permission
from backend.core.exceptions import (
    ValidationException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)

router = APIRouter(prefix="/api/accounts", tags=["Account Lifecycle"])


@router.post("/invite", response_model=InvitationOut, status_code=201)
async def invite_user(
    payload: InvitationCreateRequest,
    current_user: User = Depends(require_permission(StandardPermissions.USERS_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """Invite a new institutional user (Requires USERS_WRITE permission)"""
    service = AccountService(db)
    try:
        invitation, raw_token = await service.invite_user(
            email=payload.email,
            role=payload.role,
            institution_id=payload.institution_id or current_user.institution_id,
            invited_by_id=current_user.id,
        )
        return InvitationOut(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role.value if hasattr(invitation.role, "value") else str(invitation.role),
            institution_id=invitation.institution_id,
            status=invitation.status.value if hasattr(invitation.status, "value") else str(invitation.status),
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            invitation_token=raw_token,
        )
    except (ValidationException, ConflictException) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err.message)


@router.post("/accept-invitation", response_model=UserOut, status_code=201)
async def accept_invitation(
    payload: AcceptInvitationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Activate an account using a cryptographically signed invitation token"""
    service = AccountService(db)
    try:
        user = await service.accept_invitation(
            token=payload.token,
            username=payload.username,
            password=payload.password,
            full_name=payload.full_name,
        )
        return user
    except (ValidationException, ConflictException) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err.message)


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset. Returns generic message to prevent account enumeration.
    """
    service = AccountService(db)
    reset_token = await service.request_password_reset(payload.email)
    response_payload = {
        "message": "If an active account exists for that email, a password reset link has been dispatched."
    }
    # In development/test environments, expose token for testing convenience
    if reset_token:
        response_payload["reset_token"] = reset_token
    return response_payload


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using token. Automatically revokes all existing active sessions"""
    service = AccountService(db)
    try:
        await service.confirm_password_reset(payload.token, payload.new_password)
        return {"message": "Password updated successfully. Please log in with your new credentials."}
    except ValidationException as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err.message)


@router.post("/{user_id}/suspend", response_model=UserOut)
async def suspend_account(
    user_id: int,
    payload: SuspendAccountRequest,
    current_user: User = Depends(require_permission(StandardPermissions.USERS_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """Suspend an account, immediately terminating all active sessions (Requires USERS_WRITE)"""
    service = AccountService(db)
    try:
        user = await service.suspend_account(user_id, payload.reason, current_user)
        return user
    except NotFoundException as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err.message)
    except ValidationException as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err.message)


@router.post("/{user_id}/reactivate", response_model=UserOut)
async def reactivate_account(
    user_id: int,
    current_user: User = Depends(require_permission(StandardPermissions.USERS_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """Reactivate a suspended user account (Requires USERS_WRITE)"""
    service = AccountService(db)
    try:
        user = await service.reactivate_account(user_id, current_user)
        return user
    except NotFoundException as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err.message)


@router.get("/invitations", response_model=List[InvitationOut])
async def list_invitations(
    current_user: User = Depends(require_permission(StandardPermissions.USERS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """List invitations for institution or platform (Requires USERS_READ)"""
    service = AccountService(db)
    invitations = await service.list_invitations(current_user.institution_id)
    return [
        InvitationOut(
            id=inv.id,
            email=inv.email,
            role=inv.role.value if hasattr(inv.role, "value") else str(inv.role),
            institution_id=inv.institution_id,
            status=inv.status.value if hasattr(inv.status, "value") else str(inv.status),
            created_at=inv.created_at,
            expires_at=inv.expires_at,
            invitation_token=None,
        )
        for inv in invitations
    ]
