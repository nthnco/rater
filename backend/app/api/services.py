from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ServiceOut
from app.db import get_db
from app.models import StreamingService
from app.services.streaming import SUPPORTED_SERVICE_IDS

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceOut])
def list_services(db: Annotated[Session, Depends(get_db)]):
    """The services a user can pick. Public: it's the same list for everyone."""
    return db.scalars(
        select(StreamingService)
        .where(StreamingService.id.in_(SUPPORTED_SERVICE_IDS))
        .order_by(StreamingService.name)
    ).all()
