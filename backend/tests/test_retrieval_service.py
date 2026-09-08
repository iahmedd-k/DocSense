import pytest

from app.core.config import settings
from app.repositories.document_chunk_repository import RetrievedChunk
from app.schemas.retrieval import ChunkResult
from app.services.retrieval_service import (
    LexicalRetrievalService,
    RetrievalMethod,
    RetrievalService,
    VectorRetrievalService,
)


class FakeEmbeddingService:
    def __init__(self):
        self.calls = []

    def generate_embedding(self, text):
        self.calls.append(text)
        return [0.5] * settings.embedding_dimension


class FakeChunkRepository:
    def __init__(self):
        self.recorded = {}

    def search_by_embedding(self, user_id, query_vector, top_k):
        self.recorded["vector"] = (user_id, query_vector, top_k)
        return [self._chunk(score=0.9)]

    def search_by_text(self, user_id, query, top_k, language):
        self.recorded["lexical"] = (user_id, query, top_k, language)
        return [self._chunk(score=3.0)]

    @staticmethod
    def _chunk(score):
        return RetrievedChunk(
            chunk_id=1,
            document_id=2,
            content="section content",
            page_number=4,
            page_numbers=[4],
            content_type="text",
            metadata={"source": "pdf"},
            score=score,
        )


@pytest.fixture()
def vector_service():
    return VectorRetrievalService(
        embedding_service=FakeEmbeddingService(),
        chunk_repository=FakeChunkRepository(),
    )


@pytest.fixture()
def retrieval_service():
    repo = FakeChunkRepository()
    return RetrievalService(
        vector_retrieval_service=VectorRetrievalService(
            embedding_service=FakeEmbeddingService(),
            chunk_repository=repo,
        ),
        lexical_retrieval_service=LexicalRetrievalService(
            chunk_repository=repo,
            language=settings.fulltext_search_language,
        ),
    )


def test_vector_retrieval_embeds_query_and_returns_shaped_results(vector_service):
    results = vector_service.retrieve(user_id=42, query="budget analysis", top_k=7)

    assert vector_service.embedding_service.calls == ["budget analysis"]
    assert len(results) == 1
    result = results[0]
    assert isinstance(result, ChunkResult)
    assert result.chunk_id == 1
    assert result.document_id == 2
    assert result.content == "section content"
    assert result.page_number == 4
    assert result.page_numbers == [4]
    assert result.content_type == "text"
    assert result.metadata == {"source": "pdf"}
    assert result.score == pytest.approx(0.9)


def test_vector_retrieval_passes_ownership_and_top_k(vector_service):
    vector_service.retrieve(user_id=42, query="q", top_k=7)

    user_id, query_vector, top_k = vector_service.chunk_repository.recorded["vector"]
    assert user_id == 42
    assert top_k == 7
    assert len(query_vector) == settings.embedding_dimension


def test_lexical_retrieval_returns_shaped_results():
    repo = FakeChunkRepository()
    service = LexicalRetrievalService(chunk_repository=repo)

    results = service.retrieve(user_id=42, query="annual report", top_k=5)

    assert len(results) == 1
    assert results[0].score == pytest.approx(3.0)


def test_lexical_retrieval_passes_language_and_ownership(retrieval_service):
    retrieval_service.search(
        user_id=42, query="annual report", method=RetrievalMethod.LEXICAL, top_k=5
    )

    user_id, query, top_k, language = (
        retrieval_service.lexical_retrieval_service.chunk_repository.recorded["lexical"]
    )
    assert user_id == 42
    assert query == "annual report"
    assert top_k == 5
    assert language == settings.fulltext_search_language


def test_default_top_k_used_when_not_provided(retrieval_service):
    response = retrieval_service.search(
        user_id=42, query="finance", method=RetrievalMethod.VECTOR
    )

    user_id, query_vector, top_k = (
        retrieval_service.vector_retrieval_service.chunk_repository.recorded["vector"]
    )
    assert top_k == settings.retrieval_default_top_k
    assert response.query == "finance"
    assert len(response.results) == 1


def test_top_k_is_clamped_to_maximum(retrieval_service):
    retrieval_service.search(
        user_id=42,
        query="finance",
        method=RetrievalMethod.VECTOR,
        top_k=settings.retrieval_max_top_k + 100,
    )

    user_id, query_vector, top_k = (
        retrieval_service.vector_retrieval_service.chunk_repository.recorded["vector"]
    )
    assert top_k == settings.retrieval_max_top_k


def test_unsupported_method_raises(retrieval_service):
    with pytest.raises(ValueError, match="Unsupported retrieval method"):
        retrieval_service.search(user_id=42, query="q", method="unknown")
