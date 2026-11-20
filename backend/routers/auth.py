"""NSBM EduSphere — Authentication Router"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User
from backend.schemas import Token, UserCreate, UserOut
from backend.services.auth_service import AuthService
from backend.core.exceptions import UnauthorizedException, ConflictException, ValidationException
from backend.core.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    try:
        user = await service.authenticate(form_data.username, form_data.password)
        return service.generate_token(user)
    except UnauthorizedException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)


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
