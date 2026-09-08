from functools import lru_cache

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

    cors_origins: list[str] = ["*"]

    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    max_file_size_mb: int = 10

    local_temp_dir: str = "./tmp"

    chunk_size: int = 500
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

    # Evidence Sufficiency Grading (FR-015)
    evidence_grading_top_k: int = 4

    # Bounded Corrective Retrieval (FR-016)
    corrective_retrieval_max_attempts: int = 2

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