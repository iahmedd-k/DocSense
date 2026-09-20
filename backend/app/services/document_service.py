import os
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError, ServiceUnavailableError
from app.core.logging import setup_logging
from app.models.document import Document, DocumentStatus
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentStatusResponse
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingError, EmbeddingService
from app.services.pdf_parser_service import PdfParseError, PdfParserService
from app.services.spreadsheet_parser_service import SpreadsheetParseError, SpreadsheetParserService
from app.services.ppt_parser_service import PptParseError, PptParserService
from app.services.docx_parser_service import DocxParseError, DocxParserService
from app.services.storage_service import StorageError, StorageService

logger = setup_logging()

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/octet-stream",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}


class DocumentService:

    def __init__(
        self,
        document_repository: DocumentRepository,
        storage_service: StorageService,
        pdf_parser_service: PdfParserService,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
        document_chunk_repository: DocumentChunkRepository,
        spreadsheet_parser_service: SpreadsheetParserService | None = None,
        ppt_parser_service: PptParserService | None = None,
        docx_parser_service: DocxParserService | None = None,
    ):
        self.document_repository = document_repository
        self.storage_service = storage_service
        self.pdf_parser_service = pdf_parser_service
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.document_chunk_repository = document_chunk_repository
        self.spreadsheet_parser_service = spreadsheet_parser_service or SpreadsheetParserService()
        self.ppt_parser_service = ppt_parser_service or PptParserService()
        self.docx_parser_service = docx_parser_service or DocxParserService()

    @staticmethod
    def _max_file_size_bytes() -> int:
        return settings.max_file_size_mb * 1024 * 1024

    @staticmethod
    def _validate_file(filename: str, content_type: str | None) -> str:
        """Validate file type and return the detected extension."""
        safe_name = os.path.basename(filename)
        if not safe_name:
            raise BadRequestError("Invalid filename")

        ext = Path(safe_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(ALLOWED_EXTENSIONS.keys())
            raise BadRequestError(f"Unsupported file type: {ext}. Allowed: {allowed}")

        if content_type and content_type not in ALLOWED_MIME_TYPES:
            # Some browsers send generic MIME types; only reject if clearly wrong
            if content_type not in (None, "application/octet-stream", "binary/octet-stream"):
                logger.warning(
                    "File MIME type %s does not match extension %s, proceeding anyway",
                    content_type,
                    ext,
                )

        return ext

    @staticmethod
    def _temp_dir_for_user(user_id: int) -> Path:
        return Path(settings.local_temp_dir) / f"user_{user_id}"

    @staticmethod
    def _temp_path_for_document(document: Document, ext: str = ".pdf") -> Path:
        file_id = Path(document.storage_key).name
        return DocumentService._temp_dir_for_user(document.user_id) / f"{file_id}{ext}"

    def _save_temp_file(self, file_bytes: bytes, user_id: int, ext: str) -> tuple[Path, str]:
        file_id = uuid4().hex
        temp_dir = self._temp_dir_for_user(user_id)
        temp_dir.mkdir(parents=True, exist_ok=True)

        file_path = temp_dir / f"{file_id}{ext}"
        file_path.write_bytes(file_bytes)

        public_id = f"docsense/users/{user_id}/{file_id}"

        return file_path, public_id

    @staticmethod
    def _delete_temp_file(file_path: Path) -> None:
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to delete temporary file %s", file_path)

    def _detect_extension(self, file_path: Path) -> str:
        """Detect file extension from path."""
        return file_path.suffix.lower()

    def _parse_file(self, file_path: Path, ext: str) -> "ParsedPdf":
        """Route to the correct parser based on file extension."""
        if ext == ".pdf":
            return self.pdf_parser_service.parse(str(file_path))
        elif ext in (".csv", ".xlsx", ".xls"):
            return self.spreadsheet_parser_service.parse(str(file_path))
        elif ext == ".pptx":
            return self.ppt_parser_service.parse(str(file_path))
        elif ext in (".docx", ".doc"):
            return self.docx_parser_service.parse(str(file_path))
        else:
            raise BadRequestError(f"No parser available for file type: {ext}")

    def _generate_and_persist_chunks(
        self, parsed: "ParsedPdf", document: Document
    ) -> None:
        """Chunk the parsed document, generate embeddings, and persist to PostgreSQL."""
        chunks = self.chunking_service.chunk_document(parsed, document.id)

        if not chunks:
            logger.warning("No chunks generated for document %s", document.id)
            raise PdfParseError(f"No readable text or content found in document {document.id}")

        texts = [c.content for c in chunks]
        embeddings = self.embedding_service.generate_embeddings(texts)

        # Keep only chunks whose texts survived the embedding guard
        filtered_texts = [t for t in texts if t.strip()]
        text_set = set(filtered_texts)
        chunks = [c for c in chunks if c.content.strip() in text_set]

        chunk_records = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_records.append({
                "document_id": chunk.document_id,
                "user_id": document.user_id,
                "page_number": chunk.page_number,
                "page_numbers": chunk.page_numbers,
                "content": chunk.content,
                "content_type": chunk.content_type,
                "metadata": chunk.metadata,
                "embedding": embedding,
            })

        self.document_chunk_repository.create_many(chunk_records)
        logger.info(
            "Persisted %d chunks with embeddings for document %s",
            len(chunk_records),
            document.id,
        )

    def _process(self, file_path: Path, document: Document) -> Document:
        document = self.document_repository.update_status(document, DocumentStatus.PROCESSING)

        ext = self._detect_extension(file_path)

        try:
            parsed = self._parse_file(file_path, ext)
        except (PdfParseError, SpreadsheetParseError, PptParseError, DocxParseError) as exc:
            logger.warning("Failed to process document %s: %s", document.id, exc)
            return self.document_repository.update_status(document, DocumentStatus.FAILED)
        except Exception as exc:
            logger.exception("Unexpected error processing document %s", document.id)
            return self.document_repository.update_status(document, DocumentStatus.FAILED)

        try:
            self._generate_and_persist_chunks(parsed, document)
        except EmbeddingError as exc:
            logger.warning(
                "Embedding generation failed for document %s: %s",
                document.id,
                exc,
            )
            return self.document_repository.update_status(document, DocumentStatus.FAILED)
        except Exception as exc:
            logger.exception(
                "Unexpected error persisting chunks for document %s", document.id
            )
            return self.document_repository.update_status(document, DocumentStatus.FAILED)

        document = self.document_repository.update_status(document, DocumentStatus.COMPLETED)
        self._delete_temp_file(file_path)
        logger.info("Document %s processed (%d pages, type=%s)", document.id, parsed.total_pages, ext)

        return document

    def upload_async(
        self,
        user_id: int,
        filename: str,
        content_type: str | None,
        file_bytes: bytes,
    ) -> tuple[Document, Path]:
        """Save file, upload to storage, create document record with PROCESSING status, and return (document, temp_path)."""
        filename = os.path.basename(filename)
        ext = self._validate_file(filename, content_type)

        if not file_bytes:
            raise BadRequestError("File is empty")

        max_size = self._max_file_size_bytes()
        if len(file_bytes) > max_size:
            raise BadRequestError(
                f"File exceeds the maximum size of {settings.max_file_size_mb} MB"
            )

        temp_path, public_id = self._save_temp_file(file_bytes, user_id, ext)

        try:
            storage_key, storage_url = self.storage_service.upload_file(
                file_bytes,
                filename,
                user_id,
                public_id=public_id,
            )
        except StorageError as exc:
            self._delete_temp_file(temp_path)
            raise ServiceUnavailableError(
                f"File storage is temporarily unavailable: {exc}"
            ) from exc

        # Determine MIME type from extension
        mime_type = ALLOWED_EXTENSIONS.get(ext, content_type or "application/octet-stream")

        document = self.document_repository.create(
            user_id=user_id,
            original_filename=filename,
            storage_key=storage_key,
            storage_url=storage_url,
            mime_type=mime_type,
            file_size=len(file_bytes),
            status=DocumentStatus.PROCESSING,
        )

        return document, temp_path

    def process_document_background(self, document_id: int, temp_path_str: str) -> None:
        """Process document in background with its own DB session."""
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            doc_repo = DocumentRepository(db)
            chunk_repo = DocumentChunkRepository(db)
            document = doc_repo.get_by_id(document_id)
            if not document:
                logger.error("Background processing: document %d not found", document_id)
                return

            self.document_repository = doc_repo
            self.document_chunk_repository = chunk_repo
            temp_path = Path(temp_path_str)
            self._process(temp_path, document)
        except Exception:
            logger.exception("Error in background document processing for %d", document_id)
        finally:
            db.close()

    def upload(
        self,
        user_id: int,
        filename: str,
        content_type: str | None,
        file_bytes: bytes,
    ) -> Document:
        document, temp_path = self.upload_async(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )
        return self._process(temp_path, document)

    def process_document(self, user_id: int, document_id: int) -> Document:
        document = self.get_document(user_id, document_id)

        if document.status not in (DocumentStatus.UPLOADED, DocumentStatus.FAILED):
            raise BadRequestError("Document has already been processed")

        # Detect extension from original filename
        ext = Path(document.original_filename).suffix.lower() if document.original_filename else ".pdf"
        temp_path = self._temp_path_for_document(document, ext=ext)
        if not temp_path.is_file():
            self.document_repository.update_status(document, DocumentStatus.FAILED)
            raise BadRequestError(
                "Temporary file is missing, please re-upload the document"
            )

        return self._process(temp_path, document)

    def get_document(self, user_id: int, document_id: int) -> Document:
        document = self.document_repository.get_by_id_and_user(document_id, user_id)
        if document is None:
            raise NotFoundError("Document not found")

        return document

    def get_document_status(
        self,
        user_id: int,
        document_id: int,
    ) -> DocumentStatusResponse:
        document = self.get_document(user_id, document_id)

        return DocumentStatusResponse(
            document_id=document.id,
            status=document.status,
        )

    def list_documents(self, user_id: int) -> list[Document]:
        return self.document_repository.list_by_user(user_id)

    def delete_document(self, user_id: int, document_id: int) -> Document:
        """Delete a document owned by ``user_id`` and its associated data.

        Deletes the stored file, all associated chunks, and finally the
        document record. Ownership is enforced at the repository layer so a
        user cannot delete another user's document.
        """
        document = self.get_document(user_id, document_id)

        self.document_chunk_repository.delete_by_document(document.id)

        storage_key = document.storage_key
        if storage_key:
            try:
                self.storage_service.delete_file(storage_key)
            except StorageError:
                logger.warning(
                    "Failed to delete stored file for document %s", document.id
                )

        deleted = self.document_repository.delete_by_id_and_user(
            document.id,
            user_id,
        )
        if deleted is None:
            raise NotFoundError("Document not found")

        return deleted
