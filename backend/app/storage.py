"""MinIO storage client and helpers."""

import logging
from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error
from minio.helpers import ObjectWriteResult

from app.config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO client wrapper for document storage."""

    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket

    def ensure_bucket(self) -> None:
        """Ensure the bucket exists."""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info(f"Created bucket: {self.bucket}")

    def upload_file(self, bucket: str, object_name: str, file_data: bytes) -> ObjectWriteResult:
        """
        Upload a file to MinIO.

        Args:
            bucket: Bucket name
            object_name: Object key/path
            file_data: File content as bytes

        Returns:
            ObjectWriteResult from MinIO
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
            logger.error(f"MinIO upload error: {e}")
            raise

    def download_file(self, bucket: str, object_name: str) -> bytes:
        """
        Download a file from MinIO.

        Args:
            bucket: Bucket name
            object_name: Object key/path

        Returns:
            File content as bytes
        """
        try:
            data = self.client.get_object(bucket_name=bucket, object_name=object_name)
            content = data.read()
            data.close()
            data.release_conn()
            return content
        except S3Error as e:
            logger.error(f"MinIO download error: {e}")
            raise

    def file_exists(self, bucket: str, object_name: str) -> bool:
        """
        Check if a file exists in MinIO.

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


async def ensure_bucket() -> None:
    """Async wrapper for ensure_bucket."""
    minio_client.ensure_bucket()
