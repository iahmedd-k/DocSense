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
from app.services.storage_service import StorageError, StorageService

logger = setup_logging()

ALLOWED_PDF_MIME_TYPES = {"application/pdf", "application/octet-stream"}


class DocumentService:

    def __init__(
        self,
        document_repository: DocumentRepository,
        storage_service: StorageService,
        pdf_parser_service: PdfParserService,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
        document_chunk_repository: DocumentChunkRepository,
    ):
        self.document_repository = document_repository
        self.storage_service = storage_service
        self.pdf_parser_service = pdf_parser_service
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.document_chunk_repository = document_chunk_repository

    @staticmethod
    def _max_file_size_bytes() -> int:
        return settings.max_file_size_mb * 1024 * 1024

    @staticmethod
    def _validate_pdf(filename: str, content_type: str | None) -> None:
        safe_name = os.path.basename(filename)
        if not safe_name or not safe_name.lower().endswith(".pdf"):
            raise BadRequestError("Only PDF files are allowed")

        if content_type not in (None, *ALLOWED_PDF_MIME_TYPES):
            raise BadRequestError("Only PDF files are allowed")

    @staticmethod
    def _temp_dir_for_user(user_id: int) -> Path:
        return Path(settings.local_temp_dir) / f"user_{user_id}"

    @staticmethod
    def _temp_path_for_document(document: Document) -> Path:
        file_id = Path(document.storage_key).name
        return DocumentService._temp_dir_for_user(document.user_id) / f"{file_id}.pdf"

    def _save_temp_file(self, file_bytes: bytes, user_id: int) -> tuple[Path, str]:
        file_id = uuid4().hex
        temp_dir = self._temp_dir_for_user(user_id)
        temp_dir.mkdir(parents=True, exist_ok=True)

        file_path = temp_dir / f"{file_id}.pdf"
        file_path.write_bytes(file_bytes)

        public_id = f"docsense/users/{user_id}/{file_id}"

        return file_path, public_id

    @staticmethod
    def _delete_temp_file(file_path: Path) -> None:
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to delete temporary file %s", file_path)

    def _generate_and_persist_chunks(
        self, parsed: "ParsedPdf", document: Document
    ) -> None:
        """Chunk the parsed PDF, generate embeddings, and persist to PostgreSQL."""
        chunks = self.chunking_service.chunk_document(parsed, document.id)

        if not chunks:
            logger.warning("No chunks generated for document %s", document.id)
            return

        texts = [c.content for c in chunks]
        embeddings = self.embedding_service.generate_embeddings(texts)

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

        try:
            parsed = self.pdf_parser_service.parse(str(file_path))
        except PdfParseError as exc:
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
        logger.info("Document %s processed (%d pages)", document.id, parsed.total_pages)

        return document

    def upload(
        self,
        user_id: int,
        filename: str,
        content_type: str | None,
        file_bytes: bytes,
    ) -> Document:

        filename = os.path.basename(filename)
        self._validate_pdf(filename, content_type)

        if not file_bytes:
            raise BadRequestError("File is empty")

        max_size = self._max_file_size_bytes()
        if len(file_bytes) > max_size:
            raise BadRequestError(
                f"File exceeds the maximum size of {settings.max_file_size_mb} MB"
            )

        temp_path, public_id = self._save_temp_file(file_bytes, user_id)

        try:
            storage_key, storage_url = self.storage_service.upload_pdf(
                file_bytes,
                filename,
                user_id,
                public_id=public_id,
            )
        except StorageError as exc:
            self._delete_temp_file(temp_path)
            raise ServiceUnavailableError("File storage is temporarily unavailable") from exc

        document = self.document_repository.create(
            user_id=user_id,
            original_filename=filename,
            storage_key=storage_key,
            storage_url=storage_url,
            mime_type=content_type or "application/pdf",
            file_size=len(file_bytes),
            status=DocumentStatus.UPLOADED,
        )

        return self._process(temp_path, document)

    def process_document(self, user_id: int, document_id: int) -> Document:
        document = self.get_document(user_id, document_id)

        if document.status not in (DocumentStatus.UPLOADED, DocumentStatus.FAILED):
            raise BadRequestError("Document has already been processed")

        temp_path = self._temp_path_for_document(document)
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
