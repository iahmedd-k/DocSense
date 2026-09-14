import pytest
import httpx

from app.services.embedding_service import (
    EmbeddingError,
    EmbeddingService,
    HuggingFaceEmbeddingProvider,
)


class FakeProvider:
    def __init__(self, embeddings: list[list[float]] | None = None):
        self.embeddings = embeddings
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        if self.embeddings is None:
            return [[float(i)] for i in range(len(texts))]
        return self.embeddings


@pytest.fixture
def service() -> EmbeddingService:
    return EmbeddingService(provider=FakeProvider())


def test_generate_embeddings_returns_one_per_text(service):
    result = service.generate_embeddings(["one", "two", "three"])

    assert isinstance(result, list)
    assert len(result) == 3
    assert all(len(vec) == 1 for vec in result)


def test_generate_embeddings_empty_input(service):
    assert service.generate_embeddings([]) == []


def test_generate_single_embedding(service):
    result = service.generate_embedding("hello")

    assert result == [0.0]


def test_provider_called_with_input_texts(service):
    service.generate_embeddings(["alpha", "beta"])

    assert service.provider.calls == [["alpha", "beta"]]


def test_count_mismatch_raises(service):
    service = EmbeddingService(provider=FakeProvider(embeddings=[[0.1]]))
    with pytest.raises(EmbeddingError):
        service.generate_embeddings(["one", "two"])


def test_default_provider_requires_token(monkeypatch):
    monkeypatch.setattr("app.services.embedding_service.settings.huggingface_token", "")

    service = EmbeddingService()

    with pytest.raises(EmbeddingError, match="HUGGINGFACE_TOKEN"):
        service.generate_embeddings(["hello"])


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(
        "app.services.embedding_service.settings.embedding_provider", "unknown"
    )

    service = EmbeddingService()

    with pytest.raises(EmbeddingError, match="Unknown embedding provider"):
        service.generate_embeddings(["hello"])


# --------------------------------------------------------------------- #
# HuggingFaceEmbeddingProvider (HTTP mocked via httpx MockTransport)
# --------------------------------------------------------------------- #


def _provider_with(handler) -> HuggingFaceEmbeddingProvider:
    transport = httpx.MockTransport(handler)
    provider = HuggingFaceEmbeddingProvider(
        token="test-token",
        model="Snowflake/snowflake-arctic-embed-m",
    )
    provider._client = httpx.Client(transport=transport)
    return provider


def test_hf_provider_posts_to_embeddings_route():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("Authorization")
        captured["payload"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {"object": "embedding", "index": 0, "embedding": [0.1, 0.2]},
                    {"object": "embedding", "index": 1, "embedding": [0.3, 0.4]},
                ],
            },
        )

    provider = _provider_with(handler)
    result = provider.embed(["hello", "world"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    assert "Snowflake/snowflake-arctic-embed-m" in captured["url"]
    assert captured["auth"] == "Bearer test-token"


def test_hf_provider_sends_model_and_inputs():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = request.read().decode()
        return httpx.Response(200, json={"data": [{"embedding": [0.0]}]})

    provider = _provider_with(handler)
    provider.embed(["hello"])

    import json
    payload = json.loads(captured["payload"])
    assert "inputs" in payload
    assert payload["inputs"] == ["hello"]


def test_hf_provider_accepts_openai_compatible_response():
    def handler(request: httpx.Request) -> httpx.Response:
        data = [
            {"object": "embedding", "index": 1, "embedding": [9.0]},
            {"object": "embedding", "index": 0, "embedding": [1.0]},
        ]
        return httpx.Response(200, json={"object": "list", "data": data, "model": "m"})

    provider = _provider_with(handler)
    result = provider.embed(["first", "second"])

    assert result == [[1.0], [9.0]]


def test_hf_provider_http_error_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "Model too busy"})

    provider = _provider_with(handler)

    with pytest.raises(EmbeddingError, match="503"):
        provider.embed(["hello"])


def test_hf_provider_network_error_raises():
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    provider = _provider_with(boom)

    with pytest.raises(EmbeddingError, match="connect"):
        provider.embed(["hello"])


def test_hf_provider_empty_input():
    provider = HuggingFaceEmbeddingProvider(
        token="test-token",
        model="Snowflake/snowflake-arctic-embed-m",
    )

    assert provider.embed([]) == []