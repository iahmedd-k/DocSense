import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk_repository import DocumentChunkRepository


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def repo(db_session) -> DocumentChunkRepository:
    return DocumentChunkRepository(db_session)


def _chunk_dict(
    document_id: int = 1,
    user_id: int = 10,
    page_number: int = 2,
    content: str = "sample chunk content",
    embedding: list[float] | None = None,
) -> dict:
    return {
        "document_id": document_id,
        "user_id": user_id,
        "page_number": page_number,
        "page_numbers": [page_number],
        "content": content,
        "content_type": "text",
        "metadata": {"source": "pdf", "page": page_number},
        "embedding": embedding or [0.1] * settings.embedding_dimension,
    }


def test_create_persists_all_fields(repo, db_session):
    chunk = repo.create(
        document_id=1,
        user_id=10,
        page_number=2,
        page_numbers=[2],
        content="hello world",
        content_type="text",
        metadata={"source": "pdf", "page": 2},
        embedding=[0.5] * settings.embedding_dimension,
    )

    assert chunk.id is not None
    stored = db_session.get(DocumentChunk, chunk.id)
    assert stored.document_id == 1
    assert stored.user_id == 10
    assert stored.page_number == 2
    assert stored.page_numbers == [2]
    assert stored.content == "hello world"
    assert stored.content_type == "text"
    assert stored.metadata_ == {"source": "pdf", "page": 2}
    assert list(stored.embedding) == [0.5] * settings.embedding_dimension
    assert stored.created_at is not None


def test_create_many_persists_all_chunks(repo, db_session):
    chunks = [
        _chunk_dict(page_number=1, content="first chunk"),
        _chunk_dict(page_number=1, content="second chunk"),
        _chunk_dict(page_number=2, content="third chunk"),
    ]

    created = repo.create_many(chunks)

    assert len(created) == 3
    assert [c.id for c in created] == [
        db_session.get(DocumentChunk, c.id).id for c in created
    ]
    contents = {c.content for c in db_session.query(DocumentChunk).all()}
    assert contents == {"first chunk", "second chunk", "third chunk"}


def test_list_by_document_scoped_and_ordered(repo):
    repo.create_many(
        [
            _chunk_dict(document_id=1, content="doc1 a"),
            _chunk_dict(document_id=1, content="doc1 b"),
            _chunk_dict(document_id=2, content="doc2 a"),
        ]
    )

    by_doc1 = repo.list_by_document(1)

    assert [c.content for c in by_doc1] == ["doc1 a", "doc1 b"]


def test_list_by_user_scoped(repo):
    repo.create_many(
        [
            _chunk_dict(user_id=10, content="user10"),
            _chunk_dict(user_id=20, content="user20"),
        ]
    )

    by_user = repo.list_by_user(20)

    assert [c.content for c in by_user] == ["user20"]
    assert all(c.user_id == 20 for c in by_user)


def test_count_by_document(repo):
    repo.create_many(
        [
            _chunk_dict(document_id=1),
            _chunk_dict(document_id=1),
            _chunk_dict(document_id=1),
        ]
    )

    assert repo.count_by_document(1) == 3
    assert repo.count_by_document(999) == 0


def test_delete_by_document_removes_only_that_document(repo):
    repo.create_many(
        [
            _chunk_dict(document_id=1, content="keep-me"),
            _chunk_dict(document_id=1, content="delete-me"),
            _chunk_dict(document_id=2, content="doc2"),
        ]
    )

    repo.delete_by_document(1)

    assert repo.count_by_document(1) == 0
    assert repo.count_by_document(2) == 1


def test_ownership_metadata_preserved_across_round_trip(repo):
    repo.create_many(
        [
            _chunk_dict(user_id=10, document_id=1, page_number=4, content="owned"),
        ]
    )

    stored = repo.list_by_user(10)[0]

    assert stored.document_id == 1
    assert stored.user_id == 10
    assert stored.page_number == 4
    assert stored.page_numbers == [4]
    assert stored.content_type == "text"
    assert stored.metadata_ == {"source": "pdf", "page": 4}
    assert len(stored.embedding) == settings.embedding_dimension