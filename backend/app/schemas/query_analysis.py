from pydantic import BaseModel, Field


class QueryAnalysis(BaseModel):
    """Result of the query analysis step (Flow 3).

    ``expanded_queries`` are paraphrased retrieval variants that each target
    complementary evidence for the same intent, while ``sub_queries`` are
    independent decompositions of a multi-part question. When neither is
    needed both lists are empty and the original query alone is used.
    """

    original_query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The original user question",
    )
    expanded_queries: list[str] = Field(
        default_factory=list,
        description="Paraphrased retrieval variants when expansion is useful",
    )
    sub_queries: list[str] = Field(
        default_factory=list,
        description="Independent sub-questions when the query is multi-part",
    )
    rationale: str = Field(
        default="",
        description="Brief rationale for the analysis decisions",
    )