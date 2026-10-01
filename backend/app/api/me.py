from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.api.schemas import UserOut

router = APIRouter(prefix="/me", tags=["me"])  # every route here requires login


@router.get("", response_model=UserOut)
def get_me(user: CurrentUser):
    return user
