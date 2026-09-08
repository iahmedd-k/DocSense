import os

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError, ServiceUnavailableError
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.storage_service import StorageError, StorageService

ALLOWED_PDF_MIME_TYPES = {"application/pdf", "application/octet-stream"}


class DocumentService:

    def __init__(
        self,
        document_repository: DocumentRepository,
        storage_service: StorageService,
    ):
        self.document_repository = document_repository
        self.storage_service = storage_service

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

        try:
            storage_key, _ = self.storage_service.upload_pdf(
                file_bytes,
                filename,
                user_id,
            )
        except StorageError as exc:
            raise ServiceUnavailableError("File storage is temporarily unavailable") from exc

        return self.document_repository.create(
            user_id=user_id,
            filename=filename,
            storage_key=storage_key,
            mime_type=content_type or "application/pdf",
            file_size=len(file_bytes),
            status=DocumentStatus.UPLOADED,
        )

    def get_document(self, user_id: int, document_id: int) -> Document:
        document = self.document_repository.get_by_id_and_user(document_id, user_id)
        if document is None:
            raise NotFoundError("Document not found")

        return document

    def list_documents(self, user_id: int) -> list[Document]:
        return self.document_repository.list_by_user(user_id)