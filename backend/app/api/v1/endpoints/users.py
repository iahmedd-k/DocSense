from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db import get_db
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.schemas.user import RoleUpdateRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Insufficient permissions")

    return current_user


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List all users (admin only)",
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    return db.scalars(select(User).order_by(User.id)).all()


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update a user's role (admin only)",
)
def update_role(
    user_id: int,
    data: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise NotFoundError("User not found")

    return UserRepository(db).set_role(user, data.role)