from app.schemas.chat import (
    CitationResponse,
    SourceCitation,
    VerificationResponse,
)
from app.schemas.evidence import EvidenceVerdict
from app.schemas.query_analysis import QueryAnalysis
from app.schemas.retrieval import ChunkResult, SearchResponse
from app.services.rag_service import RAGService


def _chunk(chunk_id=1, document_id=10, page=2, content="The budget is 100M."):
    return ChunkResult(
        chunk_id=chunk_id,
        document_id=document_id,
        content=content,
        page_number=page,
        page_numbers=[page],
        content_type="text/markdown",
        metadata={},
        score=0.85,
    )


def _verdict(sufficient, reason="ok"):
    return EvidenceVerdict(
        sufficient=sufficient,
        confidence_score=0.9 if sufficient else 0.2,
        reason=reason,
        missing_information=[] if sufficient else ["budget figures"],
    )


class ScriptedAnalysis:
    def __init__(self, expanded=(), sub=()):
        self.expanded = list(expanded)
        self.sub = list(sub)

    def analyze(self, query):
        return QueryAnalysis(
            original_query=query,
            expanded_queries=self.expanded,
            sub_queries=self.sub,
            rationale="scripted",
        )


class ScriptedRetrieval:
    def __init__(self, per_query=None):
        self.per_query = per_query or {}
        self.calls = []

    def search(self, user_id, query, method, top_k=None, rerank=True):
        self.calls.append(
            {"user_id": user_id, "query": query, "method": method}
        )
        results = self.per_query.get(query, [_chunk()])
        return SearchResponse(query=query, results=results)


class ScriptedRRF:
    def __init__(self):
        self.fuse_calls = 0

    def fuse(self, *lists):
        self.fuse_calls += 1
        return lists[0]


class ScriptedGrader:
    def __init__(self, verdict):
        self.verdict = verdict
        self.calls = []

    def grade(self, query, evidence):
        self.calls.append((query, evidence))
        if isinstance(self.verdict, list):
            return self.verdict[len(self.calls) - 1]
        return self.verdict


class ScriptedChat:
    def __init__(
        self,
        answers=("final answer",),
        citation=CitationResponse(
            query="q",
            answer="final answer",
            citations=[
                SourceCitation(
                    text="The budget is 100M.",
                    document_id=10,
                    page_number=2,
                    chunk_id=1,
                    confidence=0.9,
                )
            ],
        ),
        verifications=None,
        revisions=(),
    ):
        self.answers = list(answers)
        self.citation = citation
        self.verifications = list(verifications or [])
        self.revisions = list(revisions)
        self.generate_calls = 0
        self.revise_calls = 0
        self.verify_calls = 0
        self.verify_requests = []

    def generate_answer(self, query, evidence, temperature=0.0):
        self.generate_calls += 1
        return self.answers[min(self.generate_calls - 1, len(self.answers) - 1)]

    def generate_citations(self, request):
        return self.citation

    def verify_answer(self, request):
        self.verify_calls += 1
        self.verify_requests.append(request)
        idx = min(self.verify_calls - 1, len(self.verifications) - 1)
        if self.verifications:
            return self.verifications[idx]
        return VerificationResponse(
            supported=True, citations_correct=True, explanation="default ok"
        )

    def revise_answer(self, query, evidence, answer, verification, temperature=0.0):
        self.revise_calls += 1
        return self.revisions[min(self.revise_calls - 1, len(self.revisions) - 1)]


class NoCorrective:
    pass


def _make_service(
    *,
    analysis=None,
    retrieval_query_map=None,
    verdicts=(),
    chat_kwargs=None,
    corrective=None,
):
    analysis = analysis or ScriptedAnalysis()
    retrieval = ScriptedRetrieval(per_query=retrieval_query_map)
    rrf = ScriptedRRF()
    grader = ScriptedGrader(
        list(verdicts) if len(verdicts) > 1 else (verdicts[0] if verdicts else None)
    )
    chat = ScriptedChat(**(chat_kwargs or {}))
    service = RAGService(
        query_analysis_service=analysis,
        retrieval_service=retrieval,
        rrf_service=rrf,
        evidence_grader_service=grader,
        chat_service=chat,
        corrective_retrieval_service=corrective,
    )
    return service, retrieval, grader, chat, rrf


def test_sufficient_evidence_returns_grounded_answer():
    service, retrieval, grader, chat, _ = _make_service(
        verdicts=(_verdict(True),)
    )

    resp = service.answer(user_id=1, query="What is the budget?")

    assert resp.abstained is False
    assert resp.answer == "final answer"
    assert len(resp.citations) == 1
    assert resp.verification is not None
    assert resp.verification.supported is True
    assert resp.revision_attempts == 0


def test_insufficient_evidence_abstains_without_corrective():
    service, _, _, _, _ = _make_service(verdicts=(_verdict(False),))

    resp = service.answer(user_id=1, query="What is the budget?")

    assert resp.abstained is True
    assert resp.answer is None
    assert resp.abstention_reason


