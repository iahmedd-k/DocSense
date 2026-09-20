from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "DocSense Backend"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    api_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+psycopg://docsense:adminadmin@localhost:5432/docsense"
    )

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    cors_origins: str | list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://docsense-one.vercel.app",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str] | None) -> list[str]:
        default_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://docsense-one.vercel.app",
        ]
        if not v:
            return default_origins
        if isinstance(v, str):
            v_str = v.strip()
            if not v_str:
                return default_origins
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(i).strip() for i in parsed if str(i).strip()]
                except Exception:
                    pass
            return [i.strip() for i in v_str.split(",") if i.strip()]
        if isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return default_origins

    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    max_file_size_mb: int = 10

    supabase_url: str = ""
    supabase_secret_key: str = ""
    supabase_bucket: str = "documents"

    local_temp_dir: str = "./tmp"

    chunk_size: int = 400  # token count (not characters)
    chunk_overlap: int = 50  # token count

    # Retrieval
    retrieval_default_top_k: int = 10
    retrieval_max_top_k: int = 50
    fulltext_search_language: str = "english"

    # Reciprocal Rank Fusion (FR-012)
    rrf_k: int = 60

    # Cross-Encoder Reranking (FR-014)
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_max_results: int = 20
    reranker_candidate_multiplier: int = 2
    min_rerank_score: float = 0.1

    # Evidence Sufficiency Grading (FR-015) — adaptive per query intent
    evidence_grading_top_k: int = 12  # default fallback
    evidence_grading_top_k_summarization: int = 25
    evidence_grading_top_k_qa: int = 10
    evidence_grading_top_k_comparison: int = 15
    evidence_grading_top_k_listing: int = 15
    evidence_grading_top_k_open_ended: int = 12

    # Bounded Corrective Retrieval (FR-016)
    corrective_retrieval_max_attempts: int = 2

    # Composed RAG pipeline (Flow 2 - Flow 5)
    query_analysis_max_expansion: int = 3
    query_analysis_max_sub_queries: int = 3
    answer_revision_max_attempts: int = 1

    # Embeddings (Hugging Face Inference API)
    embedding_provider: str = "huggingface"
    embedding_model: str = "Snowflake/snowflake-arctic-embed-m"
    embedding_dimension: int = 768
    huggingface_token: str = ""
    huggingface_inference_url: str = "https://router.huggingface.co/v1"

    # Groq (LLM / query processing, used in later features)
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_chat_model: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()