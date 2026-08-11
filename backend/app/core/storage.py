"""MinIO / S3 Object Storage Provider abstraction and implementation."""

import abc
import asyncio
import io
from typing import Optional
from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AbstractStorageProvider(abc.ABC):
    """Abstract interface for object storage operations."""

    @abc.abstractmethod
    async def upload_file(
        self,
        file_bytes: bytes,
        destination_filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload file content and return accessible URL/path."""
        pass

    @abc.abstractmethod
    async def get_file_url(self, filename: str) -> str:
        """Get publicly accessible or presigned URL for a file."""
        pass

    @abc.abstractmethod
    async def delete_file(self, filename: str) -> bool:
        """Delete file from storage."""
        pass


class MinIOStorageProvider(AbstractStorageProvider):
    """MinIO / S3 compatible object storage provider implementation."""

    def __init__(self) -> None:
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.secure = settings.MINIO_USE_SSL
        self.public_url = settings.MINIO_PUBLIC_URL

        self.client = Minio(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )
        self._bucket_checked = False

    def _ensure_bucket_exists_sync(self) -> None:
        """Synchronously check and create bucket if missing."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info("MinIO bucket created successfully", bucket=self.bucket_name)
        except S3Error as err:
            logger.error("Failed to ensure MinIO bucket existence", error=str(err))
            raise

    async def _ensure_bucket_exists(self) -> None:
        """Asynchronously ensure bucket exists."""
        if not self._bucket_checked:
            await asyncio.to_thread(self._ensure_bucket_exists_sync)
            self._bucket_checked = True

    async def upload_file(
        self,
        file_bytes: bytes,
        destination_filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload file bytes to MinIO bucket asynchronously."""
        await self._ensure_bucket_exists()

        def _upload() -> str:
            stream = io.BytesIO(file_bytes)
            file_len = len(file_bytes)
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=destination_filename,
                data=stream,
                length=file_len,
                content_type=content_type,
            )
            return f"{self.public_url}/{self.bucket_name}/{destination_filename}"

        try:
            file_url = await asyncio.to_thread(_upload)
            logger.info("File uploaded to MinIO", filename=destination_filename, url=file_url)
            return file_url
        except Exception as e:
            logger.error("Failed to upload file to MinIO", filename=destination_filename, error=str(e))
            raise

    async def get_file_url(self, filename: str) -> str:
        """Get accessible URL for a stored object."""
        return f"{self.public_url}/{self.bucket_name}/{filename}"

    async def delete_file(self, filename: str) -> bool:
        """Delete an object from MinIO bucket asynchronously."""
        await self._ensure_bucket_exists()

        def _delete() -> bool:
            self.client.remove_object(self.bucket_name, filename)
            return True

        try:
            result = await asyncio.to_thread(_delete)
            logger.info("File deleted from MinIO", filename=filename)
            return result
        except Exception as e:
            logger.error("Failed to delete file from MinIO", filename=filename, error=str(e))
            return False


_storage_instance: Optional[AbstractStorageProvider] = None


def get_storage_provider() -> AbstractStorageProvider:
    """Return storage provider instance singleton."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = MinIOStorageProvider()
    return _storage_instance
