import pytest

from app.core.config import settings
from app.schemas.retrieval import ChunkResult
from app.services.reranking_service import (
    RerankingError,
    RerankingService,
)


def _chunk(chunk_id, score=1.0, content="content"):
    return ChunkResult(
        chunk_id=chunk_id,
        document_id=chunk_id,
        content=content,
        page_number=2,
        page_numbers=[2],
        content_type="text",
        metadata={"source": "pdf", "page": 2},
        score=score,
    )


class FakeCrossEncoderProvider:
    """Deterministic fake: returns scores such that chunk_id matches score."""

    def __init__(self, scores=None):
        self.scores = scores
        self.calls = []

    def rerank(self, query, contents):
        self.calls.append((query, contents))
        if self.scores is not None:
            return self.scores
        return [float(len(contents) - i) for i in range(len(contents))]


@pytest.fixture()
def reranking_service():
    return RerankingService(provider=FakeCrossEncoderProvider())


def test_sorts_by_descending_rerank_score(reranking_service):
    candidates = [
        _chunk(1, score=0.3),
        _chunk(2, score=0.9),
        _chunk(3, score=0.5),
    ]
    # Fake scores: [3.0, 1.0, 2.0] -> order should become 1, 3, 2
    reranking_service.provider.scores = [3.0, 1.0, 2.0]

    results = reranking_service.rerank(
        query="budget", candidates=candidates, top_n=3
    )

    assert [c.chunk_id for c in results] == [1, 3, 2]
    assert [c.rerank_score for c in results] == [3.0, 2.0, 1.0]


def test_returns_top_n_only(reranking_service):
    candidates = [_chunk(i) for i in range(1, 6)]
    # scores equal to chunk index+1 so higher chunk_id is more relevant
    reranking_service.provider.scores = [float(i + 1) for i in range(5)]

    results = reranking_service.rerank(
        query="budget", candidates=candidates, top_n=2
    )

    assert len(results) == 2
    assert results[0].chunk_id == 5
    assert results[1].chunk_id == 4


def test_preserves_chunk_metadata(reranking_service):
    candidates = [
        _chunk(7, score=0.1, content="unique content"),
    ]
    reranking_service.provider.scores = [2.5]

    results = reranking_service.rerank(query="q", candidates=candidates, top_n=1)

    result = results[0]
    assert result.chunk_id == 7
    assert result.document_id == 7
    assert result.content == "unique content"
    assert result.page_number == 2
    assert result.page_numbers == [2]
    assert result.content_type == "text"
    assert result.metadata == {"source": "pdf", "page": 2}


def test_rerank_score_assigned_and_original_score_kept(reranking_service):
    candidates = [_chunk(1, score=0.42)]
    reranking_service.provider.scores = [0.99]

    results = reranking_service.rerank(query="q", candidates=candidates, top_n=1)

    assert results[0].rerank_score == pytest.approx(0.99)
    assert results[0].score == pytest.approx(0.42)


def test_empty_candidates_returns_empty(reranking_service):
    assert reranking_service.rerank(query="q", candidates=[], top_n=3) == []


def test_provider_receives_query_and_contents(reranking_service):
    candidates = [_chunk(1, content="alpha"), _chunk(2, content="beta")]
    reranking_service.provider.scores = [0.5, 0.6]

    reranking_service.rerank(query="my query", candidates=candidates, top_n=2)

    assert reranking_service.provider.calls == [("my query", ["alpha", "beta"])]


def test_score_count_mismatch_raises(reranking_service):
    candidates = [_chunk(1), _chunk(2)]
    reranking_service.provider.scores = [0.5]

    with pytest.raises(RerankingError, match="Expected 2 rerank scores"):
        reranking_service.rerank(query="q", candidates=candidates, top_n=2)


def test_default_top_n_from_settings():
    service = RerankingService(provider=FakeCrossEncoderProvider())
    candidates = [_chunk(i) for i in range(10)]
    service.provider.scores = [float(i) for i in range(10, 0, -1)]

    results = service.rerank(query="q", candidates=candidates)

    assert len(results) == min(10, settings.reranker_max_results)


def test_top_n_clamped_to_max_results():
    service = RerankingService(provider=FakeCrossEncoderProvider())
    candidates = [_chunk(i) for i in range(1, settings.reranker_max_results + 20)]
    service.provider.scores = [float(i + 1) for i in range(len(candidates))]

    results = service.rerank(
        query="q", candidates=candidates, top_n=settings.reranker_max_results + 50
    )

    assert len(results) == settings.reranker_max_results


def test_default_provider_uses_configured_model(monkeypatch):
    monkeypatch.setattr(settings, "reranker_model", "cross-encoder/ms-marco-MiniLM-L-6-v2")

    service = RerankingService()
    provider = service.provider

    assert provider.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"