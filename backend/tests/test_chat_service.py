import pytest

from app.schemas.chat import VerificationResponse
from app.schemas.retrieval import ChunkResult
from app.services.chat_service import (
    REVISION_SYSTEM_PROMPT,
    ChatService,
    ServiceUnavailableError,
)
from app.services.llm_service import LLMError, LLMService


def _chunk(chunk_id=1, document_id=10, page=2, content="The budget is 100M."):
    return ChunkResult(
        chunk_id=chunk_id,
        document_id=document_id,
        content=content,
        page_number=page,
        page_numbers=[page],
        content_type="text",
        metadata={},
        score=0.85,
    )


class ScriptedProvider:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.index = 0
        self.calls = []

    def chat(self, messages, temperature=0.0):
        self.calls.append(messages)
        if self.index < len(self.responses):
            response = self.responses[self.index]
            self.index += 1
            return response
        raise AssertionError("no scripted response left")


def test_generate_answer_is_grounded():
    provider = ScriptedProvider(["The budget is 100 million."])
    service = ChatService(llm_service=LLMService(provider=provider))

    answer = service.generate_answer(
        "What is the budget?", [_chunk(1), _chunk(2)], temperature=0.0
    )

    assert answer == "The budget is 100 million."
    system_prompt = provider.calls[0][0]["content"]
    assert "provided evidence chunks" in system_prompt
    assert "(document_id=10" in provider.calls[0][-1]["content"]


def test_generate_answer_raises_service_unavailable_on_llm_error():
    class FailingProvider:
        def chat(self, messages, temperature=0.0):
            raise LLMError("backend down")

    service = ChatService(llm_service=LLMService(provider=FailingProvider()))

    with pytest.raises(ServiceUnavailableError):
        service.generate_answer("Q", [_chunk(1)])


def test_revise_answer_includes_previous_answer_and_issues():
    verification = VerificationResponse(
        supported=False,
        citations_correct=False,
        issues=[],
        explanation="claim not in evidence",
    )
    provider = ScriptedProvider(["Revised grounded answer."])
    service = ChatService(llm_service=LLMService(provider=provider))

    answer = service.revise_answer(
        query="What is the budget?",
        evidence=[_chunk(1)],
        answer="Old ungrounded answer.",
        verification=verification,
    )

    assert answer == "Revised grounded answer."
    user_prompt = provider.calls[0][-1]["content"]
    assert "Old ungrounded answer." in user_prompt
    assert "supported=False" in user_prompt
    assert "claim not in evidence" in user_prompt

    system_prompt = provider.calls[0][0]["content"]
    assert REVISION_SYSTEM_PROMPT == system_prompt


def test_revise_answer_formats_individual_issues():
    from app.schemas.chat import CitationMismatch

    verification = VerificationResponse(
        supported=False,
        citations_correct=False,
        issues=[
            CitationMismatch(
                citation_text="wrong span",
                claimed_document_id=99,
                claimed_page=5,
                issue="does not exist",
            )
        ],
        explanation="",
    )
    provider = ScriptedProvider(["revised"])
    service = ChatService(llm_service=LLMService(provider=provider))

    service.revise_answer("Q", [_chunk(1)], "old", verification)

    user_prompt = provider.calls[0][-1]["content"]
    assert "wrong span" in user_prompt
    assert "claimed document=99" in user_prompt
    assert "page=5" in user_prompt
    assert "does not exist" in user_prompt