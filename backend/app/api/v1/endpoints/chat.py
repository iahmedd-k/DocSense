from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
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
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    return ChatService(llm_service=LLMService())


@router.post(
    "/citations",
    response_model=CitationResponse,
    summary="Generate page/source citations for the grounded answer (FR-018)",
)
def generate_citations(
    request: CitationRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return chat_service.generate_citations(request)


@router.post(
    "/verify",
    response_model=VerificationResponse,
    summary="Verify the answer and its citations against evidence (FR-019)",
)
def verify_answer(
    request: VerificationRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return chat_service.verify_answer(request)


@router.post(
    "/abstain",
    response_model=AbstentionResponse,
    summary="Return an explicit abstention response (FR-020)",
)
def abstain(
    request: AbstentionRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return chat_service.decide_abstention(request)


@router.post(
    "/stream",
    response_class=StreamingResponse,
    summary="Stream the grounded LLM response (FR-021)",
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
    response_model=WebSearchResponse,
    summary="Perform optional external web search (FR-023)",
)
def web_search(
    request: WebSearchRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return chat_service.web_search(request)
