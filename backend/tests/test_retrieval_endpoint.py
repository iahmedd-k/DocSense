from app.api.v1.endpoints.search import get_retrieval_service
from app.main import app


class StubRetrievalService:
    def __init__(self):
        self.received = {}

    def search(self, user_id, query, method, top_k=None, rerank=False):
        self.received = {
            "user_id": user_id,
            "query": query,
            "method": method,
            "top_k": top_k,
            "rerank": rerank,
        }
        return {
            "query": query,
            "results": [
                {
                    "chunk_id": 1,
                    "document_id": 2,
                    "content": "matched chunk",
                    "page_number": 3,
                    "page_numbers": [3],
                    "content_type": "text",
                    "metadata": {"source": "pdf"},
                    "score": 0.95,
                    "rerank_score": 0.9 if rerank else None,
                }
            ],
        }


def _override_service(app, stub):
    app.dependency_overrides[get_retrieval_service] = lambda: stub


def test_search_requires_auth(client):
    resp = client.get("/api/v1/search", params={"query": "resume", "method": "vector"})

    assert resp.status_code == 401


def test_search_vector_returns_results_and_scopes_to_user(client):
    stub = StubRetrievalService()
    _override_service(app, stub)

    token = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Doc",
            "last_name": "Owner",
            "email": "searcher@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/search",
        params={"query": "budget report", "method": "vector", "top_k": 7},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "budget report"
    assert data["results"][0]["chunk_id"] == 1
    assert stub.received["user_id"] == 1
    assert stub.received["query"] == "budget report"
    assert stub.received["method"].value == "vector"
    assert stub.received["top_k"] == 7


def test_search_lexical_uses_lexical_method(client):
    stub = StubRetrievalService()
    _override_service(app, stub)

    token = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Lex",
            "last_name": "User",
            "email": "lexical@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/search",
        params={"query": "annual report", "method": "lexical"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert stub.received["method"].value == "lexical"


def test_search_hybrid_uses_hybrid_method(client):
    stub = StubRetrievalService()
    _override_service(app, stub)

    token = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Hyb",
            "last_name": "User",
            "email": "hybrid@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/search",
        params={"query": "profit margin", "method": "hybrid"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert stub.received["method"].value == "hybrid"
    assert stub.received["user_id"] == 1


def test_search_rejects_empty_query(client):
    stub = StubRetrievalService()
    _override_service(app, stub)

    token = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Doc",
            "last_name": "Owner",
            "email": "empty-query@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/search",
        params={"query": "", "method": "vector"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422


def test_search_rejects_unknown_method(client):
    stub = StubRetrievalService()
    _override_service(app, stub)

    token = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Doc",
            "last_name": "Owner",
            "email": "bad-method@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/search",
        params={"query": "hello", "method": "fuzzy"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422


def test_search_rerank_flag_pass_through(client):
    stub = StubRetrievalService()
    _override_service(app, stub)

    token = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Rer",
            "last_name": "Rank",
            "email": "rerank@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/search",
        params={"query": "budget report", "method": "vector", "rerank": "true"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert stub.received["rerank"] is True
    assert resp.json()["results"][0]["rerank_score"] == 0.9
