import pytest

from app.services.pdf_parser_service import (
    PdfParseError,
    PdfParserService,
    _is_fragmented,
    _is_multicolumn,
    _merge_fragmented_lines,
    _merge_multicolumn,
    _needs_ocr,
)


@pytest.fixture
def parser_service() -> PdfParserService:
    return PdfParserService()


def test_parse_valid_pdf(tmp_path, parser_service):
    from pypdf import PdfWriter

    pdf_path = tmp_path / "valid.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=300)
    with open(pdf_path, "wb") as file_handle:
        writer.write(file_handle)

    parsed = parser_service.parse(str(pdf_path))

    assert parsed.total_pages == 1
    assert parsed.pages[0].page_number == 1
    assert parsed.pages[0].extracted_text == ""


def test_parse_multiple_pages(tmp_path, parser_service):
    from pypdf import PdfWriter

    pdf_path = tmp_path / "multi.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=300)
    writer.add_blank_page(width=200, height=300)
    writer.add_blank_page(width=200, height=300)
    with open(pdf_path, "wb") as file_handle:
        writer.write(file_handle)

    parsed = parser_service.parse(str(pdf_path))

    assert parsed.total_pages == 3
    assert [p.page_number for p in parsed.pages] == [1, 2, 3]


def test_parse_corrupt_pdf_raises(tmp_path, parser_service):
    pdf_path = tmp_path / "corrupt.pdf"
    pdf_path.write_bytes(b"this is not a pdf")

    with pytest.raises(PdfParseError):
        parser_service.parse(str(pdf_path))


def test_parse_empty_file_raises(tmp_path, parser_service):
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(b"")

    with pytest.raises(PdfParseError):
        parser_service.parse(str(pdf_path))


def test_parse_missing_file_raises(tmp_path, parser_service):
    with pytest.raises(PdfParseError):
        parser_service.parse(str(tmp_path / "missing.pdf"))


# ------------------------------------------------------------------ #
# Heuristic unit tests
# ------------------------------------------------------------------ #

def test_is_fragmented_detects_single_word_lines():
    text = "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nThis is a real line."
    assert _is_fragmented(text) is True


def test_is_fragmented_normal_text_not_fragmented():
    text = (
        "This is a normal paragraph with enough text.\n"
        "Another sentence that is also reasonably long.\n"
        "Third sentence to make sure we have enough lines.\n"
        "Fourth line with substantial content.\n"
        "Fifth line of reasonable length text.\n"
    )
    assert _is_fragmented(text) is False


def test_merge_fragmented_lines_joins_short_lines():
    text = "a\nb\nc\nThis is a real line.\nd\ne"
    result = _merge_fragmented_lines(text)
    assert "a b c" in result
    assert "This is a real line." in result
    assert "d e" in result


def test_merge_fragmented_lines_preserves_paragraph_breaks():
    text = "a\nb\n\nc\nd"
    result = _merge_fragmented_lines(text)
    assert "a b" in result
    assert "c d" in result
    lines = result.split("\n")
    assert "" in lines


def test_is_multicolumn_detects_two_column_layout():
    # Many short lines alternating with many long lines
    lines = []
    for i in range(10):
        lines.append("a")  # left column (1 char)
        lines.append("this is a much longer line from the right column of the document")  # right column
    text = "\n".join(lines)
    assert _is_multicolumn(text) is True


def test_is_multicolumn_single_column_not_detected():
    text = (
        "All lines are roughly the same length here.\n"
        "Another line of similar length text here too.\n"
        "Third line with about the same number of chars.\n"
        "Fourth line also matching in length roughly.\n"
        "Fifth line of similar size text content.\n"
    )
    assert _is_multicolumn(text) is False


def test_merge_multicolumn_separates_columns():
    lines = ["left1", "right1 is longer", "left2", "right2 is longer"]
    text = "\n".join(lines)
    result = _merge_multicolumn(text)
    assert "left1" in result
    assert "left2" in result
    assert "right1 is longer" in result
    assert "right2 is longer" in result
    # Left column should come before right column
    left_pos = result.index("left1")
    right_pos = result.index("right1 is longer")
    assert left_pos < right_pos


def test_needs_ocr_empty_text():
    assert _needs_ocr("") is True


def test_needs_ocr_sparse_text():
    assert _needs_ocr("a\nb\nc") is True


def test_needs_ocr_normal_text_not_ocr():
    assert _needs_ocr("This is a normal document with plenty of text content.") is False