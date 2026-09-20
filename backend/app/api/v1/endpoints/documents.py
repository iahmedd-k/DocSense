from fastapi import APIRouter, BackgroundTasks, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.schemas.response import ApiResponse
from app.services.chunking_service import ChunkingService
from app.services.docx_parser_service import DocxParserService
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.pdf_parser_service import PdfParserService
from app.services.ppt_parser_service import PptParserService
from app.services.spreadsheet_parser_service import SpreadsheetParserService
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
        spreadsheet_parser_service=SpreadsheetParserService(),
        ppt_parser_service=PptParserService(),
        docx_parser_service=DocxParserService(),
    )


@router.post(
    "",
    response_model=ApiResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document (PDF, CSV, Excel, PPTX, DOCX)",
)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    file_bytes = file.file.read()
    document, temp_path = document_service.upload_async(
        user_id=current_user.id,
        filename=file.filename or "",
        content_type=file.content_type,
        file_bytes=file_bytes,
    )
    background_tasks.add_task(
        document_service.process_document_background,
        document.id,
        str(temp_path),
    )
    return ApiResponse(
        success=True,
        data=document,
        message="Document uploaded successfully. Processing started in background.",
    )


@router.get(
    "",
    response_model=ApiResponse[list[DocumentResponse]],
    summary="List the authenticated user's documents",
)
def list_documents(
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    results = document_service.list_documents(current_user.id)
    return ApiResponse(
        success=True,
        data=results,
        message=f"Found {len(results)} document(s).",
    )


@router.get(
    "/{document_id}/status",
    response_model=ApiResponse[DocumentStatusResponse],
    summary="Get a document's processing status",
)
def get_document_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    result = document_service.get_document_status(current_user.id, document_id)
    return ApiResponse(success=True, data=result, message="Document status retrieved.")


@router.get(
    "/{document_id}",
    response_model=ApiResponse[DocumentResponse],
    summary="Get one of the authenticated user's documents",
)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    result = document_service.get_document(current_user.id, document_id)
    return ApiResponse(success=True, data=result, message="Document retrieved.")


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its associated stored data",
)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    document_service.delete_document(current_user.id, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)