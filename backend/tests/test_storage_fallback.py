from app.core.config import settings
from app.services.storage_service import StorageError, StorageService


def _make_service(monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_secret_key", "sb_secret_test")
    monkeypatch.setattr(settings, "supabase_publishable_key", "")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "demo-cloud")
    monkeypatch.setattr(settings, "cloudinary_api_key", "demo-key")
    monkeypatch.setattr(settings, "cloudinary_api_secret", "demo-secret")
    return StorageService()


def test_upload_falls_back_to_cloudinary_when_supabase_fails(monkeypatch):
    service = _make_service(monkeypatch)

    def boom(*args, **kwargs):
        raise StorageError("supabase is down")

    monkeypatch.setattr(StorageService, "_upload_supabase", boom)

    uploaded = {"public_id": "docsense/users/1/abc", "secure_url": "https://cdn.demo/abc"}
    monkeypatch.setattr(
        "cloudinary.uploader.upload", lambda *a, **k: uploaded
    )

    key, url = service.upload_file(b"print('hi')", "dummy.py", 1)
    assert key == "docsense/users/1/abc"
    assert url == "https://cdn.demo/abc"


def test_upload_falls_back_to_supabase_when_cloudinary_fails(monkeypatch):
    service = _make_service(monkeypatch)

    def boom(*args, **kwargs):
        raise Exception("cloudinary is down")

    monkeypatch.setattr("cloudinary.uploader.upload", boom)

    expected = ("users/1/abc_dummy.py", "https://supabase.co/object/public/documents/users/1/abc_dummy.py")
    monkeypatch.setattr(
        StorageService, "_upload_supabase", lambda *a, **k: expected
    )

    key, url = service.upload_file(b"print('hi')", "dummy.py", 1)
    assert key == expected[0]
    assert url == expected[1]


def test_upload_raises_when_all_providers_fail(monkeypatch):
    service = _make_service(monkeypatch)

    monkeypatch.setattr(
        StorageService, "_upload_supabase", lambda *a, **k: (_ for _ in ()).throw(StorageError("supabase down"))
    )
    monkeypatch.setattr(
        "cloudinary.uploader.upload", lambda *a, **k: (_ for _ in ()).throw(Exception("cloudinary down"))
    )

    try:
        service.upload_file(b"print('hi')", "dummy.py", 1)
    except StorageError as exc:
        assert "Supabase Storage" in str(exc)
        assert "Cloudinary" in str(exc)
    else:
        raise AssertionError("Expected StorageError when all providers fail")


def test_upload_uses_supabase_when_it_succeeds(monkeypatch):
    service = _make_service(monkeypatch)

    expected = ("users/1/abc_dummy.py", "https://supabase.co/object/public/documents/users/1/abc_dummy.py")
    monkeypatch.setattr(
        StorageService, "_upload_supabase", lambda *a, **k: expected
    )
    monkeypatch.setattr(
        "cloudinary.uploader.upload", lambda *a, **k: (_ for _ in ()).throw(AssertionError("cloudinary should not be tried"))
    )

    key, url = service.upload_file(b"print('hi')", "dummy.py", 1)
    assert key == expected[0]
    assert url == expected[1]