def test_insufficient_evidence_resolved_by_corrective_returns_answer():
    verdicts = [_verdict(False), _verdict(True)]
    corrective = type(
        "Corrective",
        (),
        {
            "search": lambda self, user_id, query, top_k=None: type(
                "CorrectiveResult",
                (),
                {
                    "evidence": [_chunk(2)],
                    "verdict": verdicts[1],
                    "corrective_queries": ["budget totals"],
                    "attempts_used": 1,
                },
            )()
        },
    )()
    service, _, grader, chat, _ = _make_service(
        verdicts=verdicts, corrective=corrective
    )

    resp = service.answer(user_id=1, query="What is the budget?")

    assert resp.abstained is False
    assert resp.answer == "final answer"
    assert resp.corrective_attempts == 1
    assert resp.corrective_queries == ["budget totals"]


def test_corrective_still_insufficient_abstains_with_metadata():
    verdicts = [_verdict(False), _verdict(False)]
    corrective = type(
        "Corrective",
        (),
        {
            "search": lambda self, user_id, query, top_k=None: type(
                "CorrectiveResult",
                (),
                {
                    "evidence": [_chunk(2)],
                    "verdict": verdicts[1],
                    "corrective_queries": ["budget totals"],
                    "attempts_used": 2,
                },
            )()
        },
    )()
    service, _, _, _, _ = _make_service(verdicts=verdicts, corrective=corrective)

    resp = service.answer(user_id=1, query="What is the budget?")

    assert resp.abstained is True
    assert resp.corrective_attempts == 2
    assert resp.corrective_queries == ["budget totals"]


def test_revision_fixes_verification_failure():
    passed = VerificationResponse(
        supported=True, citations_correct=True, explanation="ok"
    )
    failed = VerificationResponse(
        supported=False, citations_correct=True, explanation="unsupported claim"
    )
    service, _, _, _, _ = _make_service(
        verdicts=(_verdict(True),),
        chat_kwargs={
            "verifications": [failed, passed],
            "answers": ("v1 answer",),
            "revisions": ("revised answer",),
        },
    )

    resp = service.answer(user_id=1, query="What is the budget?")

    assert resp.abstained is False
    assert resp.answer == "revised answer"
    assert resp.revision_attempts == 1
    assert resp.verification.supported is True
    assert service.chat_service.revise_calls == 1


def test_revision_exhausted_abstains():
    failed = VerificationResponse(
        supported=False, citations_correct=False, explanation="still bad"
    )
    service, _, _, _, _ = _make_service(
        verdicts=(_verdict(True),),
        chat_kwargs={
            "verifications": [failed, failed],
            "answers": ("v1 answer",),
            "revisions": ("revised answer",),
        },
    )

    resp = service.answer(user_id=1, query="What is the budget?")

    assert resp.abstained is True
    assert resp.revision_attempts == 1
    assert resp.answer is None


def test_expansion_runs_multiple_retrieval_queries_and_fuses():
    ch1 = _chunk(1)
    ch2 = _chunk(2)
    service, retrieval, _, _, rrf = _make_service(
        analysis=ScriptedAnalysis(expanded=("budget figures 2026",)),
        retrieval_query_map={
            "What is the budget?": [ch1],
            "budget figures 2026": [ch2],
        },
        verdicts=(_verdict(True),),
    )

    resp = service.answer(user_id=1, query="What is the budget?")

    assert {c["query"] for c in retrieval.calls} == {
        "What is the budget?",
        "budget figures 2026",
    }
    assert rrf.fuse_calls == 1
    assert resp.evidence == [ch1]


def test_empty_evidence_abstains():
    service, _, grader, _, _ = _make_service(
        retrieval_query_map={"q": []}, verdicts=(_verdict(False),)
    )
    resp = service._retrieve_merged(1, "q", QueryAnalysis(original_query="q"), None)
    assert resp == []
    resp2 = service.answer(user_id=1, query="q")
    assert resp2.abstained is True


def test_citation_failure_is_non_fatal():
    class FailingChat(ScriptedChat):
        def generate_citations(self, request):
            raise RuntimeError("citation provider down")

    service, _, _, _, _ = _make_service(verdicts=(_verdict(True),))
    service.chat_service = FailingChat()

    resp = service.answer(user_id=1, query="What is the budget?")

    assert resp.abstained is False
    assert resp.answer == "final answer"
    assert resp.citations == []


def test_revision_attempts_limit_from_config():
    from app.services.rag_service import settings

    assert service_revision_limit_default() == settings.answer_revision_max_attempts


def service_revision_limit_default():
    from app.services.rag_service import RAGService

    return RAGService(
        query_analysis_service=None,
        retrieval_service=None,
        rrf_service=None,
        evidence_grader_service=None,
        chat_service=None,
    ).revision_attempts_limit