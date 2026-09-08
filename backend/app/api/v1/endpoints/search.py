from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.schemas.retrieval import SearchResponse
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import (
    LexicalRetrievalService,
    RetrievalMethod,
    RetrievalService,
    VectorRetrievalService,
)

router = APIRouter(prefix="/search", tags=["search"])


def get_retrieval_service(db: Session = Depends(get_db)) -> RetrievalService:
    chunk_repository = DocumentChunkRepository(db)
    return RetrievalService(
        vector_retrieval_service=VectorRetrievalService(
            embedding_service=EmbeddingService(),
            chunk_repository=chunk_repository,
        ),
        lexical_retrieval_service=LexicalRetrievalService(
            chunk_repository=chunk_repository,
            language=settings.fulltext_search_language,
        ),
    )


@router.get(
    "",
    response_model=SearchResponse,
    summary="Retrieve chunks from the authenticated user's documents",
)
def search(
    query: str = Query(..., min_length=1, max_length=500),
    method: RetrievalMethod = Query(
        default=RetrievalMethod.VECTOR,
        description="Retrieval strategy: vector (semantic) or lexical (full-text)",
    ),
    top_k: int | None = Query(
        default=None,
        ge=1,
        le=settings.retrieval_max_top_k,
        description="Number of results to return (defaults to server config)",
    ),
    current_user: User = Depends(get_current_user),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    return retrieval_service.search(
        user_id=current_user.id,
        query=query,
        method=method,
        top_k=top_k,
    )
