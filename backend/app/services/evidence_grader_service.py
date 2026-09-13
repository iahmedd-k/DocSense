from __future__ import annotations

import logging
import time

from app.core.config import settings
from app.schemas.evidence import EvidenceVerdict
from app.schemas.retrieval import ChunkResult
from app.services.llm_service import LLMError, LLMService

logger = logging.getLogger(__name__)

GRADER_SYSTEM_PROMPT = """\
You are an evidence sufficiency grader for a document question-answering \
system. Given a user question and a set of retrieved evidence chunks, decide \
whether those chunks are sufficient to answer the question.

Evaluate whether the evidence:
- is relevant to the question,
- contains enough information to answer it,
- supports the expected answer, and
- is missing any important information.

Respond with STRICT JSON only and no extra text, using this exact shape:
{
  "sufficient": <true or false>,
  "confidence_score": <float 0.0 to 1.0>,
  "reason": <brief string>,
  "missing_information": <list of strings; empty when sufficient>
}

Rules:
- "sufficient" must be true ONLY when the evidence can fully answer the question.
- When insufficient, "missing_information" must list the specific information that is absent.
- "confidence_score" reflects how confident you are in the relevance and completeness of the evidence.
"""


class EvidenceGraderError(Exception):
    """Raised when an evidence verdict cannot be produced from LLM output."""


class EvidenceGraderService:
    """Grades whether retrieved evidence is sufficient to answer a question.

    The grading decision is produced independently of answer generation; a
    downstream feature (e.g. FR-020) decides what to do with the verdict.
    When no evidence is retrieved the verdict is insufficient without making
    an LLM call.
    """

    def __init__(
        self,
        llm_service: LLMService | None = None,
    ):
        self._llm_service = llm_service

    @property
    def llm_service(self) -> LLMService:
        if self._llm_service is None:
            self._llm_service = LLMService()
        return self._llm_service

    @property
    def evidence_window(self) -> int:
        return settings.evidence_grading_top_k

    def grade(
        self,
        query: str,
        chunks: list[ChunkResult],
    ) -> EvidenceVerdict:
        """Return a sufficiency verdict for ``chunks`` against ``query``.

        Only the top ``evidence_window`` chunks are presented to the grader.
        Raises LLMError on an LLM failure.
        """
        window = chunks[: self.evidence_window]
        if not window:
            return EvidenceVerdict(
                sufficient=False,
                confidence_score=0.0,
                reason="No evidence chunks were retrieved.",
                missing_information=[
                    "No evidence was found for the question."
                ],
            )

        user_prompt = self._build_prompt(query, window)
        try:
            t0 = time.perf_counter()
            data = self.llm_service.complete_json(GRADER_SYSTEM_PROMPT, user_prompt)
            logger.info("LLM evidence_grading: %.3fs", time.perf_counter() - t0)
        except LLMError as exc:
            raise EvidenceGraderError(
                f"Evidence grader LLM call failed: {exc}"
            ) from exc

        try:
            return self._parse_verdict(data)
        except (TypeError, ValueError) as exc:
            raise EvidenceGraderError(
                f"Evidence grader produced a malformed verdict: {exc}"
            ) from exc

    def _build_prompt(self, query: str, chunks: list[ChunkResult]) -> str:
        lines = [f"Question: {query}", "", "Retrieved evidence:"]
        for index, chunk in enumerate(chunks, start=1):
            lines.append(
                f"[{index}] document_id={chunk.document_id}, "
                f"page={chunk.page_number}: {chunk.content}"
            )
        return "\n".join(lines)

    @staticmethod
    def _parse_verdict(data) -> EvidenceVerdict:
        if not isinstance(data, dict):
            raise ValueError(f"expected a JSON object, got {type(data).__name__}")

        sufficient = _coerce_bool(data.get("sufficient"))
        reason = str(data.get("reason") or "No reason provided")

        raw_missing = data.get("missing_information") or []
        if isinstance(raw_missing, list):
            missing = [str(item) for item in raw_missing]
        else:
            missing = [str(raw_missing)]

        raw_confidence = data.get("confidence_score")
        confidence = float(raw_confidence) if raw_confidence is not None else None

        return EvidenceVerdict(
            sufficient=sufficient,
            confidence_score=confidence,
            reason=reason,
            missing_information=missing,
        )


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
        raise ValueError(f"cannot coerce {value!r} to bool")
    raise ValueError(f"cannot coerce {type(value).__name__} to bool")