"""Password hashing (Argon2id) and login tokens (JWT in an httpOnly cookie, DESIGN.md §3)."""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import settings

JWT_ALGORITHM = "HS256"

# argon2-cffi's defaults follow RFC 9106's recommended profile: Argon2id, 64 MiB memory,
# 3 passes, random 16-byte salt per hash. The output string embeds all of these.
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):  # wrong password, or a corrupt stored hash
        return False


def create_access_token(
    user_id: int, now: datetime | None = None, secret: str | None = None
) -> str:
    """A signed (not encrypted) token: anyone can read the payload, so it holds only the id."""
    now = now or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_ttl_days),
    }
    return jwt.encode(payload, secret or settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, secret: str | None = None) -> int | None:
    """The user id if the token is genuine and unexpired, else None."""
    try:
        payload = jwt.decode(
            token,
            secret or settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],  # pinned: never let the token choose its own algorithm
            options={"require": ["sub", "exp"]},
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        return None
