from pathlib import Path

import pytest

from app.core.config import settings
from app.services.pdf_parser_service import (
    PdfPage,
    PdfParseError,
    ParsedPdf,
    PdfParserService,
)

VALID_PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


@pytest.fixture(autouse=True)
def _temp_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "local_temp_dir", str(tmp_path / "tmp"))


def _mock_cloudinary_upload(monkeypatch, fail=False):
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "test-cloud")
    _mock_pdf_parser(monkeypatch)

    def fake_upload(file, public_id=None, resource_type=None, **kwargs):
        if fail:
            raise Exception("cloudinary down")
        return {
            "public_id": public_id,
            "secure_url": f"https://res.cloudinary.com/{public_id}.pdf",
        }

    monkeypatch.setattr("app.services.storage_service.uploader.upload", fake_upload)


def _mock_pdf_parser(monkeypatch, fail=False):
    def fake_parse(self, file_path):
        if fail:
            raise PdfParseError("corrupt pdf")
        return ParsedPdf(
            pages=[PdfPage(page_number=1, extracted_text="Resume text")],
            total_pages=1,
        )

    monkeypatch.setattr(PdfParserService, "parse", fake_parse)


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
    assert data["original_filename"] == "resume.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] == len(VALID_PDF)
    assert data["status"] == "completed"
    assert data["storage_key"].startswith("docsense/users/")
    assert data["storage_url"].startswith("https://res.cloudinary.com/")
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
    assert [doc["original_filename"] for doc in owner_docs.json()] == ["b.pdf", "a.pdf"]
    assert [doc["original_filename"] for doc in other_docs.json()] == ["c.pdf"]


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


def test_get_document_status_own_document(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token = _register(client)

    upload = client.post(
        "/api/v1/documents/upload",
        files={"file": ("resume.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    resp = client.get(
        f"/api/v1/documents/{upload['id']}/status",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert resp.json() == {
        "document_id": upload["id"],
        "status": "completed",
    }


def test_get_document_status_requires_auth(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token = _register(client)

    upload = client.post(
        "/api/v1/documents/upload",
        files={"file": ("resume.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    resp = client.get(f"/api/v1/documents/{upload['id']}/status")

    assert resp.status_code == 401


def test_get_document_status_non_existent(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token = _register(client)

    resp = client.get(
        "/api/v1/documents/9999/status",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 404


def test_get_document_status_other_users_document(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token_owner = _register(client, "owner@example.com")
    token_other = _register(client, "other@example.com")

    upload = client.post(
        "/api/v1/documents/upload",
        files={"file": ("private.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token_owner}"},
    ).json()

    resp = client.get(
        f"/api/v1/documents/{upload['id']}/status",
        headers={"Authorization": f"Bearer {token_other}"},
    )

    assert resp.status_code == 404


def test_upload_corrupt_pdf_marks_failed(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    _mock_pdf_parser(monkeypatch, fail=True)
    token = _register(client)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("broken.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "failed"
    assert data["storage_url"].startswith("https://res.cloudinary.com/")

    temp_path = (
        Path(settings.local_temp_dir)
        / f"user_{data['user_id']}"
        / f"{Path(data['storage_key']).name}.pdf"
    )
    assert temp_path.is_file()


def test_temp_file_deleted_after_successful_processing(client, monkeypatch):
    _mock_cloudinary_upload(monkeypatch)
    token = _register(client)

    data = client.post(
        "/api/v1/documents/upload",
        files={"file": ("resume.pdf", VALID_PDF, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    temp_path = (
        Path(settings.local_temp_dir)
        / f"user_{data['user_id']}"
        / f"{Path(data['storage_key']).name}.pdf"
    )
    assert not temp_path.exists()