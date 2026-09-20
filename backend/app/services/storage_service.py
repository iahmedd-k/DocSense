import io
from uuid import uuid4

import cloudinary
from cloudinary import uploader
import httpx

from app.core.config import settings


class StorageError(Exception):
    """Raised when an operation against the object storage backend fails."""


_cloudinary_configured = False


def _ensure_cloudinary_config() -> None:
    global _cloudinary_configured
    if _cloudinary_configured:
        return
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    _cloudinary_configured = True


class StorageService:

    def _supabase_headers(self) -> dict[str, str]:
        key = settings.supabase_secret_key or settings.supabase_publishable_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
        }

    def _upload_supabase(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: int,
        public_id: str | None = None,
    ) -> tuple[str, str]:
        """Upload a file to Supabase Storage bucket."""
        bucket = settings.supabase_bucket or "documents"
        storage_path = public_id or f"users/{user_id}/{uuid4().hex}_{filename}"
        base_url = settings.supabase_url.rstrip("/")
        upload_url = f"{base_url}/storage/v1/object/{bucket}/{storage_path}"

        headers = self._supabase_headers()
        headers["x-upsert"] = "true"

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    upload_url,
                    headers=headers,
                    content=file_bytes,
                )
                if resp.status_code not in (200, 201):
                    raise StorageError(
                        f"Supabase Storage error ({resp.status_code}): {resp.text}"
                    )
        except Exception as exc:
            raise StorageError(
                f"Failed to upload file '{filename}' to Supabase Storage"
            ) from exc

        public_url = f"{base_url}/storage/v1/object/public/{bucket}/{storage_path}"
        return storage_path, public_url

    def _delete_supabase(self, storage_path: str) -> None:
        """Delete a file from Supabase Storage bucket."""
        bucket = settings.supabase_bucket or "documents"
        base_url = settings.supabase_url.rstrip("/")
        delete_url = f"{base_url}/storage/v1/object/{bucket}/{storage_path}"

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.delete(delete_url, headers=self._supabase_headers())
                if resp.status_code not in (200, 204):
                    # Attempt bulk delete format if single delete returned error
                    client.post(
                        f"{base_url}/storage/v1/object/{bucket}",
                        headers=self._supabase_headers(),
                        json={"prefixes": [storage_path]},
                    )
        except Exception as exc:
            raise StorageError(
                f"Failed to delete file '{storage_path}' from Supabase Storage"
            ) from exc

    def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: int,
        public_id: str | None = None,
    ) -> tuple[str, str]:
        """Upload any file to configured storage provider (Supabase Storage or Cloudinary)."""

        # 1. Prefer Supabase Storage if credentials are configured
        if settings.supabase_url and settings.supabase_secret_key:
            return self._upload_supabase(file_bytes, filename, user_id, public_id)

        # 2. Fallback to Cloudinary if configured
        if settings.cloudinary_cloud_name:
            _ensure_cloudinary_config()
            public_id = public_id or f"docsense/users/{user_id}/{uuid4().hex}"
            try:
                result = uploader.upload(
                    io.BytesIO(file_bytes),
                    public_id=public_id,
                    resource_type="raw",
                )
            except Exception as exc:
                raise StorageError(
                    f"Failed to upload file '{filename}' to Cloudinary"
                ) from exc

            return result["public_id"], result["secure_url"]

        raise StorageError("No storage provider configured (Supabase Storage or Cloudinary required).")

    def upload_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: int,
        public_id: str | None = None,
    ) -> tuple[str, str]:
        """Upload a PDF (backward compatible alias)."""
        return self.upload_file(file_bytes, filename, user_id, public_id)

    def delete_file(self, public_id: str) -> None:
        """Delete a file from the configured storage provider."""

        if settings.supabase_url and settings.supabase_secret_key:
            return self._delete_supabase(public_id)

        if settings.cloudinary_cloud_name:
            _ensure_cloudinary_config()
            try:
                uploader.destroy(public_id, resource_type="raw")
            except Exception as exc:
                raise StorageError(
                    f"Failed to delete file '{public_id}' from Cloudinary"
                ) from exc
            return

        raise StorageError("No storage provider configured.")