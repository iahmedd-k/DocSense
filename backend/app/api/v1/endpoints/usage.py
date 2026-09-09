from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.usage import UsageResponse
from app.services.usage_service import UsageService

router = APIRouter(prefix="/usage", tags=["usage"])


def get_usage_service(db: Session = Depends(get_db)) -> UsageService:
    return UsageService(db)


@router.get(
    "",
    response_model=UsageResponse,
    summary="Return the authenticated user's usage and quota information (FR-022)",
)
def get_usage(
    current_user: User = Depends(get_current_user),
    usage_service: UsageService = Depends(get_usage_service),
):
    return usage_service.get_usage(current_user.id)
