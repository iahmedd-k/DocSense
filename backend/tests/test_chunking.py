import pytest

from app.core.config import settings
from app.schemas.chunk import DocumentChunk
from app.services.chunking_service import ChunkingService
from app.services.pdf_parser_service import ParsedPdf, PdfPage


@pytest.fixture
def chunking_service() -> ChunkingService:
    return ChunkingService()


def _page(number: int, text: str) -> PdfPage:
    return PdfPage(page_number=number, extracted_text=text)


def _parsed(*pages: PdfPage) -> ParsedPdf:
    return ParsedPdf(pages=list(pages), total_pages=len(pages))


def _chunk_types(chunks: list[DocumentChunk]) -> list[str]:
    return [c.content_type for c in chunks]


@pytest.fixture(autouse=True)
def _reset_chunk_settings(monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 500)
    monkeypatch.setattr(settings, "chunk_overlap", 50)


# --------------------------------------------------------------------- #
# Normal text
# --------------------------------------------------------------------- #
def test_normal_paragraph_single_chunk(chunking_service):
    text = (
        "This is the first paragraph of a document describing the product. "
        "It contains several sentences that belong together."
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=7)

    assert len(chunks) == 1
    assert chunks[0].content_type == "text"
    assert chunks[0].document_id == 7
    assert chunks[0].page_number == 1
    assert chunks[0].content == text


def test_normal_text_long_gets_split_with_overlap(chunking_service, monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 50)
    monkeypatch.setattr(settings, "chunk_overlap", 10)

    paragraph = "word " * 40  # ~200 chars, should split
    chunks = chunking_service.chunk_document(_parsed(_page(1, paragraph)), document_id=1)

    assert len(chunks) > 1
    assert all(len(c.content) <= 50 for c in chunks)
    assert all(c.content_type == "text" for c in chunks)
    joined = " ".join(c.content for c in chunks)
    assert "word" in joined


def test_normal_text_chunks_overlap(chunking_service, monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 60)
    monkeypatch.setattr(settings, "chunk_overlap", 20)

    paragraph = "the quick brown fox jumps over the lazy dog. " * 5
    chunks = chunking_service.chunk_document(_parsed(_page(1, paragraph)), document_id=5)

    assert len(chunks) >= 2
    # Consecutive chunks should share overlapping tail content.
    assert chunks[0].content[-15:] in chunks[1].content


def test_normal_text_groups_related_paragraphs(chunking_service):
    text = (
        "First related paragraph sentence one. First related paragraph sentence two.\n"
        "Second related paragraph sentence one. Second related paragraph sentence two."
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=3)

    # Both paragraphs stay together in a single chunk.
    assert len(chunks) == 1
    assert "First related paragraph" in chunks[0].content
    assert "Second related paragraph" in chunks[0].content


# --------------------------------------------------------------------- #
# Headings
# --------------------------------------------------------------------- #
def test_heading_kept_with_section_content(chunking_service):
    text = (
        "Introduction\n"
        "This section explains the background and motivation for the project."
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=2)

    assert len(chunks) == 2
    assert chunks[0].content_type == "heading"
    assert chunks[0].content == "Introduction"
    assert chunks[1].content_type == "text"
    assert "background and motivation" in chunks[1].content


def test_heading_lone_when_no_content(chunking_service):
    text = "Appendix A"
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=4)

    assert len(chunks) == 1
    assert chunks[0].content_type == "heading"
    assert chunks[0].content == "Appendix A"


# --------------------------------------------------------------------- #
# Lists
# --------------------------------------------------------------------- #
def test_list_items_kept_together(chunking_service):
    text = (
        "- First benefit of the product.\n"
        "- Second benefit of the product.\n"
        "- Third benefit of the product."
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=6)

    assert len(chunks) == 1
    assert chunks[0].content_type == "list"
    assert "First benefit" in chunks[0].content
    assert "Third benefit" in chunks[0].content


def test_large_list_split_by_size_not_in_middle(chunking_service, monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 40)

    text = "\n".join(f"- item {i} with some descriptive text" for i in range(10))
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=8)
    list_chunks = [c for c in chunks if c.content_type == "list"]

    assert len(list_chunks) > 1
    assert all(len(c.content) <= 40 for c in list_chunks)


# --------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------- #
def test_small_table_one_chunk(chunking_service):
    text = (
        "Year | Revenue | Profit\n"
        "2024 | $10M | $2M\n"
        "2025 | $14M | $3M"
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=9)

    assert len(chunks) == 1
    table = chunks[0]
    assert table.content_type == "table"
    assert "Year | Revenue | Profit" in table.content
    assert "2024 | $10M | $2M" in table.content
    assert "2025 | $14M | $3M" in table.content
    assert "|" in table.content  # row/column relationships preserved


def test_large_table_split_by_rows_with_repeated_header(chunking_service, monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 40)

    lines = ["Month | Sales | Costs"]
    for i in range(10):
        lines.append(f"{i:02d} | $100 | $50")
    text = "\n".join(lines)

    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=10)
    table_chunks = [c for c in chunks if c.content_type == "table"]

    assert len(table_chunks) > 1
    for tc in table_chunks:
        assert "Month | Sales | Costs" in tc.content  # header repeated
        assert tc.document_id == 10


# --------------------------------------------------------------------- #
# Page provenance
# --------------------------------------------------------------------- #
def test_chunks_preserve_page_number(chunking_service):
    page1 = _page(1, (
        "Title\n"
        "Paragraph of content on the first page."
    ))
    page2 = _page(2, (
        "More content\n"
        "Paragraph of content on the second page."
    ))
    chunks = chunking_service.chunk_document(_parsed(page1, page2), document_id=12)

    page_chunks = [c for c in chunks if c.content_type == "text"]
    assert {c.page_number for c in page_chunks} == {1, 2}
    assert all(c.document_id == 12 for c in chunks)
    assert all([c.page_number] == c.page_numbers for c in chunks)


def test_every_chunk_has_required_fields(chunking_service):
    text = (
        "Heading\n"
        "Some paragraph text content here.\n"
        "- a list item\n"
        "2024 | A | B\n"
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=13)

    assert chunks
    for chunk in chunks:
        assert chunk.chunk_id
        assert chunk.chunk_id.startswith("doc-13-")
        assert chunk.document_id == 13
        assert chunk.page_number == 1
        assert isinstance(chunk.page_numbers, list)
        assert chunk.content
        assert chunk.content_type in {"text", "heading", "list", "table"}
        assert chunk.metadata["page"] == 1


# --------------------------------------------------------------------- #
# Chunk size / overlap configuration
# --------------------------------------------------------------------- #
def test_chunk_size_config_respected(chunking_service, monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 5)
    text = "abcdefghijklmnopqrst"  # 20 chars
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=14)

    assert all(len(c.content) <= 5 for c in chunks)


def test_chunk_overlap_greater_than_size_is_safe(chunking_service, monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 20)
    monkeypatch.setattr(settings, "chunk_overlap", 100)


def test_overlap_never_exceeds_producing_empty_chunks(chunking_service, monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 10)
    monkeypatch.setattr(settings, "chunk_overlap", 5)
    text = "0123456789" * 5
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=15)

    assert chunks
    assert all(c.content for c in chunks)
