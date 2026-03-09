"""MinIO client for object storage operations."""

import logging
from typing import List, Tuple

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
            secure=False,
        )
        # Check connection
        try:
            self._client.list_buckets()
            logger.info("✅ MinIO connection successful")
        except Exception as e:
            logger.error(f"❌ MinIO connection failed: {e}")

    @property
    def client(self) -> Minio:
        """Get the raw Minio client instance."""
        return self._client

    def batch_check_objects_exist(
        self,
        bucket_name: str,
        object_names: List[str],
    ) -> Tuple[List[str], List[str]]:
        """Check which objects exist in a MinIO bucket.

        Args:
            bucket_name: Name of the MinIO bucket.
            object_names: List of object names to check.

        Returns:
            Tuple of (existing_objects, missing_objects).
        """
        if not object_names:
            return [], []

        existing_objects = []
        missing_objects = []

        for object_name in object_names:
            try:
                self._client.stat_object(bucket_name, object_name)
                existing_objects.append(object_name)
            except Exception:
                missing_objects.append(object_name)

        return existing_objects, missing_objects

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
