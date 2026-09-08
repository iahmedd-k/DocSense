import io
from uuid import uuid4

import cloudinary
from cloudinary import uploader

from app.core.config import settings


class StorageError(Exception):
    """Raised when an operation against the object storage backend fails."""


cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


class StorageService:

    def upload_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: int,
    ) -> tuple[str, str]:
        """Upload a PDF to Cloudinary and return (public_id, secure_url)."""

        if not settings.cloudinary_cloud_name:
            raise StorageError("Cloudinary is not configured")

        public_id = f"docsense/users/{user_id}/{uuid4().hex}"

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

    def delete_file(self, public_id: str) -> None:
        """Delete a file from Cloudinary by its public_id."""

        if not settings.cloudinary_cloud_name:
            raise StorageError("Cloudinary is not configured")

        try:
            uploader.destroy(public_id, resource_type="raw")
        except Exception as exc:
            raise StorageError(
                f"Failed to delete file '{public_id}' from Cloudinary"
            ) from exc