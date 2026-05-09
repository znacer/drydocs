"""MinIO storage client and helpers."""

import asyncio
import logging
from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error
from minio.helpers import ObjectWriteResult

from app.config import settings
from app.exceptions import StorageDeleteError, StorageDownloadError, StorageUploadError

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO client wrapper for document storage.

    Provides a high-level interface for file operations with MinIO object storage.
    Handles connection management, bucket operations, and file CRUD operations.
    Uses asyncio.to_thread() to avoid blocking the event loop.
    """

    def __init__(self) -> None:
        """Initialize MinIO client with configuration from settings."""
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket

    async def ensure_bucket(self) -> None:
        """Ensure the bucket exists.

        Creates the bucket if it doesn't already exist.
        """
        await asyncio.to_thread(self._ensure_bucket_sync)

    def _ensure_bucket_sync(self) -> None:
        """Synchronous implementation of ensure_bucket."""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info(f"Created bucket: {self.bucket}")

    async def upload_file(self, bucket: str, object_name: str, file_data: bytes) -> ObjectWriteResult:
        """Upload a file to MinIO.

        Args:
            bucket: Bucket name
            object_name: Object key/path
            file_data: File content as bytes

        Returns:
            ObjectWriteResult from MinIO

        Raises:
            StorageUploadError: If the upload fails
        """
        return await asyncio.to_thread(self._upload_file_sync, bucket, object_name, file_data)

    def _upload_file_sync(self, bucket: str, object_name: str, file_data: bytes) -> ObjectWriteResult:
        """Synchronous implementation of upload_file."""
        try:
            # MinIO put_object expects a file-like object (BinaryIO)
            data_stream = BytesIO(file_data)
            result = self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=data_stream,
                length=len(file_data),
            )
            logger.debug(f"Uploaded {object_name} to bucket {bucket}")
            return result
        except S3Error as e:
            logger.error(f"MinIO upload error for {object_name}: {e}")
            raise StorageUploadError(object_name, str(e))

    async def download_file(self, bucket: str, object_name: str) -> bytes:
        """Download a file from MinIO.

        Args:
            bucket: Bucket name
            object_name: Object key/path

        Returns:
            File content as bytes

        Raises:
            StorageDownloadError: If the download fails
        """
        return await asyncio.to_thread(self._download_file_sync, bucket, object_name)

    def _download_file_sync(self, bucket: str, object_name: str) -> bytes:
        """Synchronous implementation of download_file."""
        try:
            data = self.client.get_object(bucket_name=bucket, object_name=object_name)
            content = data.read()
            data.close()
            data.release_conn()
            logger.debug(f"Downloaded {object_name} from bucket {bucket}")
            return content
        except S3Error as e:
            logger.error(f"MinIO download error for {object_name}: {e}")
            raise StorageDownloadError(object_name, str(e))

    async def file_exists(self, bucket: str, object_name: str) -> bool:
        """Check if a file exists in MinIO.

        Args:
            bucket: Bucket name
            object_name: Object key/path

        Returns:
            True if file exists, False otherwise
        """
        return await asyncio.to_thread(self._file_exists_sync, bucket, object_name)

    def _file_exists_sync(self, bucket: str, object_name: str) -> bool:
        """Synchronous implementation of file_exists."""
        try:
            self.client.stat_object(bucket_name=bucket, object_name=object_name)
            return True
        except S3Error:
            return False

    async def delete_file(self, bucket: str, object_name: str) -> bool:
        """Delete a file from MinIO.

        Args:
            bucket: Bucket name
            object_name: Object key/path

        Returns:
            True if deletion was successful, False if file didn't exist

        Raises:
            StorageDeleteError: If deletion fails for other reasons
        """
        return await asyncio.to_thread(self._delete_file_sync, bucket, object_name)

    def _delete_file_sync(self, bucket: str, object_name: str) -> bool:
        """Synchronous implementation of delete_file."""
        try:
            if self._file_exists_sync(bucket, object_name):
                self.client.remove_object(bucket_name=bucket, object_name=object_name)
                logger.debug(f"Deleted {object_name} from bucket {bucket}")
                return True
            return False
        except S3Error as e:
            logger.error(f"MinIO delete error for {object_name}: {e}")
            raise StorageDeleteError(object_name, str(e))

    async def delete_files_by_prefix(self, bucket: str, prefix: str) -> int:
        """Delete all files with a given prefix from MinIO.

        Useful for cleaning up all files associated with a document.

        Args:
            bucket: Bucket name
            prefix: Object name prefix to match (e.g., "doc-id/" for all document files)

        Returns:
            Number of files deleted

        Raises:
            StorageDeleteError: If deletion fails
        """
        return await asyncio.to_thread(self._delete_files_by_prefix_sync, bucket, prefix)

    def _delete_files_by_prefix_sync(self, bucket: str, prefix: str) -> int:
        """Synchronous implementation of delete_files_by_prefix."""
        try:
            objects = self.client.list_objects(bucket_name=bucket, prefix=prefix, recursive=True)
            deleted_count = 0
            for obj in objects:
                if obj.object_name is not None:
                    self.client.remove_object(bucket_name=bucket, object_name=obj.object_name)
                    deleted_count += 1
                    logger.debug(f"Deleted {obj.object_name} from bucket {bucket}")
            logger.info(f"Deleted {deleted_count} files with prefix '{prefix}' from bucket {bucket}")
            return deleted_count
        except S3Error as e:
            logger.error(f"MinIO batch delete error for prefix {prefix}: {e}")
            raise StorageDeleteError(prefix, str(e))

    async def list_files(self, bucket: str, prefix: str | None = None) -> list[str]:
        """List all files in a bucket with optional prefix filter.

        Args:
            bucket: Bucket name
            prefix: Optional prefix to filter objects

        Returns:
            List of object names
        """
        return await asyncio.to_thread(self._list_files_sync, bucket, prefix)

    def _list_files_sync(self, bucket: str, prefix: str | None = None) -> list[str]:
        """Synchronous implementation of list_files."""
        try:
            objects = self.client.list_objects(
                bucket_name=bucket,
                prefix=prefix or "",
                recursive=True,
            )
            return [obj.object_name for obj in objects if obj.object_name is not None]
        except S3Error as e:
            logger.error(f"MinIO list error: {e}")
            return []

    async def get_presigned_url(self, bucket: str, object_name: str, expiry: int = 3600) -> str:
        """
        Get a presigned URL for temporary access to a file.

        Args:
            bucket: Bucket name
            object_name: Object key/path
            expiry: URL expiry time in seconds

        Returns:
            Presigned URL string
        """
        return await asyncio.to_thread(self._get_presigned_url_sync, bucket, object_name, expiry)

    def _get_presigned_url_sync(self, bucket: str, object_name: str, expiry: int = 3600) -> str:
        """Synchronous implementation of get_presigned_url."""
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=timedelta(seconds=expiry),
            )
            return url
        except S3Error as e:
            logger.error(f"MinIO presigned URL error: {e}")
            raise


# Singleton client instance
minio_client = MinIOClient()


# Convenience functions for direct use
def get_client() -> MinIOClient:
    """Get the MinIO client instance."""
    return minio_client


# Async wrappers for use with async/await
async def upload_file(bucket: str, object_name: str, file_data: bytes) -> ObjectWriteResult:
    """Async wrapper for upload_file."""
    return await minio_client.upload_file(bucket, object_name, file_data)


async def download_file(bucket: str, object_name: str) -> bytes:
    """Async wrapper for download_file."""
    return await minio_client.download_file(bucket, object_name)


async def file_exists(bucket: str, object_name: str) -> bool:
    """Async wrapper for file_exists."""
    return await minio_client.file_exists(bucket, object_name)


async def delete_file(bucket: str, object_name: str) -> bool:
    """Async wrapper for delete_file."""
    return await minio_client.delete_file(bucket, object_name)


async def delete_files_by_prefix(bucket: str, prefix: str) -> int:
    """Async wrapper for delete_files_by_prefix."""
    return await minio_client.delete_files_by_prefix(bucket, prefix)


async def list_files(bucket: str, prefix: str | None = None) -> list[str]:
    """Async wrapper for list_files."""
    return await minio_client.list_files(bucket, prefix)


async def ensure_bucket() -> None:
    """Async wrapper for ensure_bucket."""
    await minio_client.ensure_bucket()
