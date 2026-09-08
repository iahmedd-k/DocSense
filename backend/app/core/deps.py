from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db import get_db
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    user = UserRepository(db).get_by_id(int(user_id))

    if user is None:
        raise UnauthorizedError("User no longer exists")

    if not user.is_active:
        raise UnauthorizedError("Inactive user")

    return user


def require_role(*roles: UserRole) -> Callable:
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError("Insufficient permissions")

        return current_user

    return role_checker