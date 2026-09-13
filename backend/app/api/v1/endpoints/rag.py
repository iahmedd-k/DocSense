from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.schemas.rag import ChatResponse, RagRequest, RagResponse
from app.schemas.response import ApiResponse
from app.services.chat_service import ChatService
from app.services.corrective_retrieval_service import CorrectiveRetrievalService
from app.services.embedding_service import EmbeddingService
from app.services.evidence_grader_service import EvidenceGraderService
from app.services.llm_service import LLMService
from app.services.query_analysis_service import QueryAnalysisService
from app.services.query_refinement_service import QueryRefinementService
from app.services.rag_service import RAGService
from app.services.reranking_service import RerankingService
from app.services.retrieval_service import (
    LexicalRetrievalService,
    RetrievalService,
    VectorRetrievalService,
)
from app.services.rrf_service import RRFService

router = APIRouter(prefix="/chat", tags=["chat"])


def get_rag_service(db: Session = Depends(get_db)) -> RAGService:
    chunk_repository = DocumentChunkRepository(db)
    vector_retrieval_service = VectorRetrievalService(
        embedding_service=EmbeddingService(),
        chunk_repository=chunk_repository,
    )
    lexical_retrieval_service = LexicalRetrievalService(
        chunk_repository=chunk_repository,
        language=settings.fulltext_search_language,
    )
    rrf_service = RRFService(
        vector_retrieval_service=vector_retrieval_service,
        lexical_retrieval_service=lexical_retrieval_service,
    )
    retrieval_service = RetrievalService(
        vector_retrieval_service=vector_retrieval_service,
        lexical_retrieval_service=lexical_retrieval_service,
        rrf_service=rrf_service,
        reranking_service=RerankingService(),
    )

    llm_service = LLMService()
    chat_service = ChatService(llm_service=llm_service)
    query_analysis_service = QueryAnalysisService(llm_service=llm_service)
    evidence_grader_service = EvidenceGraderService(llm_service=llm_service)
    query_refinement_service = QueryRefinementService(llm_service=llm_service)
    corrective_retrieval_service = CorrectiveRetrievalService(
        retrieval_service=retrieval_service,
        evidence_grader_service=evidence_grader_service,
        query_refinement_service=query_refinement_service,
    )

    return RAGService(
        query_analysis_service=query_analysis_service,
        retrieval_service=retrieval_service,
        rrf_service=rrf_service,
        evidence_grader_service=evidence_grader_service,
        chat_service=chat_service,
        corrective_retrieval_service=corrective_retrieval_service,
    )


@router.post(
    "/rag",
    response_model=ApiResponse[ChatResponse],
    summary="Run the composed RAG pipeline (question → grounded answer or abstention)",
    description=(
        "End-to-end retrieval-augmented generation: query analysis "
        "(expansion/decomposition) → hybrid retrieval + RRF + reranking → "
        "evidence grading → corrective retrieval → grounded generation → "
        "citation generation → verification → bounded revision. Abstains "
        "explicitly instead of answering when reliable evidence cannot be "
        "established."
    ),
)
def rag_answer(
    request: RagRequest,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    rag_response = rag_service.answer(
        user_id=current_user.id,
        query=request.query,
        top_k=request.top_k,
        max_revision_attempts=request.max_revision_attempts,
    )
    chat_response = ChatResponse.from_rag_response(rag_response)

    if chat_response.abstained:
        message = chat_response.abstention_reason or "Unable to answer based on available documents."
    else:
        message = "Answer generated successfully."

    return ApiResponse(
        success=True,
        data=chat_response,
        message=message,
    )