from __future__ import annotations

import abc
import logging
import time

from app.core.config import settings
from app.schemas.retrieval import ChunkResult

logger = logging.getLogger(__name__)


class RerankingError(Exception):
    """Raised when cross-encoder reranking fails."""


class CrossEncoderProvider(abc.ABC):
    """Abstract base class for cross-encoder reranking providers."""

    @abc.abstractmethod
    def rerank(self, query: str, contents: list[str]) -> list[float]:
        """Score each ``(query, content)`` pair and return a relevance score per item."""
        ...


class SentenceTransformerCrossEncoderProvider(CrossEncoderProvider):
    """Cross-encoder reranker backed by a Hugging Face model.

    The model is loaded lazily on first use (as a module-level singleton) so
    it is not loaded at application startup, and it is reused across requests.
    """

    _model = None
    _tokenizer = None

    def __init__(
        self,
        model_name: str | None = None,
    ):
        self.model_name = model_name or settings.reranker_model

    @property
    def model(self):
        if self.__class__._model is None:
            self._load_model()
        return self.__class__._model

    @property
    def tokenizer(self):
        if self.__class__._tokenizer is None:
            self._load_model()
        return self.__class__._tokenizer

    def _load_model(self) -> None:
        try:
            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
            )
        except ImportError as exc:
            raise RerankingError(
                "transformers is required for reranking. Install it via "
                "`pip install transformers torch`"
            ) from exc

        logger.info("Loading cross-encoder model %s", self.model_name)
        try:
            self.__class__._model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            self.__class__._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        except Exception as exc:
            raise RerankingError(
                f"Failed to load reranker model {self.model_name}: {exc}"
            ) from exc
        logger.info("Cross-encoder model %s loaded", self.model_name)

    def rerank(self, query: str, contents: list[str]) -> list[float]:
        if not contents:
            return []

        encoded = self.tokenizer(
            [(query, content) for content in contents],
            padding=True,
            truncation=True,
            return_tensors="pt",
        )

        try:
            import torch

            with torch.no_grad():
                outputs = self.model(**encoded)
            logits = outputs.logits
            scores = torch.nn.functional.sigmoid(logits).cpu()
            return [float(score) for score in scores]
        except Exception as exc:
            raise RerankingError(f"Reranking inference failed: {exc}") from exc


class RerankingService:
    """Reranks retrieval candidates with a cross-encoder model.

    The cross-encoder is loaded lazily on first use so the service can be
    injected (and the application started) without loading a model at startup.
    """

    def __init__(
        self,
        provider: CrossEncoderProvider | None = None,
    ):
        self._provider = provider

    @property
    def provider(self) -> CrossEncoderProvider:
        if self._provider is None:
            self._provider = self._build_default_provider()
        return self._provider

    @staticmethod
    def _build_default_provider() -> CrossEncoderProvider:
        return SentenceTransformerCrossEncoderProvider(
            model_name=settings.reranker_model,
        )

    @property
    def max_results(self) -> int:
        return settings.reranker_max_results

    def rerank(
        self,
        query: str,
        candidates: list[ChunkResult],
        top_n: int | None = None,
    ) -> list[ChunkResult]:
        """Score candidates against the query and return the top-N by relevance.

        Candidates are expected to be already ownership-filtered by the
        retrieval layer; no additional user/document filtering is performed
        here. The original retrieval ``score`` is preserved on each result and
        a new ``rerank_score`` is attached.
        """
        if not candidates:
            return []

        top_n = self._resolve_top_n(top_n)

        t0 = time.perf_counter()
        contents = [candidate.content for candidate in candidates]
        scores = self.provider.rerank(query, contents)

        if len(scores) != len(candidates):
            raise RerankingError(
                f"Expected {len(candidates)} rerank scores, got {len(scores)}"
            )

        reranked = [
            candidate.model_copy(update={"rerank_score": score})
            for candidate, score in zip(candidates, scores)
        ]
        reranked.sort(key=lambda item: item.rerank_score, reverse=True)

        logger.info(
            "Reranked %d candidates with %s in %.3fs (returning top %d)",
            len(reranked),
            settings.reranker_model,
            time.perf_counter() - t0,
            top_n,
        )
        return reranked[:top_n]

    def _resolve_top_n(self, top_n: int | None) -> int:
        if top_n is None:
            return self.max_results
        return max(1, min(top_n, self.max_results))