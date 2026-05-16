"""Storage abstraction layer — local filesystem or S3-compatible (R2/S3/Spaces).

Falls back to local storage when S3 is not configured, so the app always works.
"""
import logging
import os
import uuid
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

_s3_client = None


def _get_s3_client():
    """Lazy-init boto3 S3 client."""
    global _s3_client
    if _s3_client is not None:
        return _s3_client
    if not settings.S3_ENDPOINT_URL or not settings.S3_ACCESS_KEY_ID:
        return None
    try:
        import boto3
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
        )
        _s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        logger.info("S3 storage connected: %s/%s", settings.S3_ENDPOINT_URL, settings.S3_BUCKET_NAME)
    except Exception as e:
        logger.warning("S3 unavailable, falling back to local storage: %s", e)
        _s3_client = None
    return _s3_client


def _use_s3() -> bool:
    return settings.STORAGE_BACKEND == "s3" and _get_s3_client() is not None


def _generate_key(subfolder: str, original_filename: str) -> str:
    """Generate a unique object key: {subfolder}/{date}/{uuid}.{ext}"""
    ext = os.path.splitext(original_filename)[1] or ""
    date_str = datetime.utcnow().strftime("%Y/%m/%d")
    return f"{subfolder}/{date_str}/{uuid.uuid4().hex}{ext}"


async def upload_file(file_content: bytes, subfolder: str, filename: str) -> str:
    """Upload a file and return the public URL (or local path).

    Args:
        file_content: Raw bytes of the file.
        subfolder: e.g. "properties" or "imports".
        filename: Original filename (used for extension detection).

    Returns:
        Public URL (S3) or relative path (local): e.g. "/static/properties/abc.jpg"
    """
    if _use_s3():
        key = _generate_key(subfolder, filename)
        s3 = _get_s3_client()
        content_type = _guess_mime(filename)
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType=content_type,
        )
        if settings.S3_PUBLIC_URL_PREFIX:
            return f"{settings.S3_PUBLIC_URL_PREFIX.rstrip('/')}/{key}"
        return f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET_NAME}/{key}"

    # Local storage
    base_dir = os.path.abspath(os.path.join(settings.UPLOAD_DIR, "..", subfolder))
    os.makedirs(base_dir, exist_ok=True)
    file_id = uuid.uuid4().hex
    ext = os.path.splitext(filename)[1] or ""
    local_filename = f"{file_id}{ext}"
    filepath = os.path.join(base_dir, local_filename)
    with open(filepath, "wb") as f:
        f.write(file_content)
    return f"/static/{subfolder}/{local_filename}"


async def delete_file(url_or_path: str) -> bool:
    """Delete a file from storage. Returns True if successful."""
    if not url_or_path:
        return False

    if _use_s3() and (url_or_path.startswith("http") or not url_or_path.startswith("/static")):
        key = _extract_s3_key(url_or_path)
        if not key:
            return False
        try:
            s3 = _get_s3_client()
            s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
            return True
        except Exception:
            return False

    # Local storage
    try:
        local_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, "..", url_or_path.lstrip("/static/")))
        if os.path.exists(local_path):
            os.remove(local_path)
            return True
    except Exception:
        pass
    return False


def _extract_s3_key(url: str) -> str | None:
    """Extract the S3 object key from a full URL."""
    if settings.S3_PUBLIC_URL_PREFIX and url.startswith(settings.S3_PUBLIC_URL_PREFIX):
        return url[len(settings.S3_PUBLIC_URL_PREFIX.rstrip("/")) + 1:]
    prefix = f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET_NAME}/"
    if url.startswith(prefix):
        return url[len(prefix):]
    if url.startswith("http"):
        return url.split(f"/{settings.S3_BUCKET_NAME}/", 1)[-1] if f"/{settings.S3_BUCKET_NAME}/" in url else None
    return None


def _guess_mime(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
        ".pdf": "application/pdf", ".csv": "text/csv",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
    }
    return mime_map.get(ext, "application/octet-stream")
