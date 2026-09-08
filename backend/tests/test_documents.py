from app.core.config import settings

VALID_PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def _mock_cloudinary_upload(monkeypatch, fail=False):
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "test-cloud")

    def fake_upload(file, public_id=None, resource_type=None, **kwargs):
        if fail:
            raise Exception("cloudinary down")
        return {
            "public_id": public_id,
            "secure_url": f"https://res.cloudinary.com/{public_id}.pdf",
        }

    monkeypatch.setattr("app.services.storage_service.uploader.upload", fake_upload)


def _register(client, email="owner@example.com"):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Doc",
            "last_name": "Owner",
            "email": email,
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    return resp.json()["access_token"]


def test_upload_requires_auth(client):
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("resume.pdf", VALID_PDF, "application/pdf")},
    )

    assert resp.status_code == 401


def test_upload_success(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token = _register(client)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("resume.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "resume.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] == len(VALID_PDF)
    assert data["status"] == "uploaded"
    assert data["storage_key"].startswith("docsense/users/")
    assert data["user_id"] == 1


def test_upload_rejects_non_pdf(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token = _register(client)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 400


def test_upload_rejects_wrong_mime_for_pdf(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token = _register(client)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("photo.pdf", VALID_PDF, "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 400


def test_upload_rejects_empty_file(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token = _register(client)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 400


def test_upload_rejects_oversized_file(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token = _register(client)

    oversized = b"x" * (settings.max_file_size_mb * 1024 * 1024 + 1)
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("big.pdf", oversized, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 400


def test_upload_storage_failure_returns_503(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch, fail=True)
    token = _register(client)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("resume.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 503


def test_list_returns_only_own_documents(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token_owner = _register(client, "owner@example.com")
    token_other = _register(client, "other@example.com")

    client.post(
        "/api/v1/documents/upload",
        files={"file": ("a.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("b.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("c.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token_other}"},
    )

    owner_docs = client.get(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    other_docs = client.get(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token_other}"},
    )

    assert owner_docs.status_code == 200
    assert [doc["filename"] for doc in owner_docs.json()] == ["b.pdf", "a.pdf"]
    assert [doc["filename"] for doc in other_docs.json()] == ["c.pdf"]


def test_cannot_access_another_users_document(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token_owner = _register(client, "owner@example.com")
    token_other = _register(client, "other@example.com")

    upload = client.post(
        "/api/v1/documents/upload",
        files={"file": ("private.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token_owner}"},
    ).json()

    resp = client.get(
        f"/api/v1/documents/{upload['id']}",
        headers={"Authorization": f"Bearer {token_other}"},
    )

    assert resp.status_code == 404


def test_get_document_not_found(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token = _register(client)

    resp = client.get(
        "/api/v1/documents/999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 404