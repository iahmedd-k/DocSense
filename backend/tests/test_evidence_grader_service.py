import json

import pytest

from app.schemas.retrieval import ChunkResult
from app.services.evidence_grader_service import (
    EvidenceGraderError,
    EvidenceGraderService,
)
from app.services.llm_service import LLMService


def _chunk(chunk_id, content="budget totals are 42.3 million", page=3):
    return ChunkResult(
        chunk_id=chunk_id,
        document_id=chunk_id + 100,
        content=content,
        page_number=page,
        page_numbers=[page, page + 1],
        content_type="text",
        metadata={"source": "pdf", "page": page},
        score=0.85,
    )


class FakeChatProvider:
    """Scripted chat provider returning pre-built JSON responses."""

    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.index = 0
        self.calls = []

    def chat(self, messages, temperature=0.0):
        self.calls.append({"messages": messages, "temperature": temperature})
        if self.index < len(self.responses):
            response = self.responses[self.index]
            self.index += 1
            return response if isinstance(response, str) else json.dumps(response)
        return json.dumps(
            {
                "sufficient": False,
                "confidence_score": 0.2,
                "reason": "not enough evidence",
                "missing_information": ["details"],
            }
        )


@pytest.fixture()
def grader():
    return EvidenceGraderService(llm_service=LLMService(provider=FakeChatProvider()))


def test_sufficient_evidence(grader):
    grader.llm_service.provider.responses = [
        {
            "sufficient": True,
            "confidence_score": 0.94,
            "reason": "Evidence directly answers the budget question.",
            "missing_information": [],
        }
    ]

    verdict = grader.grade("What is the budget?", [_chunk(1), _chunk(2)])

    assert verdict.sufficient is True
    assert verdict.confidence_score == pytest.approx(0.94)
    assert verdict.reason == "Evidence directly answers the budget question."
    assert verdict.missing_information == []


def test_insufficient_evidence(grader):
    grader.llm_service.provider.responses = [
        {
            "sufficient": False,
            "confidence_score": 0.35,
            "reason": "Only marketing figures were retrieved.",
            "missing_information": ["capital expenditure budget", "fiscal year"],
        }
    ]

    verdict = grader.grade("What is the capital budget?", [_chunk(1)])

    assert verdict.sufficient is False
    assert verdict.confidence_score == pytest.approx(0.35)
    assert verdict.missing_information == [
        "capital expenditure budget",
        "fiscal year",
    ]


def test_no_chunks_is_insufficient_without_llm():
    provider = FakeChatProvider()
    service = EvidenceGraderService(llm_service=LLMService(provider=provider))

    verdict = service.grade("What is the budget?", [])

    assert verdict.sufficient is False
    assert verdict.missing_information
    assert provider.calls == []


def test_marks_sufficient_from_fenced_json():
    provider = FakeChatProvider(
        [
            '```json\n{"sufficient": true, "confidence_score": 0.9, '
            '"reason": "ok", "missing_information": []}\n```'
        ]
    )
    service = EvidenceGraderService(llm_service=LLMService(provider=provider))

    verdict = service.grade("Question?", [_chunk(1)])

    assert verdict.sufficient is True


def test_passes_only_top_evidence_window(monkeypatch):
    monkeypatch.setattr(
        "app.services.evidence_grader_service.settings.evidence_grading_top_k", 2
    )
    provider = FakeChatProvider()
    service = EvidenceGraderService(llm_service=LLMService(provider=provider))

    service.grade("Q", [_chunk(i) for i in range(1, 5)])

    messages = provider.calls[0]["messages"]
    user_prompt = messages[-1]["content"]
    assert "[3] document_id=103" not in user_prompt
    assert "[1] document_id=101" in user_prompt
    assert "[2] document_id=102" in user_prompt


def test_malformed_llm_output_raises():
    provider = FakeChatProvider(["not json at all"])
    service = EvidenceGraderService(llm_service=LLMService(provider=provider))

    with pytest.raises(EvidenceGraderError):
        service.grade("Q", [_chunk(1)])