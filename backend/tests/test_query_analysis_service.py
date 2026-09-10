import json

from app.services.llm_service import LLMError, LLMService
from app.services.query_analysis_service import QueryAnalysisService


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


def _no_enrichment():
    return {
        "needs_expansion": False,
        "expanded_queries": [],
        "needs_decomposition": False,
        "sub_queries": [],
        "rationale": "single query is enough",
    }


def test_analyze_no_enrichment_returns_original_only():
    provider = FakeChatProvider([_no_enrichment()])
    service = QueryAnalysisService(llm_service=LLMService(provider=provider))

    analysis = service.analyze("What is the budget for 2026?")

    assert analysis.original_query == "What is the budget for 2026?"
    assert analysis.expanded_queries == []
    assert analysis.sub_queries == []
    assert analysis.rationale == "single query is enough"


def test_analyze_expansion_returns_variants():
    provider = FakeChatProvider(
        [
            {
                "needs_expansion": True,
                "expanded_queries": [
                    "budget 2026 figures",
                    "2026 spending totals",
                ],
                "needs_decomposition": False,
                "sub_queries": [],
                "rationale": "multiple keywords",
            }
        ]
    )
    service = QueryAnalysisService(llm_service=LLMService(provider=provider))

    analysis = service.analyze("What is the budget for 2026?")

    assert analysis.expanded_queries == [
        "budget 2026 figures",
        "2026 spending totals",
    ]
    assert analysis.sub_queries == []


def test_analyze_decomposition_returns_sub_queries():
    provider = FakeChatProvider(
        [
            {
                "needs_expansion": False,
                "expanded_queries": [],
                "needs_decomposition": True,
                "sub_queries": ["revenue growth", "operating margins"],
                "rationale": "two distinct facts",
            }
        ]
    )
    service = QueryAnalysisService(llm_service=LLMService(provider=provider))

    analysis = service.analyze("How did revenue and margins change?")

    assert analysis.sub_queries == ["revenue growth", "operating margins"]
    assert analysis.expanded_queries == []


def test_analyze_combines_expansion_and_decomposition():
    provider = FakeChatProvider(
        [
            {
                "needs_expansion": True,
                "expanded_queries": ["R&D spending"],
                "needs_decomposition": True,
                "sub_queries": ["headcount changes", "capex plan"],
                "rationale": "complex",
            }
        ]
    )
    service = QueryAnalysisService(llm_service=LLMService(provider=provider))

    analysis = service.analyze("Describe R&D and headcount changes last year")

    assert analysis.expanded_queries == ["R&D spending"]
    assert analysis.sub_queries == ["headcount changes", "capex plan"]


def test_analyze_deduplicates_and_caps_lists(monkeypatch):
    monkeypatch.setattr(
        "app.services.query_analysis_service.settings.query_analysis_max_expansion", 2
    )
    provider = FakeChatProvider(
        [
            {
                "needs_expansion": True,
                "expanded_queries": ["same", "same", "one", "two", "three"],
                "needs_decomposition": False,
                "sub_queries": [],
                "rationale": "capped and deduped",
            }
        ]
    )
    service = QueryAnalysisService(llm_service=LLMService(provider=provider))

    analysis = service.analyze("question")

    assert analysis.expanded_queries == ["same", "one"]
    assert analysis.sub_queries == []


def test_analyze_ignores_queries_when_flag_false_but_list_present():
    provider = FakeChatProvider(
        [
            {
                "needs_expansion": False,
                "expanded_queries": ["stale variant"],
                "needs_decomposition": True,
                "sub_queries": ["sub one"],
                "rationale": "flags rule",
            }
        ]
    )
    service = QueryAnalysisService(llm_service=LLMService(provider=provider))

    analysis = service.analyze("question")

    assert analysis.expanded_queries == []
    assert analysis.sub_queries == ["sub one"]


def test_analyze_falls_back_on_llm_error():
    class FailingProvider:
        def chat(self, messages, temperature=0.0):
            raise LLMError("backend down")

    service = QueryAnalysisService(llm_service=LLMService(provider=FailingProvider()))

    analysis = service.analyze("question")

    assert analysis.expanded_queries == []
    assert analysis.sub_queries == []
    assert analysis.rationale  # informative fallback reason