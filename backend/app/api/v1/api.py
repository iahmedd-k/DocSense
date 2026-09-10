from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    chat,
    documents,
    rag,
    search,
    usage,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(chat.router)
api_router.include_router(rag.router)
api_router.include_router(usage.router)

__all__ = ["api_router"]