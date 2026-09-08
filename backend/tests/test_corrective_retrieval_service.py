import pytest

from app.core.config import settings
from app.repositories.document_chunk_repository import RetrievedChunk
from app.schemas.evidence import EvidenceVerdict, RefinedQuery
from app.schemas.retrieval import ChunkResult, SearchResponse
from app.services.corrective_retrieval_service import CorrectiveRetrievalService
from app.services.evidence_grader_service import EvidenceGraderService
from app.services.query_refinement_service import QueryRefinementService
from app.services.reranking_service import RerankingService
from app.services.retrieval_service import (
    LexicalRetrievalService,
    RetrievalMethod,
    RetrievalService,
    VectorRetrievalService,
)
from app.services.rrf_service import RRFService


def _chunk(chunk_id, page, score=0.7):
    return ChunkResult(
        chunk_id=chunk_id,
        document_id=chunk_id + 100,
        content=f"content-{chunk_id}",
        page_number=page,
        page_numbers=[page, page + 1],
        content_type="text",
        metadata={"source": "pdf", "page": page},
        score=score,
    )


def _verdict(sufficient, missing=None):
    return EvidenceVerdict(
        sufficient=sufficient,
        confidence_score=0.9 if sufficient else 0.2,
        reason="ok" if sufficient else "need more",
        missing_information=missing or [],
    )


class ScriptedGrader:
    """Returns a scripted verdict per call, recording what it graded."""

    def __init__(self, verdicts):
        self.verdicts = list(verdicts)
        self.calls = []

    def grade(self, query, chunks):
        self.calls.append((query, chunks))
        return self.verdicts[len(self.calls) - 1]


class ScriptedRefiner:
    def __init__(self, refined_query):
        self.refined_query = refined_query
        self.calls = []

    def refine(self, user_query, verdict):
        self.calls.append((user_query, verdict))
        return RefinedQuery(query=self.refined_query, rationale="refined")


class SequentialRefiner:
    """Returns a fresh query on every call so the loop always progresses."""

    def __init__(self, prefix="attempt"):
        self.prefix = prefix
        self.calls = []

    def refine(self, user_query, verdict):
        query = f"{self.prefix}-{len(self.calls) + 1}"
        self.calls.append((user_query, verdict))
        return RefinedQuery(query=query, rationale="refined")


class FakeRetrievalService:
    """Records the pipeline invocation and serves evidence per query."""

    def __init__(self, evidence_by_query):
        self.evidence_by_query = evidence_by_query
        self.calls = []

    def search(self, user_id, query, method, top_k, rerank):
        self.calls.append(
            {
                "user_id": user_id,
                "query": query,
                "method": method,
                "top_k": top_k,
                "rerank": rerank,
            }
        )
        evidence = self.evidence_by_query.get(query, [])
        return SearchResponse(query=query, results=evidence)


def test_returns_immediately_when_evidence_sufficient():
    retrieval = FakeRetrievalService(
        {"question": [_chunk(1, page=2), _chunk(2, page=5)]}
    )
    grader = ScriptedGrader([_verdict(True)])
    refiner = ScriptedRefiner("should not be used")

    service = CorrectiveRetrievalService(retrieval, grader, refiner, max_attempts=2)
    response = service.search(user_id=1, query="question")

    assert response.sufficient is True
    assert response.attempts_used == 0
    assert response.corrective_queries == []
    assert len(retrieval.calls) == 1
    assert refiner.calls == []


def test_successful_corrective_retrieval():
    retrieval = FakeRetrievalService(
        {
            "question": [_chunk(1, page=2)],
            "refined question": [_chunk(3, page=9)],
        }
    )
    grader = ScriptedGrader([_verdict(False, ["details"]), _verdict(True)])
    refiner = ScriptedRefiner("refined question")

    service = CorrectiveRetrievalService(retrieval, grader, refiner, max_attempts=2)
    response = service.search(user_id=7, query="question", top_k=5)

    assert response.sufficient is True
    assert response.attempts_used == 1
    assert response.final_query == "refined question"
    assert response.corrective_queries == ["refined question"]
    assert [c.chunk_id for c in response.evidence] == [3]

    # Both retrievals re-ran the existing hybrid + rerank pipeline.
    assert retrieval.calls[0]["method"] == RetrievalMethod.HYBRID
    assert retrieval.calls[0]["rerank"] is True
    assert retrieval.calls[0]["top_k"] == 5
    assert retrieval.calls[1]["query"] == "refined question"
    assert retrieval.calls[1]["user_id"] == 7


