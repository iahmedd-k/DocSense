from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.services.chunking_service import ChunkingService
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.pdf_parser_service import PdfParserService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(
        document_repository=DocumentRepository(db),
        storage_service=StorageService(),
        pdf_parser_service=PdfParserService(),
        chunking_service=ChunkingService(),
        embedding_service=EmbeddingService(),
        document_chunk_repository=DocumentChunkRepository(db),
    )


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF document",
)
def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    file_bytes = file.file.read()
    return document_service.upload(
        user_id=current_user.id,
        filename=file.filename or "",
        content_type=file.content_type,
        file_bytes=file_bytes,
    )


@router.get(
    "",
    response_model=list[DocumentResponse],
    summary="List the authenticated user's documents",
)
def list_documents(
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    return document_service.list_documents(current_user.id)


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="Get a document's processing status",
)
def get_document_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    return document_service.get_document_status(current_user.id, document_id)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get one of the authenticated user's documents",
)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    return document_service.get_document(current_user.id, document_id)