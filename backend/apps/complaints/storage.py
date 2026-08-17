"""
apps/complaints/storage.py

Supabase Storage integration for complaint media.

Architecture:
  - Files are uploaded to the 'complaint-media' Supabase Storage bucket.
  - Django controls the upload path and returns the Storage object path.
  - The path is stored in complaint_attachments.file_path.
  - Binary files are NEVER stored in PostgreSQL.
  - The Supabase service-role key is used server-side only — it is never
    exposed to React.

Storage path structure:
  complaints/{complaint_id}/submission/{filename}

Consistency strategy:
  1. The complaint and attachment DB records are created inside a transaction.
  2. The Storage upload happens AFTER the transaction commits.
  3. If the upload fails, the attachment DB record is deleted (compensating).
  4. This is an eventual-consistency approach. A more robust solution
     (e.g., marking attachments as 'pending' until upload confirms) can be
     added in a future hardening phase.

File size limits (configurable via settings):
  - COMPLAINT_MAX_PHOTO_MB  = 10  (10 MB per photo)
  - COMPLAINT_MAX_VIDEO_MB  = 100 (100 MB per video)
  - COMPLAINT_MAX_DOC_MB    = 20  (20 MB per document)
  These are documented here so they can be tuned without a schema change.
"""

import os
import uuid
import mimetypes
import httpx
from django.conf import settings


# ---------------------------------------------------------------------------
# Allowed MIME types per file_type
# ---------------------------------------------------------------------------

ALLOWED_MIME_TYPES = {
    'photo': {
        'image/jpeg', 'image/png', 'image/webp', 'image/gif',
    },
    'video': {
        'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm',
    },
    'document': {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
    },
}

# Max sizes in bytes
MAX_FILE_SIZE = {
    'photo':    getattr(settings, 'COMPLAINT_MAX_PHOTO_MB', 10) * 1024 * 1024,
    'video':    getattr(settings, 'COMPLAINT_MAX_VIDEO_MB', 100) * 1024 * 1024,
    'document': getattr(settings, 'COMPLAINT_MAX_DOC_MB', 20) * 1024 * 1024,
}

STORAGE_BUCKET = 'complaint-media'


def build_storage_path(complaint_id: str, purpose: str, original_filename: str) -> str:
    """
    Returns the canonical Storage object path for a complaint attachment.

    Example:
      complaints/3f2a.../submission/abc123_photo.jpg
    """
    ext = os.path.splitext(original_filename)[1].lower()
    unique_name = f'{uuid.uuid4().hex}{ext}'
    # purpose maps to: submission, verification, resolution
    folder_map = {
        'submission_evidence': 'submission',
        'verification_evidence': 'verification',
        'resolution_proof': 'resolution',
    }
    folder = folder_map.get(purpose, 'submission')
    return f'complaints/{complaint_id}/{folder}/{unique_name}'


def detect_file_type(mime_type: str) -> str | None:
    """
    Infers the file_type (photo/video/document) from a MIME type.
    Returns None if unrecognised.
    """
    for file_type, mimes in ALLOWED_MIME_TYPES.items():
        if mime_type in mimes:
            return file_type
    return None


def validate_upload(file_type: str, mime_type: str, size_bytes: int) -> list[str]:
    """
    Returns a list of validation error strings (empty = valid).
    Called before uploading to Storage.
    """
    errors = []
    allowed = ALLOWED_MIME_TYPES.get(file_type, set())
    if mime_type not in allowed:
        errors.append(
            f'MIME type "{mime_type}" is not allowed for file_type "{file_type}". '
            f'Allowed: {sorted(allowed)}'
        )
    max_bytes = MAX_FILE_SIZE.get(file_type, 0)
    if size_bytes > max_bytes:
        errors.append(
            f'File size {size_bytes} bytes exceeds the {max_bytes // (1024*1024)} MB '
            f'limit for {file_type}.'
        )
    return errors


def upload_to_storage(storage_path: str, file_bytes: bytes, mime_type: str) -> bool:
    """
    Uploads file_bytes to Supabase Storage at storage_path.

    Returns True on success, False on failure.

    Uses the service-role key (server-side only — never exposed to React).
    If SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY are not configured, raises
    RuntimeError (deployment configuration error).
    """
    supabase_url = getattr(settings, 'SUPABASE_URL', None)
    service_role_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None)

    if not supabase_url or not service_role_key:
        raise RuntimeError(
            'SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured '
            'to upload to Supabase Storage.'
        )

    upload_url = (
        f'{supabase_url}/storage/v1/object/{STORAGE_BUCKET}/{storage_path}'
    )
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': mime_type,
    }
    try:
        response = httpx.post(upload_url, content=file_bytes, headers=headers, timeout=30)
        return response.status_code in (200, 201)
    except httpx.RequestError:
        return False


def delete_from_storage(storage_path: str) -> bool:
    """
    Deletes a file from Supabase Storage (used for compensating rollback).
    Returns True on success.
    """
    supabase_url = getattr(settings, 'SUPABASE_URL', None)
    service_role_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None)
    if not supabase_url or not service_role_key:
        return False

    delete_url = (
        f'{supabase_url}/storage/v1/object/{STORAGE_BUCKET}/{storage_path}'
    )
    headers = {'Authorization': f'Bearer {service_role_key}'}
    try:
        response = httpx.delete(delete_url, headers=headers, timeout=10)
        return response.status_code in (200, 204)
    except httpx.RequestError:
        return False
