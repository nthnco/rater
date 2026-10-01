from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.api.schemas import ServiceOut, UpdateServicesRequest, UserOut
from app.db import get_db
from app.models import StreamingService, UserService
from app.services.streaming import SUPPORTED_SERVICE_IDS

router = APIRouter(prefix="/me", tags=["me"])  # every route here requires login


@router.get("", response_model=UserOut)
def get_me(user: CurrentUser):
    return user


@router.get("/services", response_model=list[ServiceOut])
def get_my_services(user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    return _services_of(db, user.id)


@router.put("/services", response_model=list[ServiceOut])
def set_my_services(
    body: UpdateServicesRequest, user: CurrentUser, db: Annotated[Session, Depends(get_db)]
):
    """Replace the user's services with exactly this set (used only to filter recs, §2)."""
    ids = set(body.service_ids)  # duplicates collapse
    unsupported = ids - SUPPORTED_SERVICE_IDS
    if unsupported:
        # Reject before touching anything, so a bad request can't half-apply.
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Unsupported service ids: {sorted(unsupported)}",
        )

    db.execute(delete(UserService).where(UserService.user_id == user.id))
    if ids:
        db.execute(
            insert(UserService).values([{"user_id": user.id, "service_id": i} for i in ids])
        )
    db.commit()
    return _services_of(db, user.id)


def _services_of(db: Session, user_id: int) -> Sequence[StreamingService]:
    return db.scalars(
        select(StreamingService)
        .join(UserService, UserService.service_id == StreamingService.id)
        .where(UserService.user_id == user_id)
        .order_by(StreamingService.name)
    ).all()
