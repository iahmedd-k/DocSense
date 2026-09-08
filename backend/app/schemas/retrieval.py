from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Input payload for a hybrid retrieval query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language query to retrieve chunks for",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of top results to return",
    )


class ChunkResult(BaseModel):
    """A single retrieved chunk with provenance and a relevance score.

    The ``score`` semantics are method-specific: for vector retrieval it is
    a cosine similarity in ``[0, 1]``; for full-text retrieval it is the
    PostgreSQL ``ts_rank`` value (higher is more relevant).
    """

    chunk_id: int
    document_id: int
    content: str
    page_number: int
    page_numbers: list[int] = Field(default_factory=list)
    content_type: str
    metadata: dict = Field(default_factory=dict)
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[ChunkResult]
