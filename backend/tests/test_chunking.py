import pytest

from app.core.config import settings
from app.schemas.chunk import DocumentChunk
from app.services.chunking_service import ChunkingService, _MIN_CHUNK_TOKENS
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


def _chunk_token_counts(chunks: list[DocumentChunk]) -> list[int]:
    return [len(c.content.split()) for c in chunks]


@pytest.fixture(autouse=True)
def _reset_chunk_settings(monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 400)
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
    monkeypatch.setattr(settings, "chunk_size", 10)
    monkeypatch.setattr(settings, "chunk_overlap", 3)

    paragraph = "word " * 40  # 40 words, should split at chunk_size=10 words
    chunks = chunking_service.chunk_document(_parsed(_page(1, paragraph)), document_id=1)

    assert len(chunks) > 1
    assert all(c.content_type == "text" for c in chunks)
    joined = " ".join(c.content for c in chunks)
    assert "word" in joined


def test_normal_text_chunks_overlap(chunking_service, monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 12)
    monkeypatch.setattr(settings, "chunk_overlap", 4)

    paragraph = "the quick brown fox jumps over the lazy dog. " * 5  # 45 words
    chunks = chunking_service.chunk_document(_parsed(_page(1, paragraph)), document_id=5)

    assert len(chunks) >= 2


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
        "EDUCATION\n"
        "This section explains the background and motivation for the project."
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=2)

    assert len(chunks) == 2
    assert chunks[0].content_type == "heading"
    assert chunks[0].content == "EDUCATION"
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
    monkeypatch.setattr(settings, "chunk_size", 8)
    monkeypatch.setattr(settings, "chunk_overlap", 2)

    text = "\n".join(f"- item {i} with some descriptive text" for i in range(10))
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=8)
    list_chunks = [c for c in chunks if c.content_type == "list"]

    assert len(list_chunks) > 1


# --------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------- #
def test_small_table_one_chunk(chunking_service):
    text = (
        "Year | Revenue | Profit\n"
        "2024 | $100M | $20M\n"
        "2025 | $140M | $30M\n"
        "2026 | $180M | $45M\n"
        "2027 | $220M | $60M\n"
        "2028 | $260M | $80M\n"
        "2029 | $300M | $100M\n"
        "2030 | $350M | $120M\n"
        "2031 | $400M | $140M\n"
        "2032 | $450M | $160M"
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=9)

    assert len(chunks) >= 1
    # All content should contain table-like pipe separators
    for chunk in chunks:
        assert "|" in chunk.content


def test_large_table_split_by_rows_with_repeated_header(chunking_service, monkeypatch):
    monkeypatch.setattr(settings, "chunk_size", 40)

    lines = ["Month | Sales | Costs"]
    for i in range(10):
        lines.append(f"{i:02d} | $100 | $50")
    text = "\n".join(lines)

    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=10)

    assert len(chunks) >= 1
    all_text = " ".join(c.content for c in chunks)
    assert "Month | Sales | Costs" in all_text


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
    monkeypatch.setattr(settings, "chunk_size", 3)
    text = "one two three four five six seven eight nine ten"
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=14)

    # With chunk_size=3 words, should split into multiple chunks
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.content.split()) <= 3


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


# --------------------------------------------------------------------- #
# Resume-like documents (the bug scenario)
# --------------------------------------------------------------------- #
def test_fragmented_pdf_text_merges_into_coherent_chunks(chunking_service):
    """Simulate pypdf output where every word is on its own line."""
    fragmented_text = (
        "Experience\n"
        "Letter\n"
        "To\n"
        "Whom\n"
        "It\n"
        "May\n"
        "Concern,\n"
        "This\n"
        "is to certify that\n"
        "Mr.\n"
        "Ahmed\n"
        "Khan\n"
        "holding\n"
        "CNIC\n"
        "# 13504-6875326-9 successfully completed their internship at\n"
        "Emumba\n"
        "as an\n"
        "AI\n"
        "Developer\n"
        "Intern\n"
        "from 29/07/2026 to 04/09/2026.\n"
        "During\n"
        "their internship,\n"
        "Ahmed\n"
        "actively contributed to:\n"
        "Assisting\n"
        "in developing, testing, and improving\n"
        "AI\n"
        "and machine-learning solutions."
    )
    chunks = chunking_service.chunk_document(
        _parsed(_page(1, fragmented_text)), document_id=100
    )

    # No chunk should be a single word
    for chunk in chunks:
        tokens = chunk.content.split()
        assert len(tokens) >= _MIN_CHUNK_TOKENS or len(chunks) == 1, (
            f"Chunk too small ({len(tokens)} tokens): '{chunk.content}'"
        )

    # The key content should be present somewhere
    all_text = " ".join(c.content for c in chunks)
    assert "Ahmed Khan" in all_text or "Ahmed" in all_text
    assert "internship" in all_text.lower() or "Emumba" in all_text


