from app.api.v1.endpoints.chat import get_rag_service
from app.main import app


def _rag_response(abstained=False, **overrides):
    data = {
        "query": "What is the budget?",
        "query_analysis": {
            "original_query": "What is the budget?",
            "expanded_queries": [],
            "sub_queries": [],
            "rationale": "single query is enough",
        },
        "evidence": [
            {
                "chunk_id": 1,
                "document_id": 2,
                "content": "The budget is 100M.",
                "page_number": 3,
                "page_numbers": [3],
                "content_type": "text",
                "metadata": {},
                "score": 0.9,
            }
        ],
        "verdict": {
            "sufficient": True,
            "confidence_score": 0.9,
            "reason": "enough",
            "missing_information": [],
        },
        "answer": "The budget is 100M.",
        "citations": [
            {
                "text": "The budget is 100M.",
                "document_id": 2,
                "page_number": 3,
                "chunk_id": 1,
                "confidence": 0.9,
            }
        ],
        "verification": {
            "supported": True,
            "citations_correct": True,
            "issues": [],
            "explanation": "ok",
        },
        "abstained": False,
        "abstention_reason": None,
        "abstention_suggestion": "",
        "corrective_queries": [],
        "corrective_attempts": 0,
        "revision_attempts": 0,
    }
    if abstained:
        data.update(
            {
                "abstained": True,
                "answer": None,
                "citations": [],
                "verification": None,
                "abstention_reason": "Insufficient evidence.",
            }
        )
    data.update(overrides)
    return data


class StubRAGService:
    def __init__(self):
        self.received = {}
        self.response = _rag_response()

    def answer(self, user_id, query, top_k=None, max_revision_attempts=None):
        self.received = {
            "user_id": user_id,
            "query": query,
            "top_k": top_k,
            "max_revision_attempts": max_revision_attempts,
        }
        return self.response


def _register(client, email):
    return client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Rag",
            "last_name": "User",
            "email": email,
            "password": "password123",
            "confirm_password": "password123",
        },
    ).json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_rag_requires_auth(client):
    resp = client.post("/api/v1/chat", json={"query": "What is the budget?"})

    assert resp.status_code == 401


def test_rag_returns_grounded_response(client):
    stub = StubRAGService()
    app.dependency_overrides[get_rag_service] = lambda: stub

    token = _register(client, "rag-user@example.com")

    resp = client.post(
        "/api/v1/chat",
        json={"query": "What is the budget?", "top_k": 5},
        headers=_auth_headers(token),
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["abstained"] is False
    assert data["answer"] == "The budget is 100M."
    assert data["citations"][0]["document_id"] == 2
    assert stub.received["user_id"] == 1
    assert stub.received["query"] == "What is the budget?"
    assert stub.received["top_k"] == 5


def test_rag_returns_abstention_response(client):
    stub = StubRAGService()
    stub.response = _rag_response(abstained=True)
    app.dependency_overrides[get_rag_service] = lambda: stub

    token = _register(client, "rag-abstain@example.com")

    resp = client.post(
        "/api/v1/chat",
        json={"query": "What is unknown?"},
        headers=_auth_headers(token),
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["abstained"] is True
    assert data["answer"] is None
    assert data["abstention_reason"] == "Insufficient evidence."


def test_rag_rejects_empty_query(client):
    stub = StubRAGService()
    app.dependency_overrides[get_rag_service] = lambda: stub

    token = _register(client, "rag-empty@example.com")

    resp = client.post(
        "/api/v1/chat",
        json={"query": ""},
        headers=_auth_headers(token),
    )

    assert resp.status_code == 422