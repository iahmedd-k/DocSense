from __future__ import annotations

import logging

from app.core.config import settings
from app.schemas.chat import CitationRequest, VerificationRequest
from app.schemas.evidence import EvidenceVerdict
from app.schemas.query_analysis import QueryAnalysis
from app.schemas.rag import RagResponse
from app.schemas.retrieval import ChunkResult
from app.services.chat_service import ChatService
from app.services.corrective_retrieval_service import CorrectiveRetrievalService
from app.services.evidence_grader_service import EvidenceGraderService
from app.services.query_analysis_service import QueryAnalysisService
from app.services.retrieval_service import RetrievalMethod, RetrievalService
from app.services.rrf_service import RRFService

logger = logging.getLogger(__name__)


class RAGService:
    """Composed end-to-end RAG pipeline (Flows 2-5).

    Orchestrates the full reliability chain:

    1. Query analysis (expansion / decomposition when needed)      -- Flow 3
    2. Hybrid retrieval (vector + lexical) with RRF and reranking -- Flow 3
    3. Evidence sufficiency grading                               -- Flow 4
    4. Corrective retrieval when the evidence is insufficient      -- Flow 4
    5. Grounded generation + citation generation                   -- Flow 2
    6. Answer/citation verification                               -- Flow 4
    7. Bounded revision when verification fails                    -- Flow 4
    8. Automatic hard abstention when no reliable evidence exists  -- Flow 5

    ``answer`` returns either a grounded, verified answer with citations, or an
    explicit ``RagResponse`` with ``abstained=True`` -- never an ungrounded
    answer.
    """

    def __init__(
        self,
        query_analysis_service: QueryAnalysisService,
        retrieval_service: RetrievalService,
        rrf_service: RRFService,
        evidence_grader_service: EvidenceGraderService,
        chat_service: ChatService,
        corrective_retrieval_service: CorrectiveRetrievalService | None = None,
        max_revision_attempts: int | None = None,
    ):
        self.query_analysis_service = query_analysis_service
        self.retrieval_service = retrieval_service
        self.rrf_service = rrf_service
        self.evidence_grader_service = evidence_grader_service
        self.chat_service = chat_service
        self.corrective_retrieval_service = corrective_retrieval_service
        self._max_revision_attempts = max_revision_attempts

    @property
    def revision_attempts_limit(self) -> int:
        if self._max_revision_attempts is None:
            return max(0, settings.answer_revision_max_attempts)
        return max(0, self._max_revision_attempts)

    # ------------------------------------------------------------------
    # Public entrypoint
    # ------------------------------------------------------------------

    def answer(
        self,
        user_id: int,
        query: str,
        top_k: int | None = None,
        max_revision_attempts: int | None = None,
    ) -> RagResponse:
        """Run the composed pipeline and return a grounded response or abstention."""
        analysis = self.query_analysis_service.analyze(query)

        evidence = self._retrieve_merged(user_id, query, analysis, top_k)

        verdict = self.evidence_grader_service.grade(query, evidence)

        corrective_queries: list[str] = []
        corrective_attempts = 0
        if not verdict.sufficient and self.corrective_retrieval_service is not None:
            corrective = self.corrective_retrieval_service.search(
                user_id, query, top_k
            )
            evidence = corrective.evidence
            verdict = corrective.verdict
            corrective_queries = corrective.corrective_queries
            corrective_attempts = corrective.attempts_used

        # Flow 5: hard abstention -- never invent an answer without reliable
        # evidence (regardless of whether corrective retrieval was attempted).
        if not verdict.sufficient:
            return self._abstain(
                query=query,
                analysis=analysis,
                evidence=evidence,
                verdict=verdict,
                corrective_queries=corrective_queries,
                corrective_attempts=corrective_attempts,
                reason=(
                    verdict.reason
                    or "Insufficient evidence to answer this question reliably."
                ),
            )

        # Flow 2: grounded generation + citations.
        answer = self.chat_service.generate_answer(query, evidence)

        citations = self._try_generate_citations(query, answer, evidence)

        # Flow 4: verification, then a bounded revision loop.
        verification = self.chat_service.verify_answer(
            VerificationRequest(query=query, answer=answer, evidence=evidence)
        )

        revision_attempts, answer, verification = self._revise_until_verified(
            query=query,
            evidence=evidence,
            answer=answer,
            verification=verification,
            max_revision_attempts=max_revision_attempts,
        )

        if not self._verification_passed(verification):
            logger.info(
                "RAG pipeline for user %s: verification failed after %d "
                "revision attempts; abstaining",
                user_id,
                revision_attempts,
            )
            return self._abstain(
                query=query,
                analysis=analysis,
                evidence=evidence,
                verdict=verdict,
                corrective_queries=corrective_queries,
                corrective_attempts=corrective_attempts,
                revision_attempts=revision_attempts,
                reason=(
                    "The answer could not be verified against the available "
                    "evidence after revision."
                ),
            )

        logger.info(
            "RAG pipeline for user %s: sufficient=%s revision_attempts=%d "
            "corrective_attempts=%d",
            user_id,
            verdict.sufficient,
            revision_attempts,
            corrective_attempts,
        )

        return RagResponse(
            query=query,
            query_analysis=analysis,
            evidence=evidence,
            verdict=verdict,
            answer=answer,
            citations=citations,
            verification=verification,
            abstained=False,
            corrective_queries=corrective_queries,
            corrective_attempts=corrective_attempts,
            revision_attempts=revision_attempts,
        )

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    def _retrieve_merged(
        self,
        user_id: int,
        query: str,
        analysis: QueryAnalysis,
        top_k: int | None,
    ) -> list[ChunkResult]:
        """Run hybrid + rerank retrieval per query and fuse the results.

        When the analysis produced expansion/decomposition variants, each
        variant is retrieved and the ordered lists are merged with RRF so
        evidence is deduplicated and ranked across all queries.
        """
        retrieval_queries = self._retrieval_queries(query, analysis)

        lists: list[list[ChunkResult]] = []
        for q in retrieval_queries:
            response = self.retrieval_service.search(
                user_id=user_id,
                query=q,
                method=RetrievalMethod.HYBRID,
                top_k=top_k,
                rerank=True,
            )
            if response.results:
                lists.append(response.results)

        if not lists:
            return []
        if len(lists) == 1:
            return lists[0]
        return self.rrf_service.fuse(*lists)

    @staticmethod
    def _retrieval_queries(query: str, analysis: QueryAnalysis) -> list[str]:
        queries = [query]
        for extra in analysis.expanded_queries + analysis.sub_queries:
            extra = extra.strip()
            if extra and extra not in queries:
                queries.append(extra)
        return queries

    def _try_generate_citations(self, query: str, answer: str, evidence):
        """Best-effort citation generation.

        Citations are an enrichment, not a correctness gate: when citation
        generation fails the grounded answeris still returned (verification is
        the quality gate). Failures are logged.
        """
        try:
            response = self.chat_service.generate_citations(
                CitationRequest(query=query, answer=answer, evidence=evidence)
            )
            return response.citations
        except Exception as exc:  # noqa: BLE001 - citations must not fail the pipeline
            logger.warning(
                "Citation generation failed for query %r: %s", query, exc
            )
            return []

    def _revise_until_verified(
        self,
        *,
        query: str,
        evidence: list[ChunkResult],
        answer: str,
        verification,
        max_revision_attempts: int | None,
    ) -> tuple[int, object]:
        """Revise the answer until verification passes, up to a bound.

        Returns ``(attempts_used, final_answer, final_verification)`` so the
        caller sees the outcome of the loop rather than the stale pre-revision
        verdict.
        """
        limit = (
            self.revision_attempts_limit
            if max_revision_attempts is None
            else max(0, max_revision_attempts)
        )

        attempts = 0
        while not self._verification_passed(verification) and attempts < limit:
            attempts += 1
            answer = self.chat_service.revise_answer(
                query=query,
                evidence=evidence,
                answer=answer,
                verification=verification,
            )
            verification = self.chat_service.verify_answer(
                VerificationRequest(query=query, answer=answer, evidence=evidence)
            )
        return attempts, answer, verification

    @staticmethod
    def _verification_passed(verification) -> bool:
        return verification.supported and verification.citations_correct

    @staticmethod
    def _abstain(
        *,
        query: str,
        analysis: QueryAnalysis,
        evidence: list[ChunkResult],
        verdict: EvidenceVerdict,
        corrective_queries: list[str],
        corrective_attempts: int,
        reason: str,
        revision_attempts: int = 0,
        answer: str | None = None,
        citations=None,
        verification=None,
        suggestion: str = "",
    ) -> RagResponse:
        """Build an explicit abstention response (Flow 5)."""
        return RagResponse(
            query=query,
            query_analysis=analysis,
            evidence=evidence,
            verdict=verdict,
            answer=answer,
            citations=citations or [],
            verification=verification,
            abstained=True,
            abstention_reason=reason,
            abstention_suggestion=suggestion,
            corrective_queries=corrective_queries,
            corrective_attempts=corrective_attempts,
            revision_attempts=revision_attempts,
        )