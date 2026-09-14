from __future__ import annotations

import abc
import logging
import time

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


class EmbeddingProvider(abc.ABC):
    """Abstract base class for embedding providers."""

    @abc.abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        ...


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        logger.info("Loading local embedding model: %s", model_name)
        self.model = SentenceTransformer(model_name)
        logger.info("Local embedding model loaded: %s", model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """Embedding provider backed by the Hugging Face Inference API.

    Calls the HF Inference API:
        POST https://api-inference.huggingface.co/models/{model}
    with ``{"inputs": [text, ...]}`` and returns one vector per text.
    """

    def __init__(
        self,
        token: str,
        model: str,
        base_url: str = "https://api-inference.huggingface.co",
    ):
        self.token = token
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=120.0)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        url = f"{self.base_url}/models/{self.model}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": texts,
        }

        try:
            response = self._client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise EmbeddingError(
                f"Hugging Face API returned status {exc.response.status_code}: "
                f"{exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise EmbeddingError(
                f"Failed to connect to Hugging Face API: {exc}"
            ) from exc

        return _parse_embeddings_response(response.json())


class EmbeddingService:
    """High-level service for generating text embeddings.

    The concrete provider is built lazily on first use so the service can be
    instantiated (and injected across the application) without requiring API
    credentials at startup.
    """

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
    ):
        self._provider = provider

    @property
    def provider(self) -> EmbeddingProvider:
        if self._provider is None:
            self._provider = self._build_default_provider()
        return self._provider

    @staticmethod
    def _build_default_provider() -> EmbeddingProvider:
        provider_name = settings.embedding_provider.lower()

        if provider_name == "local":
            return LocalEmbeddingProvider(model_name=settings.embedding_model)

        if provider_name == "huggingface":
            if not settings.huggingface_token:
                raise EmbeddingError(
                    "HUGGINGFACE_TOKEN is required for the Hugging Face "
                    "embedding provider"
                )
            return HuggingFaceEmbeddingProvider(
                token=settings.huggingface_token,
                model=settings.embedding_model,
                base_url=settings.huggingface_inference_url,
            )

        raise EmbeddingError(
            f"Unknown embedding provider: {provider_name}"
        )

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Rejects any text that is empty or whitespace-only as a safety net
        (the chunking layer is the primary guard for size).

        Raises EmbeddingError on failure.
        """
        if not texts:
            return []

        original_count = len(texts)
        filtered = [t for t in texts if t.strip()]

        if not filtered:
            raise EmbeddingError(
                "All texts rejected: no non-empty texts to embed"
            )

        if len(filtered) < original_count:
            logger.warning(
                "Filtered %d empty/whitespace texts before embedding "
                "(%d remaining)",
                original_count - len(filtered),
                len(filtered),
            )

        logger.info(
            "Generating embeddings for %d texts using %s/%s",
            len(filtered),
            settings.embedding_provider,
            settings.embedding_model,
        )

        t0 = time.perf_counter()
        embeddings = self.provider.embed(filtered)
        logger.info("Embedding generation: %.3fs", time.perf_counter() - t0)

        if len(embeddings) != len(filtered):
            raise EmbeddingError(
                f"Expected {len(filtered)} embeddings, got {len(embeddings)}"
            )

        logger.info("Successfully generated %d embeddings", len(embeddings))
        return embeddings

    @staticmethod
    def filter_texts(texts: list[str]) -> list[str]:
        """Filter out empty/whitespace-only texts to align with generate_embeddings."""
        return [t for t in texts if t.strip()]

    def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        results = self.generate_embeddings([text])
        return results[0]


def _parse_embeddings_response(data) -> list[list[float]]:
    """Normalize Hugging Face responses to a flat list of vectors.

    The HF API can return:
    - A bare list of vectors ``[[...], [...]]`` for multiple inputs
    - A single flat vector ``[...]`` for a single input
    - An OpenAI-compatible dict ``{"data": [{"embedding": ...}]}``
    """
    if isinstance(data, list):
        if data and isinstance(data[0], (int, float)):
            return [data]
        return data

    if isinstance(data, dict) and "data" in data:
        items = sorted(data["data"], key=lambda item: item.get("index", 0))
        return [item["embedding"] for item in items]

    raise EmbeddingError(
        f"Unexpected Hugging Face response format: {type(data).__name__}"
    )