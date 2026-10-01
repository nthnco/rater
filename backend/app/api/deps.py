"""Shared request dependencies: the login cookie and the current user."""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User
from app.services.security import create_access_token, decode_access_token

ACCESS_COOKIE = "rater_session"


def set_login_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        create_access_token(user_id),
        max_age=settings.jwt_ttl_days * 24 * 60 * 60,
        httponly=True,  # JavaScript can't read it, so an XSS bug can't steal it
        samesite="lax",  # not sent on cross-site POST/PUT/DELETE, which blocks CSRF
        secure=settings.cookie_secure,  # HTTPS-only in production
        path="/",
    )


def clear_login_cookie(response: Response) -> None:
    response.delete_cookie(
        ACCESS_COOKIE,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Cookie(alias=ACCESS_COOKIE)] = None,
) -> User:
    """The logged-in user, or 401. Missing, invalid, expired, or orphaned tokens all fail."""
    user_id = decode_access_token(token) if token else None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
