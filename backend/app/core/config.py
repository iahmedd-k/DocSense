from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
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

    database_url: str = Field(
        default="postgresql+psycopg://docsense:adminadmin@localhost:5432/docsense",
        validation_alias=AliasChoices("database_url", "DATABASE_URL"),
    )

    jwt_secret_key: str = Field(
        default="change-me-in-production",
        validation_alias=AliasChoices("jwt_secret_key", "JWT_SECRET_KEY"),
    )
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
            if v_str.startswith("["):
                try:
                    import json

                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            origins = [origin.strip() for origin in v_str.split(",") if origin.strip()]
            return origins if origins else default_origins
        if isinstance(v, list):
            origins = [str(origin).strip() for origin in v if str(origin).strip()]
            return origins if origins else default_origins
        return default_origins

    # Supabase (Object Storage)
    supabase_url: str = Field(
        default="",
        validation_alias=AliasChoices("supabase_url", "SUPABASE_URL"),
    )
    supabase_secret_key: str = Field(
        default="",
        validation_alias=AliasChoices("supabase_secret_key", "SUPABASE_SECRET_KEY", "supabase_service_role_key", "SUPABASE_SERVICE_ROLE_KEY"),
    )
    supabase_bucket: str = "documents"

    # Cloudinary (Object Storage — fallback)
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # Document upload limits
    max_file_size_mb: int = 10
    local_temp_dir: str = "./tmp"

    # Chunking defaults (FR-007)
    chunk_size: int = 512
    chunk_overlap: int = 50

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
    embedding_provider: str = Field(
        default="huggingface",
        validation_alias=AliasChoices("embedding_provider", "EMBEDDING_PROVIDER"),
    )
    embedding_model: str = Field(
        default="Snowflake/snowflake-arctic-embed-m",
        validation_alias=AliasChoices("embedding_model", "EMBEDDING_MODEL"),
    )
    embedding_dimension: int = 768
    huggingface_token: str = Field(
        default="",
        validation_alias=AliasChoices("huggingface_token", "HUGGINGFACE_TOKEN", "hf_token", "HF_TOKEN"),
    )
    huggingface_inference_url: str = Field(
        default="https://router.huggingface.co/v1",
        validation_alias=AliasChoices("huggingface_inference_url", "HUGGINGFACE_INFERENCE_URL"),
    )

    # Groq (LLM / query processing)
    groq_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("groq_api_key", "GROQ_API_KEY"),
    )
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_chat_model: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()