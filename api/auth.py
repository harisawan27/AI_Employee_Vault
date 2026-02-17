"""
WEBXES Tech — JWT Authentication for Dashboard API

Single-user auth: CEO logs in with API_PASSWORD, gets a JWT.
Rate-limited login (5 attempts/minute).
"""

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

JWT_SECRET = os.getenv("API_JWT_SECRET", "change-me-in-production-64-hex-chars")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
API_PASSWORD = os.getenv("API_PASSWORD", "webxes-ceo-2026")

# Rate limiting: track login attempts
_login_attempts: list[float] = []
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 5


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str


class UserInfo(BaseModel):
    user: str = "ceo"
    authenticated: bool = True


def _check_rate_limit():
    """Enforce 5 login attempts per minute."""
    now = time.time()
    # Prune old attempts
    _login_attempts[:] = [t for t in _login_attempts if now - t < RATE_LIMIT_WINDOW]
    if len(_login_attempts) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in 60 seconds.",
        )
    _login_attempts.append(now)


def create_token() -> tuple[str, datetime]:
    """Create a JWT token for the CEO user."""
    expires = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {
        "sub": "ceo",
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency: validate JWT and return username."""
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Authenticate with password and receive JWT."""
    _check_rate_limit()
    if req.password != API_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    token, expires = create_token()
    return TokenResponse(
        access_token=token,
        expires_at=expires.isoformat(),
    )


@router.get("/me", response_model=UserInfo)
def me(user: str = Depends(verify_token)):
    """Verify token validity."""
    return UserInfo(user=user)
