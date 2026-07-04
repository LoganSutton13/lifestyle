from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_hash_value: str) -> bool:
    return password_hash.verify(password, password_hash_value)


def create_access_token(user_id: UUID, role: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, get_settings().JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, str]:
    payload = jwt.decode(token, get_settings().JWT_SECRET, algorithms=["HS256"])
    if payload.get("type") != "access":
        msg = "Invalid token type"
        raise jwt.InvalidTokenError(msg)
    return payload
