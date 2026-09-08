import json

import pytest

from app.schemas.evidence import EvidenceVerdict
from app.services.llm_service import LLMError, LLMService
from app.services.query_refinement_service import QueryRefinementService


class FakeChatProvider:
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
        raise AssertionError("no scripted response left")


def _verdict(missing=None):
    return EvidenceVerdict(
        sufficient=False,
        confidence_score=0.3,
        reason="need more",
        missing_information=missing or ["extra details"],
    )


def test_complete_json_parses_fenced_output():
    provider = FakeChatProvider(
        ['```json\n{"query": "refined", "rationale": "why"}\n```']
    )
    service = LLMService(provider=provider)

    data = service.complete_json("system", "user")

    assert data == {"query": "refined", "rationale": "why"}
    assert provider.calls[0]["messages"][0]["role"] == "system"
    assert provider.calls[0]["messages"][1]["content"] == "user"


def test_complete_json_invalid_raises():
    provider = FakeChatProvider(["not json"])
    service = LLMService(provider=provider)

    with pytest.raises(LLMError, match="invalid JSON"):
        service.complete_json("system", "user")


def test_refine_uses_missing_information():
    provider = FakeChatProvider(
        [{"query": "capital expenditure fiscal year", "rationale": "targeted"}]
    )
    refiner = QueryRefinementService(llm_service=LLMService(provider=provider))

    refined = refiner.refine(
        "What is the capital budget?", _verdict(["capital expenditure", "fiscal year"])
    )

    assert refined.query == "capital expenditure fiscal year"
    assert refined.rationale == "targeted"


def test_refine_falls_back_when_llm_returns_empty_query():
    provider = FakeChatProvider([{"query": "", "rationale": "empty"}])
    refiner = QueryRefinementService(llm_service=LLMService(provider=provider))

    refined = refiner.refine("original question", _verdict())

    assert refined.query == "original question"


def test_refine_skips_llm_when_sufficient_or_no_missing_info():
    provider = FakeChatProvider([])
    refiner = QueryRefinementService(llm_service=LLMService(provider=provider))

    sufficient = EvidenceVerdict(
        sufficient=True, reason="enough", missing_information=[]
    )
    assert refiner.refine("q", sufficient).query == "q"

    no_missing = EvidenceVerdict(
        sufficient=False,
        reason="need more",
        missing_information=[],
    )
    assert refiner.refine("q", no_missing).query == "q"

    assert provider.calls == []