from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-jwt-secret")
ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", JWT_SECRET)
CLIENT_JWT_SECRET = os.getenv("CLIENT_JWT_SECRET", JWT_SECRET)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def _get_secret_for_role(role: str) -> str:
    if role == "admin":
        return ADMIN_JWT_SECRET
    if role == "client":
        return CLIENT_JWT_SECRET
    return JWT_SECRET


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, subject: str, role: str, expires_minutes: int | None = None) -> str:
    expire_delta = timedelta(
        minutes=expires_minutes if expires_minutes is not None else ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire_at = datetime.now(timezone.utc) + expire_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire_at,
    }
    return jwt.encode(payload, _get_secret_for_role(role), algorithm=JWT_ALGORITHM)


def decode_token(token: str, expected_role: str | None = None) -> dict[str, Any]:
    secret = _get_secret_for_role(expected_role) if expected_role else JWT_SECRET
    try:
        return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
