"""MinIO client for object storage operations."""

import io
import logging
from datetime import timedelta

from minio import Minio

from core.config import settings

logger = logging.getLogger(__name__)


class MinioClient:
    """Client class for MinIO object storage operations."""

    def __init__(self):
        self._client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

    @property
    def client(self) -> Minio:
        """Get the raw Minio client instance."""
        return self._client

    def ensure_bucket_exists(self, bucket_name: str) -> None:
        """Create the MinIO bucket if it doesn't exist.

        Args:
            bucket_name: Name of the bucket.
        """
        if not self._client.bucket_exists(bucket_name):
            self._client.make_bucket(bucket_name)
            logger.info(f"Created bucket: {bucket_name}")

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to MinIO.

        Args:
            bucket_name: Name of the bucket.
            object_name: Object key/name.
            data: File content as bytes.
            content_type: MIME type of the file.

        Returns:
            The object name.
        """
        self.ensure_bucket_exists(bucket_name)
        self._client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        logger.info(f"Uploaded {object_name} to {bucket_name}")
        return object_name

    def generate_presigned_put_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """Generate a presigned PUT URL for direct upload.

        Args:
            bucket_name: Name of the bucket.
            object_name: Object key/name.
            expires: URL expiration time in seconds.

        Returns:
            Presigned URL string.
        """
        self.ensure_bucket_exists(bucket_name)
        url = self._client.presigned_put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            expires=timedelta(seconds=expires),
        )
        logger.info(f"Generated presigned PUT URL for {bucket_name}/{object_name}")
        return url

    def get_object_bytes(self, bucket_name: str, object_name: str) -> bytes:
        """Download an object from MinIO.

        Args:
            bucket_name: Name of the bucket.
            object_name: Object key/name.

        Returns:
            Object content as bytes.
        """
        response = self._client.get_object(bucket_name, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return data


# Singleton instance
minio_client = MinioClient()
