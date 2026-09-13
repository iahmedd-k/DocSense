from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.schemas.chat import (
    AbstentionRequest,
    AbstentionResponse,
    CitationRequest,
    CitationResponse,
    StreamChatRequest,
    VerificationRequest,
    VerificationResponse,
    WebSearchRequest,
    WebSearchResponse,
)
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


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    return ChatService(llm_service=LLMService())


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
    "",
    response_model=ApiResponse[ChatResponse],
    summary="Ask a document-grounded question",
    description=(
        "End-to-end retrieval-augmented generation: query analysis "
        "→ hybrid retrieval → evidence grading → grounded generation → "
        "citation → verification → bounded revision or abstention."
    ),
)
def chat(
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


@router.post(
    "/citations",
    response_model=ApiResponse[CitationResponse],
    summary="Generate page/source citations for the grounded answer",
)
def generate_citations(
    request: CitationRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    result = chat_service.generate_citations(request)
    return ApiResponse(success=True, data=result, message="Citations generated.")


@router.post(
    "/verify",
    response_model=ApiResponse[VerificationResponse],
    summary="Verify the answer and its citations against evidence",
)
def verify_answer(
    request: VerificationRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    result = chat_service.verify_answer(request)
    return ApiResponse(success=True, data=result, message="Verification complete.")


@router.post(
    "/abstain",
    response_model=ApiResponse[AbstentionResponse],
    summary="Return an explicit abstention response",
)
def abstain(
    request: AbstentionRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    result = chat_service.decide_abstention(request)
    return ApiResponse(success=True, data=result, message="Abstention decision made.")


@router.post(
    "/stream",
    response_class=StreamingResponse,
    summary="Stream the grounded LLM response",
)
def stream_chat(
    request: StreamChatRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    generator = chat_service.stream_answer(
        query=request.query,
        evidence=request.evidence,
        temperature=request.temperature,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/web-search",
    response_model=ApiResponse[WebSearchResponse],
    summary="Perform optional external web search",
)
def web_search(
    request: WebSearchRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    result = chat_service.web_search(request)
    return ApiResponse(success=True, data=result, message="Web search completed.")
