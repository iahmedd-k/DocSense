import pytest

from app.services.pdf_parser_service import (
    PdfParseError,
    PdfParserService,
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