from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings


def hash_password(password: str, salt: str | None = None) -> str:
    raw_salt = salt or base64.urlsafe_b64encode(os.urandom(16)).decode("ascii")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), raw_salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${raw_salt}${base64.urlsafe_b64encode(digest).decode('ascii')}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        _scheme, salt, expected = password_hash.split("$", 2)
    except ValueError:
        return False
    candidate = hash_password(password, salt).split("$", 2)[2]
    return hmac.compare_digest(candidate, expected)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
        **(extra or {}),
    }
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    signing_input = f"{_b64(json.dumps(header, separators=(',', ':')).encode())}.{_b64(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.jwt_secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64(signature)}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".", 2)
        signing_input = f"{header_b64}.{payload_b64}"
        expected = _b64(hmac.new(settings.jwt_secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(expected, signature_b64):
            return None
        payload = json.loads(_unb64(payload_b64))
        if int(payload.get("exp", 0)) < int(datetime.utcnow().timestamp()):
            return None
        return payload
    except Exception:
        return None
