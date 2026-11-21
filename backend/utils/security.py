"""
NSBM EduSphere — Security Utilities
JWT token creation, verification, and password hashing
"""
import hashlib
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List
import bcrypt
import pyotp
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.database import get_db
from backend.models import User

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def validate_password_strength(password: str) -> None:
    """
    Validates enterprise password complexity:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special symbol
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=]", password):
        raise ValueError("Password must contain at least one special character.")


def hash_password(password: str) -> str:
    """Hash password using bcrypt with work factor 12"""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        plain_bytes = plain.encode('utf-8')[:72]
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


def hash_token(token: str) -> str:
    """Computes a SHA-256 cryptographic digest of a token string"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(
    user_id: int,
    family_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, str, str, datetime]:
    """
    Creates a cryptographically unique refresh token and associated family identifier.
    Returns: (raw_token_str, jti, family_id, expires_at)
    """
    jti = uuid.uuid4().hex
    family = family_id or uuid.uuid4().hex
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + (
        expires_delta or timedelta(days=7)
    )
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "family": family,
        "type": "refresh",
        "exp": expire,
    }
    raw_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return raw_token, jti, family, expire


def decode_refresh_token(token: str) -> dict:
    """Decodes and validates a refresh token payload"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── Multi-Factor Authentication (MFA) Helpers ───────────────────────────────

def generate_mfa_secret() -> str:
    """Generates an RFC 6238 base32 TOTP secret"""
    return pyotp.random_base32()


def get_mfa_uri(secret: str, username: str, issuer: str = "NSBM EduSphere") -> str:
    """Generates a standard otpauth:// URI for authenticator apps"""
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    """Verifies a 6-digit TOTP code against the secret with a 1-step clock skew window"""
    if not secret or not code:
        return False
    totp = pyotp.totp.TOTP(secret)
    return bool(totp.verify(code.strip(), valid_window=1))


def generate_backup_codes(count: int = 10) -> Tuple[List[str], List[str]]:
    """
    Generates single-use emergency backup recovery codes.
    Returns: (plain_codes, hashed_codes)
    """
    plain_codes = []
    hashed_codes = []
    for _ in range(count):
        code = secrets.token_hex(4).upper()  # 8-character hex code e.g. 'A1B2C3D4'
        plain_codes.append(code)
        hashed_codes.append(hash_token(code))
    return plain_codes, hashed_codes


def create_mfa_token(user_id: int) -> str:
    """Creates a temporary short-lived JWT token valid for 5 minutes during 2FA step-up"""
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=5)
    payload = {
        "sub": str(user_id),
        "type": "mfa_pending",
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_mfa_token(token: str) -> int:
    """Decodes a temporary MFA login token and returns the user id"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "mfa_pending":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected MFA pending token",
            )
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA session expired or invalid. Please log in again.",
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(
        select(User)
        .where(User.id == int(user_id))
        .options(selectinload(User.lecturer), selectinload(User.student))
    )
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


async def get_current_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("student", "admin"):
        raise HTTPException(status_code=403, detail="Student access required")
    return current_user


async def get_current_lecturer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("lecturer", "admin"):
        raise HTTPException(status_code=403, detail="Lecturer access required")
    return current_user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_roles(*roles: str):
    """Dependency factory for role-based access"""
    # Normalize if passed as a single list or tuple
    if len(roles) == 1 and isinstance(roles[0], (list, tuple, set)):
        allowed_roles = tuple(str(r) for r in roles[0])
    else:
        allowed_roles = tuple(str(r) for r in roles)

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if current_user.role not in allowed_roles and user_role_str not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker
