import re
from uuid import uuid4

from app.core.config import settings
from app.schemas.chunk import DocumentChunk
from app.services.pdf_parser_service import ParsedPdf


class ContentType:
    TEXT = "text"
    HEADING = "heading"
    LIST = "list"
    TABLE = "table"


# Headings look like short, non-punctuated section titles. Common forms:
#   "Introduction", "3. Results", "Section 2: Background", "APPENDIX A".
_HEADING_RE = re.compile(
    r"^\s*(?:(?:section|chapter|appendix)\s+)?"
    r"(?:[A-Z][A-Za-z0-9'&.-]*(?:\s+[A-Z][A-Za-z0-9'&.-]*)*|"
    r"\d+(?:\.\d+)*[.:]?)"
    r"(?::.*)?\s*$"
)

# A bullet/numbered list marker. Covers "-", "*", "•", "1.", "a)", "(i)" etc.
_LIST_RE = re.compile(
    r"^\s*(?:[-*•◦▪]|\d{1,3}[.)]|[a-z][.)]|[ivxIVX]+[.)]|\([a-z0-9]+\))\s+"
)

# A table row has at least two columns separated by a "|" or multiple spaces.
_TABLE_ROW_RE = re.compile(r"^\s*(?:[^|]*\|[^|]*){1,}\s*$")
_WIDE_SPACE_TABLE_RE = re.compile(r"^\s*\S+(?:  +\S+)+\s*$")