def test_reaches_maximum_attempts():
    retrieval = FakeRetrievalService({})
    grader = ScriptedGrader([_verdict(False, ["missing"])] * 5)
    refiner = SequentialRefiner()

    service = CorrectiveRetrievalService(retrieval, grader, refiner, max_attempts=2)
    response = service.search(user_id=1, query="question")

    assert response.sufficient is False
    assert response.attempts_used == 2
    assert response.max_attempts == 2
    assert len(response.corrective_queries) == 2
    assert response.verdict.missing_information == ["missing"]
    assert len(retrieval.calls) == 3  # initial + 2 corrective attempts


def test_default_max_attempts_from_settings():
    service = CorrectiveRetrievalService(None, None, None)
    assert service.max_attempts == settings.corrective_retrieval_max_attempts


def test_stops_when_refinement_returns_same_query():
    retrieval = FakeRetrievalService({"question": [_chunk(1, page=1)]})
    grader = ScriptedGrader([_verdict(False, ["details"]), _verdict(False)])
    refiner = ScriptedRefiner("question")

    service = CorrectiveRetrievalService(retrieval, grader, refiner, max_attempts=5)
    response = service.search(user_id=1, query="question")

    assert response.sufficient is False
    assert response.attempts_used == 0
    assert response.corrective_queries == []


def test_provenance_preserved_through_pipeline():
    """Provenance survives the real hybrid pipeline + corrective loop."""
    repo = _FixedChunkRepository()

    class FakeEmbeddingService:
        def generate_embedding(self, text):
            return [0.1] * settings.embedding_dimension

    class IdentityRerankProvider:
        def rerank(self, query, contents):
            return [1.0] * len(contents)

    retrieval = RetrievalService(
        vector_retrieval_service=VectorRetrievalService(
            embedding_service=FakeEmbeddingService(),
            chunk_repository=repo,
        ),
        lexical_retrieval_service=LexicalRetrievalService(
            chunk_repository=repo,
            language=settings.fulltext_search_language,
        ),
        rrf_service=RRFService(
            vector_retrieval_service=VectorRetrievalService(
                embedding_service=FakeEmbeddingService(),
                chunk_repository=repo,
            ),
            lexical_retrieval_service=LexicalRetrievalService(
                chunk_repository=repo,
                language=settings.fulltext_search_language,
            ),
        ),
        reranking_service=RerankingService(provider=IdentityRerankProvider()),
    )

    grader = ScriptedGrader([_verdict(False, ["extra"]), _verdict(True)])
    service = CorrectiveRetrievalService(
        retrieval_service=retrieval,
        evidence_grader_service=grader,
        query_refinement_service=ScriptedRefiner("refined query"),
        max_attempts=2,
    )

    response = service.search(user_id=42, query="original", top_k=5)

    assert response.sufficient is True
    assert response.attempts_used == 1
    result = response.evidence[0]
    assert result.chunk_id == 1
    assert result.document_id == 101
    assert result.page_number == 4
    assert result.page_numbers == [4, 5]
    assert result.content_type == "text"
    assert result.metadata == {"source": "pdf", "page": 4}
    assert result.content == "section about revenue"
    assert result.rerank_score is not None

    # The grader also received chunks with untouched provenance.
    first_query, first_chunks = grader.calls[0]
    assert first_query == "original"
    assert grader.calls[1][0] == "refined query"
    for query, chunks in grader.calls:
        assert chunks[0].page_number == 4
        assert chunks[0].page_numbers == [4, 5]
        assert chunks[0].document_id == 101


class _FixedChunkRepository:
    """Feeds the same two chunks to vector and lexical retrieval."""

    @staticmethod
    def _chunks():
        return [
            RetrievedChunk(
                chunk_id=1,
                document_id=101,
                content="section about revenue",
                page_number=4,
                page_numbers=[4, 5],
                content_type="text",
                metadata={"source": "pdf", "page": 4},
                score=0.9,
            ),
            RetrievedChunk(
                chunk_id=2,
                document_id=102,
                content="section about expenses",
                page_number=7,
                page_numbers=[7],
                content_type="text",
                metadata={"source": "pdf", "page": 7},
                score=0.8,
            ),
        ]

    def search_by_embedding(self, user_id, query_vector, top_k):
        return self._chunks()[:top_k]

    def search_by_text(self, user_id, query, top_k, language):
        return self._chunks()[:top_k]