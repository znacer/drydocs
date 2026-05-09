"""MinIO storage client and helpers."""

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

    def ensure_bucket(self) -> None:
        """Ensure the bucket exists.

        Creates the bucket if it doesn't already exist.
        """
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info(f"Created bucket: {self.bucket}")

    def upload_file(self, bucket: str, object_name: str, file_data: bytes) -> ObjectWriteResult:
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

    def download_file(self, bucket: str, object_name: str) -> bytes:
        """Download a file from MinIO.

        Args:
            bucket: Bucket name
            object_name: Object key/path

        Returns:
            File content as bytes

        Raises:
            StorageDownloadError: If the download fails
        """
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

    def file_exists(self, bucket: str, object_name: str) -> bool:
        """Check if a file exists in MinIO.

        Args:
            bucket: Bucket name
            object_name: Object key/path

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(bucket_name=bucket, object_name=object_name)
            return True
        except S3Error:
            return False

    def delete_file(self, bucket: str, object_name: str) -> bool:
        """Delete a file from MinIO.

        Args:
            bucket: Bucket name
            object_name: Object key/path

        Returns:
            True if deletion was successful, False if file didn't exist

        Raises:
            StorageDeleteError: If deletion fails for other reasons
        """
        try:
            if self.file_exists(bucket, object_name):
                self.client.remove_object(bucket_name=bucket, object_name=object_name)
                logger.debug(f"Deleted {object_name} from bucket {bucket}")
                return True
            return False
        except S3Error as e:
            logger.error(f"MinIO delete error for {object_name}: {e}")
            raise StorageDeleteError(object_name, str(e))

    def delete_files_by_prefix(self, bucket: str, prefix: str) -> int:
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

    def list_files(self, bucket: str, prefix: str | None = None) -> list:
        """List all files in a bucket with optional prefix filter.

        Args:
            bucket: Bucket name
            prefix: Optional prefix to filter objects

        Returns:
            List of object names
        """
        try:
            objects = self.client.list_objects(
                bucket_name=bucket,
                prefix=prefix or "",
                recursive=True,
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"MinIO list error: {e}")
            return []

    def get_presigned_url(self, bucket: str, object_name: str, expiry: int = 3600) -> str:
        """
        Get a presigned URL for temporary access to a file.

        Args:
            bucket: Bucket name
            object_name: Object key/path
            expiry: URL expiry time in seconds

        Returns:
            Presigned URL string
        """
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
    return minio_client.upload_file(bucket, object_name, file_data)


async def download_file(bucket: str, object_name: str) -> bytes:
    """Async wrapper for download_file."""
    return minio_client.download_file(bucket, object_name)


async def file_exists(bucket: str, object_name: str) -> bool:
    """Async wrapper for file_exists."""
    return minio_client.file_exists(bucket, object_name)


async def delete_file(bucket: str, object_name: str) -> bool:
    """Async wrapper for delete_file."""
    return minio_client.delete_file(bucket, object_name)


async def delete_files_by_prefix(bucket: str, prefix: str) -> int:
    """Async wrapper for delete_files_by_prefix."""
    return minio_client.delete_files_by_prefix(bucket, prefix)


async def list_files(bucket: str, prefix: str | None = None) -> list[str]:
    """Async wrapper for list_files."""
    return minio_client.list_files(bucket, prefix)


async def ensure_bucket() -> None:
    """Async wrapper for ensure_bucket."""
    minio_client.ensure_bucket()
