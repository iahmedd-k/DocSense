import pytest

from app.core.config import settings
from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk_repository import DocumentChunkRepository


class FakeDB:
    """Minimal stand-in for ``sqlalchemy.orm.Session``.

    Captures the executed statement so tests can assert on the generated query
    (ownership predicates, ordering, limits) and returns preconfigured rows.
    """

    def __init__(self, rows=None):
        self.rows = rows or []
        self.statements = []

    def execute(self, statement):
        self.statements.append(statement)
        return FakeResult(self.rows)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


def _make_chunk(
    chunk_id=1,
    document_id=1,
    user_id=42,
    page_number=3,
    content="resume section",
    content_type="text",
    metadata=None,
):
    chunk = DocumentChunk()
    chunk.id = chunk_id
    chunk.document_id = document_id
    chunk.user_id = user_id
    chunk.page_number = page_number
    chunk.page_numbers = [page_number]
    chunk.content = content
    chunk.content_type = content_type
    chunk.metadata_ = metadata or {"source": "pdf", "page": page_number}
    chunk.embedding = [0.1] * settings.embedding_dimension
    return chunk


@pytest.fixture()
def repo():
    return DocumentChunkRepository(FakeDB())


def _compiled_sql(repo):
    return [str(stmt.compile()) for stmt in repo.db.statements][-1]


def test_search_by_embedding_returns_mapped_chunks(repo):
    chunk = _make_chunk(chunk_id=7, document_id=2, content="alpha", metadata={"k": "v"})
    repo.db.rows = [(chunk, 0.15)]

    results = repo.search_by_embedding(user_id=42, query_vector=[0.1] * 3, top_k=5)

    assert len(results) == 1
    assert results[0].chunk_id == 7
    assert results[0].document_id == 2
    assert results[0].content == "alpha"
    assert results[0].content_type == "text"
    assert results[0].page_number == 3
    assert results[0].page_numbers == [3]
    assert results[0].metadata == {"k": "v"}
    assert results[0].score == pytest.approx(0.85)


def test_search_by_embedding_filters_by_user(repo):
    repo.db.rows = []

    repo.search_by_embedding(user_id=42, query_vector=[0.1, 0.2, 0.3], top_k=5)

    sql = _compiled_sql(repo)
    assert "document_chunks.user_id" in sql
    assert "=" in sql


def test_search_by_embedding_orders_by_distance_and_limits(repo):
    repo.db.rows = []

    repo.search_by_embedding(user_id=42, query_vector=[0.1] * 3, top_k=5)

    sql = _compiled_sql(repo)
    assert "distance" in sql
    assert "ORDER BY distance" in sql
    assert "LIMIT" in sql


def test_search_by_text_returns_ranked_chunks(repo):
    chunk = _make_chunk(chunk_id=3, document_id=9, content="hello world")
    repo.db.rows = [(chunk, 2.5)]

    results = repo.search_by_text(user_id=42, query="hello", top_k=5, language="english")

    assert len(results) == 1
    assert results[0].chunk_id == 3
    assert results[0].document_id == 9
    assert results[0].content == "hello world"
    assert results[0].score == pytest.approx(2.5)


def test_search_by_text_filters_by_user_and_ranks(repo):
    repo.db.rows = []

    repo.search_by_text(user_id=42, query="financial report", top_k=5, language="english")

    sql = _compiled_sql(repo)
    assert "document_chunks.user_id" in sql
    assert "@@" in sql
    assert "ts_rank" in sql
    assert "websearch_to_tsquery" in sql
    assert "LIMIT" in sql


def test_search_returns_empty_list_when_no_matches(repo):
    repo.db.rows = []

    results = repo.search_by_embedding(user_id=1, query_vector=[0.1] * 3, top_k=3)

    assert results == []
