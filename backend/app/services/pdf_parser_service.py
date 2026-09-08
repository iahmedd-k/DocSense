import os
from dataclasses import dataclass, field

from pypdf import PdfReader


class PdfParseError(Exception):
    """Raised when a PDF cannot be read or parsed."""


@dataclass
class PdfPage:
    page_number: int
    extracted_text: str


@dataclass
class ParsedPdf:
    pages: list[PdfPage] = field(default_factory=list)
    total_pages: int = 0


class PdfParserService:

    def parse(self, file_path: str) -> ParsedPdf:
        """Parse a PDF file page by page, returning extracted text per page."""

        if not os.path.isfile(file_path):
            raise PdfParseError(f"PDF file not found: {file_path}")

        try:
            with open(file_path, "rb") as file_handle:
                reader = PdfReader(file_handle)
                pages = []
                for page_number, page in enumerate(reader.pages, start=1):
                    pages.append(
                        PdfPage(
                            page_number=page_number,
                            extracted_text=page.extract_text() or "",
                        )
                    )
        except Exception as exc:
            raise PdfParseError(f"Failed to parse PDF '{file_path}'") from exc

        if not pages:
            raise PdfParseError(f"PDF '{file_path}' has no readable pages")

        return ParsedPdf(pages=pages, total_pages=len(pages))