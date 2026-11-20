"""NSBM EduSphere — Authentication Router"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User
from backend.schemas import (
    Token,
    TokenPair,
    LoginResponse,
    RefreshTokenRequest,
    MFASetupResponse,
    MFAEnableRequest,
    MFAEnableResponse,
    MFAVerifyRequest,
    MFADisableRequest,
    UserCreate,
    UserOut,
    UserSessionOut,
)
from backend.services.auth_service import AuthService
from backend.core.exceptions import (
    UnauthorizedException,
    ConflictException,
    ValidationException,
    NotFoundException,
)
from backend.core.dependencies import get_current_user
from backend.utils.security import create_mfa_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    try:
        user, session, mfa_required = await service.authenticate(
            form_data.username, form_data.password, ip_address=client_ip, user_agent=user_agent
        )
        if mfa_required:
            mfa_token = create_mfa_token(user.id)
            return LoginResponse(
                mfa_required=True,
                mfa_token=mfa_token,
            )
        token_pair = await service.issue_token_pair(user, session)
        return LoginResponse(
            mfa_required=False,
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
            role=token_pair.role,
            user_id=token_pair.user_id,
            full_name=token_pair.full_name,
        )
    except UnauthorizedException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    return await service.setup_mfa(current_user)


@router.post("/mfa/enable", response_model=MFAEnableResponse)
async def enable_mfa(
    payload: MFAEnableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    try:
        return await service.enable_mfa(current_user, payload.code)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/mfa/verify", response_model=TokenPair)
async def verify_mfa_login(
    request: Request,
    payload: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    try:
        return await service.verify_mfa_login(
            payload.mfa_token, payload.code, ip_address=client_ip, user_agent=user_agent
        )
    except (UnauthorizedException, HTTPException) as e:
        detail = e.detail if isinstance(e, HTTPException) else e.message
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


@router.post("/mfa/disable")
async def disable_mfa(
    payload: MFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    try:
        await service.disable_mfa(current_user, payload.password, payload.code)
        return {"message": "Multi-Factor Authentication disabled successfully."}
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    try:
        return await service.rotate_refresh_token(
            payload.refresh_token, ip_address=client_ip, user_agent=user_agent
        )
    except UnauthorizedException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)


@router.post("/logout")
async def logout(
    request: Request,
    payload: Optional[RefreshTokenRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    token_str = payload.refresh_token if payload else None
    await service.logout(current_user.id, token_str)
    return {"message": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    await service.revoke_all_sessions(current_user.id)
    return {"message": "All sessions terminated successfully"}


@router.get("/sessions", response_model=List[UserSessionOut])
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    sessions = await service.list_user_sessions(current_user.id)
    return sessions


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    success = await service.revoke_session(current_user.id, session_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"message": "Session terminated successfully"}


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    try:
        user = await service.register(payload)
        return user
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    try:
        await service.change_password(current_user, old_password, new_password)
        return {"message": "Password updated successfully"}
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
