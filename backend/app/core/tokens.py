import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_token_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=get_settings().REFRESH_TOKEN_DAYS)