class ChunkingService:

    def chunk_document(self, parsed: ParsedPdf, document_id: int) -> list[DocumentChunk]:
        """Convert a parsed PDF into structure-aware in-memory chunks.

        Chunks are transient objects; nothing is written to any persistence layer.
        """
        chunks: list[DocumentChunk] = []
        counter = 0

        for page in parsed.pages:
            blocks = self._split_into_blocks(page.extracted_text)
            for block in blocks:
                block_chunks = self._chunk_block(
                    block,
                    document_id=document_id,
                    page_number=page.page_number,
                    seq_start=counter,
                )
                for chunk in block_chunks:
                    counter += 1
                    chunks.append(chunk)

        return chunks

    # ------------------------------------------------------------------ #
    # Structure detection
    # ------------------------------------------------------------------ #

    def _split_into_blocks(self, text: str) -> list[dict]:
        """Split raw page text into structural blocks (dicts).

        Each block is one of:
            {"type": "text",     "lines": [...]}
            {"type": "heading",  "text": "..."}
            {"type": "list",     "items": [...]}
            {"type": "table",    "rows": [[...], ...], "header": [...]}
        """
        raw_lines = [ln for ln in text.splitlines() if ln.strip()]
        if not raw_lines:
            return []

        blocks: list[dict] = []
        i = 0
        n = len(raw_lines)

        while i < n:
            line = raw_lines[i]

            if self._is_heading(line):
                blocks.append({"type": ContentType.HEADING, "text": line.strip()})
                i += 1
                continue

            if self._is_table_row(line) and self._starts_table(raw_lines, i):
                header, body, next_i = self._collect_table(raw_lines, i)
                blocks.append(
                    {"type": ContentType.TABLE, "header": header, "rows": body}
                )
                i = next_i
                continue

            if _LIST_RE.match(line):
                items, next_i = self._collect_list(raw_lines, i)
                blocks.append({"type": ContentType.LIST, "items": items})
                i = next_i
                continue

            # Normal text: gather a paragraph (consecutive non-structural lines).
            para_lines = [line]
            j = i + 1
            while (
                j < n
                and not self._is_heading(raw_lines[j])
                and not _LIST_RE.match(raw_lines[j])
                and not (
                    self._is_table_row(raw_lines[j])
                    and self._starts_table(raw_lines, j)
                )
            ):
                para_lines.append(raw_lines[j])
                j += 1
            blocks.append({"type": ContentType.TEXT, "lines": para_lines})
            i = j

        return blocks

    @staticmethod
    def _is_heading(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        # A heading fits on a single short line with no terminal punctuation.
        if len(stripped) > 80:
            return False
        if _LIST_RE.match(stripped):
            return False
        if _TABLE_ROW_RE.match(stripped):
            return False
        return bool(_HEADING_RE.match(stripped)) 

    @staticmethod
    def _is_table_row(line: str) -> bool:
        return bool(_TABLE_ROW_RE.match(line)) or bool(
            _WIDE_SPACE_TABLE_RE.match(line)
        )

    @staticmethod
    def _starts_table(lines: list[str], i: int) -> bool:
        # A table needs a header (or at least) two consecutive table-like rows.
        return i + 1 < len(lines) and (
            _TABLE_ROW_RE.match(lines[i]) and _TABLE_ROW_RE.match(lines[i + 1])
        ) or (
            i + 1 < len(lines)
            and _WIDE_SPACE_TABLE_RE.match(lines[i])
            and _WIDE_SPACE_TABLE_RE.match(lines[i + 1])
        )

    @staticmethod
    def _collect_table(lines: list[str], i: int) -> tuple[list[str], list[list[str]], int]:
        rows: list[list[str]] = []
        j = i
        while j < len(lines):
            line = lines[j]
            if _TABLE_ROW_RE.match(line) or _WIDE_SPACE_TABLE_RE.match(line):
                rows.append(_split_row(line))
                j += 1
            else:
                break
        if not rows:
            rows = [[lines[i]]]
            j = i + 1
        header = rows[0]
        body = rows[1:]
        return header, body, j

    @staticmethod
    def _collect_list(lines: list[str], i: int) -> tuple[list[str], int]:
        items: list[str] = []
        j = i
        while j < len(lines):
            line = lines[j]
            if _LIST_RE.match(line):
                items.append(line.strip())
                j += 1
            else:
                break
        return items, j

    # ------------------------------------------------------------------ #
    # Chunk construction
    # ------------------------------------------------------------------ #

    def _chunk_block(
        self,
        block: dict,
        document_id: int,
        page_number: int,
        seq_start: int,
    ) -> list[DocumentChunk]:
        if block["type"] == ContentType.TABLE:
            return self._chunk_table(
                block,
                document_id=document_id,
                page_number=page_number,
                seq_start=seq_start,
            )
        if block["type"] == ContentType.LIST:
            return self._chunk_list(
                block,
                document_id=document_id,
                page_number=page_number,
                seq_start=seq_start,
            )
        if block["type"] == ContentType.HEADING:
            return self._chunk_heading(
                block,
                document_id=document_id,
                page_number=page_number,
                seq_start=seq_start,
            )
        return self._chunk_text(
            block,
            document_id=document_id,
            page_number=page_number,
            seq_start=seq_start,
        )

    def _make_chunk(
        self,
        document_id: int,
        page_number: int,
        content: str,
        content_type: str,
        seq: int,
    ) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=f"doc-{document_id}-{seq + 1}",
            document_id=document_id,
            page_number=page_number,
            page_numbers=[page_number],
            content=content,
            content_type=content_type,
            metadata={"source": "pdf", "page": page_number},
        )

    # -- headings ----------------------------------------------------- #
    def _chunk_heading(
        self,
        block: dict,
        document_id: int,
        page_number: int,
        seq_start: int,
    ) -> list[DocumentChunk]:
        text = block["text"]
        if len(text) <= settings.chunk_size:
            return [
                self._make_chunk(
                    document_id,
                    page_number,
                    text,
                    ContentType.HEADING,
                    seq_start,
                )
            ]
        # Extremely rare: a heading larger than the chunk size.
        return self._split_text(
            text,
            document_id,
            page_number,
            ContentType.HEADING,
            seq_start,
        )

    # -- normal text -------------------------------------------------- #
    def _chunk_text(
        self,
        block: dict,
        document_id: int,
        page_number: int,
        seq_start: int,
    ) -> list[DocumentChunk]:
        paragraph = " ".join(ln.strip() for ln in block["lines"]).strip()
        if not paragraph:
            return []
        if len(paragraph) <= settings.chunk_size:
            return [
                self._make_chunk(
                    document_id,
                    page_number,
                    paragraph,
                    ContentType.TEXT,
                    seq_start,
                )
            ]
        return self._split_text(
            paragraph,
            document_id,
            page_number,
            ContentType.TEXT,
            seq_start,
        )

    # -- lists -------------------------------------------------------- #
    def _chunk_list(
        self,
        block: dict,
        document_id: int,
        page_number: int,
        seq_start: int,
    ) -> list[DocumentChunk]:
        items = block["items"]
        groups: list[list[str]] = []
        current: list[str] = []

        for item in items:
            if len(item) > settings.chunk_size:
                if current:
                    groups.append(current)
                    current = []
                groups.append([item])
                continue
            trial = " ".join(current + [item])
            if current and len(trial) > settings.chunk_size:
                groups.append(current)
                current = [item]
            else:
                current.append(item)
        if current:
            groups.append(current)

        chunks: list[DocumentChunk] = []
        seq = seq_start
        for group in groups:
            content = " ".join(group)
            if len(content) <= settings.chunk_size:
                chunks.append(
                    self._make_chunk(
                        document_id,
                        page_number,
                        content,
                        ContentType.LIST,
                        seq,
                    )
                )
                seq += 1
            else:
                sub_chunks = self._split_text(
                    content,
                    document_id,
                    page_number,
                    ContentType.LIST,
                    seq,
                )
                chunks.extend(sub_chunks)
                seq += len(sub_chunks)
        return chunks

    # -- tables ------------------------------------------------------- #
    def _chunk_table(
        self,
        block: dict,
        document_id: int,
        page_number: int,
        seq_start: int,
    ) -> list[DocumentChunk]:
        header = block["header"]
        body = block["rows"]
        header_text = _render_table_header(header)

        if len(body) <= 1:
            content = _render_table(header, body)
            return [
                self._make_chunk(
                    document_id,
                    page_number,
                    content,
                    ContentType.TABLE,
                    seq_start,
                )
            ]

        # Large table: split by rows, repeating the header in every chunk.
        chunks: list[DocumentChunk] = []
        seq = seq_start
        group: list[list[str]] = []
        current_size = 0

        for row in body:
            row_size = len(_render_row(row))
            if group and current_size + row_size > settings.chunk_size:
                content = _render_table_with_header(header_text, group)
                chunks.append(
                    self._make_chunk(
                        document_id,
                        page_number,
                        content,
                        ContentType.TABLE,
                        seq,
                    )
                )
                seq += 1
                group = [row]
                current_size = row_size
            else:
                group.append(row)
                current_size += row_size

        if group:
            content = _render_table_with_header(header_text, group)
            chunks.append(
                self._make_chunk(
                    document_id,
                    page_number,
                    content,
                    ContentType.TABLE,
                    seq,
                )
            )

        return chunks

    # -- generic splitting -------------------------------------------- #
    def _split_text(
        self,
        text: str,
        document_id: int,
        page_number: int,
        content_type: str,
        seq_start: int,
    ) -> list[DocumentChunk]:
        size = settings.chunk_size
        overlap = settings.chunk_overlap
        step = max(1, size - overlap)
        chunks: list[DocumentChunk] = []
        seq = seq_start
        start = 0
        length = len(text)

        while start < length:
            end = min(start + size, length)
            piece = text[start:end].strip()
            if piece:
                chunks.append(
                    self._make_chunk(
                        document_id,
                        page_number,
                        piece,
                        content_type,
                        seq,
                    )
                )
                seq += 1
            if end >= length:
                break
            start += step

        return chunks


def _split_row(line: str) -> list[str]:
    if "|" in line:
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if cells:
            return cells
    # Fall back to splitting on wide whitespace runs.
    parts = re.split(r"\s{2,}", line.strip())
    return [p.strip() for p in parts if p.strip()]


def _render_row(row: list[str]) -> str:
    return " | ".join(cell for cell in row if cell)


def _render_table(header: list[str], body: list[list[str]]) -> str:
    lines = [_render_row(header)]
    lines.extend(_render_row(row) for row in body)
    return "\n".join(lines)


def _render_table_header(header: list[str]) -> str:
    return _render_row(header)


def _render_table_with_header(header_text: str, rows: list[list[str]]) -> str:
    lines = [header_text]
    lines.extend(_render_row(row) for row in rows)
    return "\n".join(lines)
