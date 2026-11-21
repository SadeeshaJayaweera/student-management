"""
NSBM EduSphere — Document & Media Storage Engine
Enterprise file storage provider with anti-traversal validation, MIME allowlists,
cryptographic SHA-256 integrity verification, and secure lifecycle handling.
"""
import os
import re
import uuid
import hashlib
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status

# Allowed MIME types and their safe extension mapping
ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "application/zip": ".zip",
    "video/mp4": ".mp4"
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB default max upload


def sanitize_filename(filename: str) -> str:
    """Removes path separators, null bytes, and dangerous characters from filenames"""
    cleaned = os.path.basename(filename)
    cleaned = re.sub(r'[\0/\\?%*:|"<>]', '', cleaned)
    cleaned = cleaned.strip()
    return cleaned or "document"


class StorageService:
    def __init__(self, base_dir: str = "uploads/media"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def validate_file(self, upload_file: UploadFile) -> Tuple[str, str]:
        """Validates MIME type against allowlist and returns sanitized filename and extension"""
        original_name = sanitize_filename(upload_file.filename or "upload.bin")
        content_type = (upload_file.content_type or "").lower().split(";")[0].strip()

        if content_type not in ALLOWED_MIME_TYPES:
            # Fallback check by extension if generic application/octet-stream
            ext = os.path.splitext(original_name)[1].lower()
            matching = [mime for mime, safe_ext in ALLOWED_MIME_TYPES.items() if safe_ext == ext]
            if matching:
                content_type = matching[0]
            else:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Unsupported media type: '{content_type}'. Permitted formats: PDF, DOCX, XLSX, PPTX, TXT, CSV, PNG, JPG, WEBP, ZIP, MP4."
                )

        return original_name, content_type

    async def save_file(self, upload_file: UploadFile) -> Tuple[str, str, int, str]:
        """
        Streams file to storage directory, calculates SHA-256 hash, and verifies size.
        Returns (relative_storage_path, original_filename, size_bytes, sha256_hash).
        """
        original_name, content_type = self.validate_file(upload_file)
        ext = ALLOWED_MIME_TYPES.get(content_type, os.path.splitext(original_name)[1] or ".bin")

        unique_filename = f"{uuid.uuid4().hex}{ext}"
        storage_path = os.path.join(self.base_dir, unique_filename)

        hasher = hashlib.sha256()
        total_bytes = 0

        try:
            with open(storage_path, "wb") as f:
                while True:
                    chunk = await upload_file.read(64 * 1024)  # 64 KB chunks
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    if total_bytes > MAX_FILE_SIZE_BYTES:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum upload limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
                        )
                    hasher.update(chunk)
                    f.write(chunk)
        except Exception:
            if os.path.exists(storage_path):
                os.remove(storage_path)
            raise

        sha256_hash = hasher.hexdigest()
        return storage_path, original_name, total_bytes, sha256_hash

    def delete_file(self, storage_path: str) -> bool:
        """Deletes file from storage directory safely"""
        if storage_path and os.path.exists(storage_path):
            # Ensure path is within base_dir to avoid arbitrary file deletion
            real_base = os.path.realpath(self.base_dir)
            real_target = os.path.realpath(storage_path)
            if real_target.startswith(real_base):
                try:
                    os.remove(real_target)
                    return True
                except OSError:
                    return False
        return False


storage_service = StorageService()
