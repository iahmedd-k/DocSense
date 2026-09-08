from __future__ import annotations

import abc
import logging

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


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """Embedding provider backed by the Hugging Face Inference Providers router.

    Calls the OpenAI-compatible embeddings route hosted on the HF router:
        POST https://router.huggingface.co/v1/embeddings
    with ``{"model": <hf-model-id>, "input": [text, ...]}`` and returns one
    vector per text.
    """

    def __init__(
        self,
        token: str,
        model: str,
        base_url: str = "https://router.huggingface.co/v1",
    ):
        self.token = token
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=120.0)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
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

        Raises EmbeddingError on failure.
        """
        if not texts:
            return []

        logger.info(
            "Generating embeddings for %d texts using %s/%s",
            len(texts),
            settings.embedding_provider,
            settings.embedding_model,
        )

        embeddings = self.provider.embed(texts)

        if len(embeddings) != len(texts):
            raise EmbeddingError(
                f"Expected {len(texts)} embeddings, got {len(embeddings)}"
            )

        logger.info("Successfully generated %d embeddings", len(embeddings))
        return embeddings

    def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        results = self.generate_embeddings([text])
        return results[0]


def _parse_embeddings_response(data) -> list[list[float]]:
    """Normalize Hugging Face responses to a flat list of vectors.

    The HF router returns OpenAI-compatible responses::

        {"data": [{"embedding": [0.1, ...]}, {"embedding": [0.3, ...]}]}

    Some endpoints still return a bare list of vectors (``[[...], [...]]``)
    which we accept as a fallback.
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict) and "data" in data:
        items = sorted(data["data"], key=lambda item: item.get("index", 0))
        return [item["embedding"] for item in items]

    raise EmbeddingError(
        f"Unexpected Hugging Face response format: {type(data).__name__}"
    )