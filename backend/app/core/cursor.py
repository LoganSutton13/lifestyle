"""Simple opaque cursor encoding for keyset pagination.

Cursors are base64-encoded JSON objects. They are not signed; they only need
to be opaque and round-trippable, since the values they carry (timestamps,
names, ids) are not secret and are re-validated against the database on
every request.
"""

import base64
import json
from typing import Any

from app.api.error_handlers import ValidationError


def encode_cursor(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), default=str)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: str) -> dict[str, Any]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        data = json.loads(raw)
    except Exception as exc:
        raise ValidationError("Invalid pagination cursor") from exc
    if not isinstance(data, dict):
        raise ValidationError("Invalid pagination cursor")
    return data
