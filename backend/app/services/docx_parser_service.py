from __future__ import annotations

import logging
from dataclasses import dataclass

from app.services.pdf_parser_service import ParsedPdf, PdfPage

logger = logging.getLogger(__name__)


class DocxParseError(Exception):
    """Raised when a Word document cannot be read or parsed."""


@dataclass
class DocxParserService:
    """Parse Word documents (.docx) into ParsedPdf format.

    The document is split by headings (Heading 1, 2, 3) into logical sections,
    each becoming a separate page. Tables are extracted as pipe-delimited text.
    """

    def parse(self, file_path: str) -> ParsedPdf:
        """Parse a .docx file and return ParsedPdf."""
        try:
            from docx import Document
        except ImportError:
            raise DocxParseError(
                "python-docx is required for Word document support. "
                "Install it with: pip install python-docx"
            )

        try:
            doc = Document(file_path)
        except Exception as exc:
            raise DocxParseError(f"Failed to read Word document: {exc}") from exc

        pages: list[PdfPage] = []
        current_section: list[str] = []
        section_num = 1

        for element in doc.element.body:
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

            if tag in ("heading1", "heading2", "heading3", "Heading1", "Heading2", "Heading3"):
                # Save current section
                if current_section:
                    page_text = "\n\n".join(current_section)
                    pages.append(PdfPage(
                        page_number=section_num,
                        extracted_text=page_text,
                    ))
                    section_num += 1
                    current_section = []

                # Get heading text
                for child in element:
                    child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_tag == "t":
                        text = child.text or ""
                        if text.strip():
                            current_section.append(text.strip())

            elif tag == "p":
                # Regular paragraph
                texts = []
                for child in element:
                    child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_tag == "r":
                        for subchild in child:
                            sub_tag = subchild.tag.split("}")[-1] if "}" in subchild.tag else subchild.tag
                            if sub_tag == "t":
                                texts.append(subchild.text or "")
                text = "".join(texts).strip()
                if text:
                    current_section.append(text)

            elif tag == "tbl":
                # Table
                table_lines = []
                for row_idx, row in enumerate(element):
                    cells = []
                    for cell in row:
                        cell_text = cell.text.strip() if cell.text else ""
                        # Also check for paragraphs inside cells
                        if not cell_text:
                            for p in cell.iter():
                                p_tag = p.tag.split("}")[-1] if "}" in p.tag else p.tag
                                if p_tag == "t" and p.text:
                                    cell_text += p.text
                        cells.append(cell_text.strip())
                    if cells:
                        if table_lines and len(cells) == len(table_lines[0].split(" | ")):
                            pass  # continue table
                        table_lines.append(" | ".join(cells))

                if table_lines:
                    current_section.append("\n".join(table_lines))

        # Don't forget the last section
        if current_section:
            page_text = "\n\n".join(current_section)
            pages.append(PdfPage(
                page_number=section_num,
                extracted_text=page_text,
            ))

        # If no sections found, try a simpler approach
        if not pages:
            full_text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
            if full_text.strip():
                # Split into pages by character count (roughly 2000 chars per page)
                chunk_size = 2000
                for i in range(0, len(full_text), chunk_size):
                    chunk = full_text[i:i + chunk_size]
                    pages.append(PdfPage(
                        page_number=len(pages) + 1,
                        extracted_text=chunk,
                    ))

        return ParsedPdf(pages=pages, total_pages=len(pages))
