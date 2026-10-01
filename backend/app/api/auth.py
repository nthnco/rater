from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import clear_login_cookie, set_login_cookie
from app.api.schemas import LoginRequest, SignupRequest, UserOut
from app.db import get_db
from app.models import User
from app.services.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

INVALID_LOGIN = "Invalid email or password"

# Verified against when the email doesn't exist, so a login attempt takes the same time
# whether or not the account exists (otherwise response timing reveals who has an account).
_DUMMY_HASH = hash_password("not-a-real-password-just-for-timing")


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, response: Response, db: Annotated[Session, Depends(get_db)]):
    email = body.email.lower()
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two signups for the same email raced past the check above; the UNIQUE constraint
        # caught the second one.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from None
    db.refresh(user)  # load DB defaults (region, created_at)

    set_login_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None:
        verify_password(_DUMMY_HASH, body.password)  # equalize timing; result ignored
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID_LOGIN)
    if not verify_password(user.password_hash, body.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID_LOGIN)

    set_login_cookie(response, user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    # The JWT itself stays valid until it expires (stateless); we just drop the cookie.
    clear_login_cookie(response)
