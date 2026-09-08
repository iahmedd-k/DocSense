import pytest

from app.core.config import settings
from app.schemas.retrieval import ChunkResult
from app.services.retrieval_service import LexicalRetrievalService, RetrievalMethod
from app.services.rrf_service import RRFService


def _chunk(chunk_id, score=0.0, content="content"):
    return ChunkResult(
        chunk_id=chunk_id,
        document_id=chunk_id,
        content=content,
        page_number=1,
        page_numbers=[1],
        content_type="text",
        metadata={"source": "pdf"},
        score=score,
    )


@pytest.fixture()
def rrf_service():
    return RRFService(
        vector_retrieval_service=None,
        lexical_retrieval_service=None,
        k=1,
    )


class FakeRetrievalService:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def retrieve(self, user_id, query, top_k):
        self.calls.append((user_id, query, top_k))
        return self.results


@pytest.fixture()
def orchestrated_service():
    vector = FakeRetrievalService([_chunk(1), _chunk(2)])
    lexical = FakeRetrievalService([_chunk(3)])
    return (
        RRFService(
            vector_retrieval_service=vector,
            lexical_retrieval_service=lexical,
            k=1,
        ),
        vector,
        lexical,
    )


def test_rrf_combines_duplicate_chunks(rrf_service):
    vector = [_chunk(10, content="shared")]
    lexical = [_chunk(10, content="shared")]

    fused = rrf_service.fuse(vector, lexical)

    assert len(fused) == 1
    assert fused[0].chunk_id == 10
    # rank 1 in both lists -> 1/2 + 1/2
    assert fused[0].score == pytest.approx(1.0)


def test_rrf_keeps_single_list_chunks(rrf_service):
    vector = [_chunk(10), _chunk(11)]
    lexical = [_chunk(20), _chunk(21)]

    fused = rrf_service.fuse(vector, lexical)

    assert {c.chunk_id for c in fused} == {10, 11, 20, 21}


def test_rrf_rank_based_scoring(rrf_service):
    vector = [_chunk(10), _chunk(11)]
    lexical = [_chunk(10), _chunk(12)]

    fused = {c.chunk_id: c.score for c in rrf_service.fuse(vector, lexical)}

    # chunk 10: rank1 in both -> 1/2 + 1/2 = 1.0
    assert fused[10] == pytest.approx(1.0)
    # chunk 11: only rank2 in vector -> 1/3
    assert fused[11] == pytest.approx(1 / 3)
    # chunk 12: only rank2 in lexical -> 1/3
    assert fused[12] == pytest.approx(1 / 3)


def test_rrf_sorts_by_descending_score(rrf_service):
    # chunk 10: rank1-only (0.5); chunk 11: rank2 vector + rank1 lexical
    # (1/3 + 1/2 = 5/6); chunk 12: rank2-only (1/3)
    vector = [_chunk(10), _chunk(11)]
    lexical = [_chunk(11), _chunk(12)]

    fused = rrf_service.fuse(vector, lexical)

    scores = [c.score for c in fused]
    assert scores == sorted(scores, reverse=True)
    assert fused[0].chunk_id == 11
    assert fused[0].score == pytest.approx(5 / 6)


def test_rrf_deduplicates_by_chunk_id(rrf_service):
    vector = [_chunk(10), _chunk(10), _chunk(11)]
    lexical = [_chunk(10), _chunk(11), _chunk(11)]

    fused = rrf_service.fuse(vector, lexical)

    chunk_ids = [c.chunk_id for c in fused]
    assert chunk_ids == [10, 11]
    assert len({c.chunk_id for c in fused}) == len(fused)


def test_rrf_empty_lists(rrf_service):
    assert rrf_service.fuse([], []) == []


def test_rrf_rejects_non_positive_k():
    with pytest.raises(ValueError):
        RRFService(None, None, k=0).fuse([_chunk(1)], [_chunk(1)])


def test_rrf_search_calls_both_retrievals_and_passes_user_id(
    orchestrated_service,
):
    rrf, vector, lexical = orchestrated_service

    results = rrf.search(user_id=42, query="quarterly earnings", top_k=7)

    assert vector.calls == [(42, "quarterly earnings", 7)]
    assert lexical.calls == [(42, "quarterly earnings", 7)]
    assert {c.chunk_id for c in results} == {1, 2, 3}


def test_rrf_default_k_from_settings():
    service = RRFService(vector_retrieval_service=None, lexical_retrieval_service=None)

    assert service.k == settings.rrf_k
    assert settings.rrf_k == 60


def test_hybrid_method_enum_exists():
    assert RetrievalMethod.HYBRID.value == "hybrid"


def test_rrf_uses_k_in_scoring():
    service = RRFService(None, None, k=60)

    fused = service.fuse([_chunk(10)], [_chunk(10)])

    assert fused[0].score == pytest.approx(2 * (1 / (60 + 1)))