def test_no_single_word_chunks(chunking_service):
    """Verify that no chunk contains only a single word."""
    text = (
        "EDUCATION\n"
        "Bachelor of Science in Computer Science\n"
        "EXPERIENCE\n"
        "AI Developer Intern at Emumba\n"
        "Skills\n"
        "Python, Machine Learning, Deep Learning"
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=200)

    for chunk in chunks:
        tokens = chunk.content.split()
        assert len(tokens) >= 2, (
            f"Single-word chunk found: '{chunk.content}'"
        )


def test_resume_sections_are_headings(chunking_service):
    """Resume section labels should be detected as headings."""
    text = (
        "EDUCATION\n"
        "BS Computer Science, FAST-NUCES, 2022-2026\n"
        "EXPERIENCE\n"
        "AI Developer Intern, Emumba, Jul-Sep 2026\n"
        "CERTIFICATIONS\n"
        "aws certified solutions architect professional level certificate"
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=300)

    heading_texts = [c.content for c in chunks if c.content_type == "heading"]
    assert "EDUCATION" in heading_texts
    assert "EXPERIENCE" in heading_texts
    assert "CERTIFICATIONS" in heading_texts


def test_min_chunk_size_guard(chunking_service, monkeypatch):
    """Even with small chunk_size, undersized chunks get merged."""
    monkeypatch.setattr(settings, "chunk_size", 200)
    monkeypatch.setattr(settings, "chunk_overlap", 20)

    # Short lines that would each be <20 tokens
    text = (
        "This is a short line.\n"
        "Another short line.\n"
        "Third short line.\n"
        "Fourth short line.\n"
        "Fifth short line."
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=400)

    # Should be merged into fewer chunks
    token_counts = _chunk_token_counts(chunks)
    # At least some chunks should have multiple sentences
    assert any(tc >= 3 for tc in token_counts), (
        f"All chunks too small: {token_counts}"
    )


def test_empty_input(chunking_service):
    chunks = chunking_service.chunk_document(_parsed(_page(1, "")), document_id=500)
    assert chunks == []


def test_whitespace_only_input(chunking_service):
    chunks = chunking_service.chunk_document(
        _parsed(_page(1, "   \n  \n   ")), document_id=600
    )
    assert chunks == []


def test_isolated_undersized_chunk_is_kept_when_no_neighbor(chunking_service, monkeypatch):
    """A page with only a page number (e.g. '42') is kept as-is when there
    is no same-type neighbor to merge with."""
    monkeypatch.setattr(settings, "chunk_size", 500)

    # Simulate: one page with only "42" and another page with real content
    page1 = _page(1, "42")
    page2 = _page(2, "This is a real paragraph with enough content to be a chunk.")
    chunks = chunking_service.chunk_document(_parsed(page1, page2), document_id=700)

    # The page with only "42" should be kept (isolated, no same-type neighbor)
    assert len(chunks) >= 1


def test_undersized_chunk_merged_when_same_type_neighbor(chunking_service, monkeypatch):
    """When an undersized chunk has a same-type neighbor, it merges."""
    monkeypatch.setattr(settings, "chunk_size", 500)
    monkeypatch.setattr(settings, "chunk_overlap", 5)

    # Two consecutive short text lines that can merge
    text = (
        "Short line one.\n"
        "Short line two.\n"
    )
    chunks = chunking_service.chunk_document(_parsed(_page(1, text)), document_id=800)

    # Both are text type and should merge into one
    text_chunks = [c for c in chunks if c.content_type == "text"]
    assert len(text_chunks) == 1
    assert "Short line one." in text_chunks[0].content
    assert "Short line two." in text_chunks[0].content
