from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.token import TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive an access token",
)
def login(
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.login(data)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated user's profile",
)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (stateless JWT, client discards the token)",
)
def logout(
    current_user: User = Depends(get_current_user),
):
    return Response(status_code=status.HTTP_204_NO_CONTENT)