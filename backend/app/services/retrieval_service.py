from __future__ import annotations

import enum
import logging

from app.core.config import settings
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
    RetrievedChunk,
)
from app.schemas.retrieval import ChunkResult, SearchResponse
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorRetrievalService:
    """Semantic retrieval over DocumentChunk embeddings using pgvector.

    The user query is embedded with the same provider/model used during
    ingestion (FR-009) and then matched against stored chunk embeddings using
    cosine similarity. Ownership filtering (``user_id``) is enforced inside the
    repository query.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        chunk_repository: DocumentChunkRepository,
    ):
        self.embedding_service = embedding_service
        self.chunk_repository = chunk_repository

    def retrieve(
        self,
        user_id: int,
        query: str,
        top_k: int,
    ) -> list[ChunkResult]:
        query_vector = self.embedding_service.generate_embedding(query)

        results = self.chunk_repository.search_by_embedding(
            user_id=user_id,
            query_vector=query_vector,
            top_k=top_k,
        )

        return [
            self._to_result(chunk) for chunk in results
        ]

    @staticmethod
    def _to_result(chunk: RetrievedChunk) -> ChunkResult:
        return ChunkResult(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            content=chunk.content,
            page_number=chunk.page_number,
            page_numbers=chunk.page_numbers,
            content_type=chunk.content_type,
            metadata=chunk.metadata,
            score=chunk.score,
        )


class LexicalRetrievalService:
    """Full-text retrieval over DocumentChunk.content using PostgreSQL FTS.

    Uses a ``websearch_to_tsquery`` query and ``ts_rank`` ranking against the
    precomputed ``search_vector`` (see migration 0006). Ownership filtering
    (``user_id``) is enforced inside the repository query.
    """

    def __init__(
        self,
        chunk_repository: DocumentChunkRepository,
        language: str = "english",
    ):
        self.chunk_repository = chunk_repository
        self.language = language

    def retrieve(
        self,
        user_id: int,
        query: str,
        top_k: int,
    ) -> list[ChunkResult]:
        results = self.chunk_repository.search_by_text(
            user_id=user_id,
            query=query,
            top_k=top_k,
            language=self.language,
        )

        return [
            self._to_result(chunk) for chunk in results
        ]

    @staticmethod
    def _to_result(chunk: RetrievedChunk) -> ChunkResult:
        return ChunkResult(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            content=chunk.content,
            page_number=chunk.page_number,
            page_numbers=chunk.page_numbers,
            content_type=chunk.content_type,
            metadata=chunk.metadata,
            score=chunk.score,
        )


class RetrievalMethod(str, enum.Enum):
    """Supported retrieval strategies exposed by the retrieval service."""

    VECTOR = "vector"
    LEXICAL = "lexical"


class RetrievalService:
    """Orchestrates document retrieval for an authenticated user.

    Dispatches to the concrete vector (semantic) or lexical (full-text)
    retrieval service based on the requested ``method``. Hybrid fusion (RRF)
    and reranking are intentionally not part of this feature.
    """

    def __init__(
        self,
        vector_retrieval_service: VectorRetrievalService,
        lexical_retrieval_service: LexicalRetrievalService,
    ):
        self.vector_retrieval_service = vector_retrieval_service
        self.lexical_retrieval_service = lexical_retrieval_service

    @property
    def default_top_k(self) -> int:
        return settings.retrieval_default_top_k

    @property
    def max_top_k(self) -> int:
        return settings.retrieval_max_top_k

    def search(
        self,
        user_id: int,
        query: str,
        method: str,
        top_k: int | None = None,
    ) -> SearchResponse:
        """Run a single-method retrieval and shape the response."""
        top_k = self._resolve_top_k(top_k)

        if method == RetrievalMethod.LEXICAL:
            results = self.lexical_retrieval_service.retrieve(user_id, query, top_k)
        elif method == RetrievalMethod.VECTOR:
            results = self.vector_retrieval_service.retrieve(user_id, query, top_k)
        else:
            raise ValueError(f"Unsupported retrieval method: {method}")

        logger.info(
            "Retrieved %d results for user %s using method=%s",
            len(results),
            user_id,
            method,
        )
        return SearchResponse(query=query, results=results)

    def _resolve_top_k(self, top_k: int | None) -> int:
        if top_k is None:
            return self.default_top_k
        return max(1, min(top_k, self.max_top_k))
