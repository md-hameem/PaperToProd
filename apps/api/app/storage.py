"""
Storage module — Object storage integration with MinIO/S3.
"""

from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.config import settings

# Global client
client = Minio(
    endpoint=settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_use_ssl,
)

# Core buckets
PAPERS_BUCKET = "papers"
JOBS_BUCKET = "jobs"

CORE_BUCKETS = [PAPERS_BUCKET, JOBS_BUCKET]


def init_buckets() -> None:
    """Ensure all required buckets exist."""
    for bucket in CORE_BUCKETS:
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
        except S3Error as e:
            # Depending on setup, bucket might exist but we lack permissions, etc.
            # For now, just log and raise
            raise RuntimeError(f"Failed to initialize MinIO bucket '{bucket}': {e}") from e


# Async wrappers (MinIO python client is synchronous, we use thread pools in production,
# but for MVP we wrap the basic operations)


async def upload_file(
    bucket_name: str,
    object_name: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> None:
    """Upload a file to MinIO."""
    import asyncio

    def _upload():
        client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    await asyncio.to_thread(_upload)


async def get_presigned_url(bucket_name: str, object_name: str, expires_sec: int = 3600) -> str:
    """Generate a pre-signed URL for downloading."""
    import asyncio
    from datetime import timedelta

    def _get_url():
        return client.get_presigned_url(
            "GET",
            bucket_name=bucket_name,
            object_name=object_name,
            expires=timedelta(seconds=expires_sec),
        )

    return await asyncio.to_thread(_get_url)
