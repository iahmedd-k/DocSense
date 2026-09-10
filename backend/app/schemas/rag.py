from pydantic import BaseModel, Field

from app.schemas.chat import SourceCitation, VerificationResponse
from app.schemas.evidence import EvidenceVerdict
from app.schemas.query_analysis import QueryAnalysis
from app.schemas.retrieval import ChunkResult


class RagRequest(BaseModel):
    """Input payload for the composed end-to-end RAG pipeline (Flow 2 - Flow 5)."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The user question to answer",
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=50,
        description="Evidence results to retrieve per query (defaults to server config)",
    )
    max_revision_attempts: int | None = Field(
        default=None,
        ge=0,
        le=5,
        description="Answer revision budget after a failed verification (defaults to server config)",
    )


class RagResponse(BaseModel):
    """Output of the composed RAG pipeline.

    When ``abstained`` is true no answer is returned: reliable evidence could
    not be established and the pipeline returned an explicit abstention instead
    of inventing a response (Flow 5). Otherwise ``answer`` is grounded in
    ``evidence``, carries ``citations``, and has passed ``verification``.
    """

    query: str
    query_analysis: QueryAnalysis
    evidence: list[ChunkResult]
    verdict: EvidenceVerdict
    answer: str | None = None
    citations: list[SourceCitation] = Field(default_factory=list)
    verification: VerificationResponse | None = None
    abstained: bool
    abstention_reason: str | None = None
    abstention_suggestion: str | None = None
    corrective_queries: list[str] = Field(default_factory=list)
    corrective_attempts: int = 0
    revision_attempts: int = 0