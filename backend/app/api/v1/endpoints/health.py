from fastapi import APIRouter, Response, status

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
def health_check():
    return {"status": "ok"}