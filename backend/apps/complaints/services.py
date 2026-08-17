"""
apps/complaints/services.py

Business logic for complaint submission and retrieval.

All validation and persistence coordination lives here.
Views delegate to this layer; it should never be called from templates.

Transaction strategy for complaint submission:
  1. Validate all inputs (category, location, description, attachments).
  2. Open a DB transaction.
  3. Generate complaint_number (uses DB sequence inside transaction).
  4. INSERT complaint row.
  5. INSERT complaint_status_history row (old=NULL, new='submitted').
  6. INSERT complaint_attachment rows for any uploaded files.
  7. COMMIT transaction.
  8. Upload binary files to Supabase Storage AFTER commit (out-of-band).
  9. If any Storage upload fails, delete the attachment DB record
     (compensating action — logged for audit).

This ensures the DB is always consistent. Storage may lag briefly, which
is acceptable and documentable.
"""

import uuid
import logging
from datetime import datetime, timezone

from django.db import transaction, connection

from apps.complaints.models import (
    Complaint,
    ComplaintCategory,
    ComplaintAttachment,
    ComplaintStatusHistory,
    ComplaintStatus,
    AttachmentPurpose,
    AttachmentFileType,
)
from apps.complaints.number import generate_complaint_number
from apps.complaints.storage import (
    build_storage_path,
    validate_upload,
    upload_to_storage,
    delete_from_storage,
    detect_file_type,
)
from apps.users.models import Profile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

LAT_MIN, LAT_MAX = -90.0, 90.0
LNG_MIN, LNG_MAX = -180.0, 180.0


def validate_location(lat, lng) -> list[str]:
    errors = []
    try:
        lat_f = float(lat)
        if not (LAT_MIN <= lat_f <= LAT_MAX):
            errors.append(f'latitude must be between {LAT_MIN} and {LAT_MAX}.')
    except (TypeError, ValueError):
        errors.append('latitude must be a valid number.')
    try:
        lng_f = float(lng)
        if not (LNG_MIN <= lng_f <= LNG_MAX):
            errors.append(f'longitude must be between {LNG_MIN} and {LNG_MAX}.')
    except (TypeError, ValueError):
        errors.append('longitude must be a valid number.')
    return errors


def validate_category(category_id) -> tuple[ComplaintCategory | None, list[str]]:
    """Returns (category, errors). category is None when invalid."""
    if not category_id:
        return None, ['category_id is required.']
    try:
        cat = ComplaintCategory.objects.get(id=category_id)
    except ComplaintCategory.DoesNotExist:
        return None, [f'Category {category_id} does not exist.']
    if not cat.is_active:
        return None, [f'Category "{cat.name}" is not currently accepting complaints.']
    return cat, []


def validate_submission_data(data: dict, uploaded_files: list) -> list[str]:
    """
    Full submission validation. Returns a list of error strings.
    An empty list means the data is valid.
    """
    errors = []

    # Description
    description = (data.get('description') or '').strip()
    if not description:
        errors.append('description is required and cannot be empty.')

    # Category
    cat, cat_errors = validate_category(data.get('category_id'))
    errors.extend(cat_errors)

    # Location
    errors.extend(validate_location(data.get('latitude'), data.get('longitude')))

    # Attachment requirement
    if cat and cat.requires_attachment and not uploaded_files:
        errors.append(
            f'Category "{cat.name}" requires at least one attachment (photo, video, or document).'
        )

    return errors


# ---------------------------------------------------------------------------
# Attachment data class
# ---------------------------------------------------------------------------

class PendingAttachment:
    """
    Holds validated attachment data before it is persisted to the DB.
    """
    __slots__ = ('file_bytes', 'mime_type', 'file_type', 'original_name', 'size_bytes')

    def __init__(self, file_bytes: bytes, mime_type: str, file_type: str,
                 original_name: str, size_bytes: int):
        self.file_bytes = file_bytes
        self.mime_type = mime_type
        self.file_type = file_type
        self.original_name = original_name
        self.size_bytes = size_bytes


def validate_attachments(uploaded_files) -> tuple[list[PendingAttachment], list[str]]:
    """
    Validates a list of uploaded file objects (Django InMemoryUploadedFile or
    TemporaryUploadedFile).

    Returns (pending_attachments, errors).
    """
    pending = []
    errors = []
    for f in (uploaded_files or []):
        mime = f.content_type or 'application/octet-stream'
        file_type = detect_file_type(mime)
        if not file_type:
            errors.append(
                f'File "{f.name}" has unsupported MIME type "{mime}". '
                'Accepted types: photo (JPEG/PNG/WebP), video (MP4/MOV), document (PDF/DOCX/TXT).'
            )
            continue
        size = f.size
        upload_errors = validate_upload(file_type, mime, size)
        if upload_errors:
            errors.extend(upload_errors)
            continue
        pending.append(PendingAttachment(
            file_bytes=f.read(),
            mime_type=mime,
            file_type=file_type,
            original_name=f.name,
            size_bytes=size,
        ))
    return pending, errors


# ---------------------------------------------------------------------------
# Core submission service
# ---------------------------------------------------------------------------

@transaction.atomic
def _create_complaint_in_db(
    citizen: Profile,
    category: ComplaintCategory,
    description: str,
    latitude: float,
    longitude: float,
    location_address: str,
    inconvenience_details: str,
    expected_solution: str,
    attachment_paths: list[tuple[str, str, str]],  # (storage_path, file_type, mime_type)
) -> Complaint:
    """
    Atomically creates:
      1. A Complaint row (status=submitted, complaint_number generated).
      2. A ComplaintStatusHistory row.
      3. ComplaintAttachment rows (Storage upload happens outside this fn).

    The location geography point is constructed with a raw SQL INSERT so that
    we avoid requiring GeoDjango/GDAL just for this query.
    """
    now = datetime.now(timezone.utc)
    complaint_id = uuid.uuid4()
    complaint_number = generate_complaint_number()

    # Build WKT representation for the location text field at the model level.
    location_wkt = f'POINT({longitude} {latitude})'

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO complaints (
                id, complaint_number, citizen_id, category_id, description,
                location, location_lat, location_lng, location_address,
                inconvenience_details, expected_solution,
                status, reporter_count, submitted_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s
            )
            """,
            [
                str(complaint_id), complaint_number, str(citizen.id),
                int(category.id), description,
                float(longitude), float(latitude),  # ST_MakePoint(lng, lat)
                float(latitude), float(longitude), location_address or '',
                inconvenience_details or '', expected_solution or '',
                ComplaintStatus.SUBMITTED, 1, now, now,
            ],
        )

        # Initial status history record
        history_id = uuid.uuid4()
        cursor.execute(
            """
            INSERT INTO complaint_status_history (
                id, complaint_id, old_status, new_status,
                changed_by, change_reason, changed_at
            ) VALUES (%s, %s, NULL, %s, %s, %s, %s)
            """,
            [
                str(history_id), str(complaint_id),
                ComplaintStatus.SUBMITTED,
                str(citizen.id), 'Complaint submitted by citizen.', now,
            ],
        )

        # Attachment rows (files uploaded after commit)
        for storage_path, file_type, mime_type in attachment_paths:
            att_id = uuid.uuid4()
            cursor.execute(
                """
                INSERT INTO complaint_attachments (
                    id, complaint_id, file_path, file_type, mime_type,
                    purpose, uploaded_by, uploaded_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(att_id), str(complaint_id),
                    storage_path, file_type, mime_type,
                    AttachmentPurpose.SUBMISSION_EVIDENCE, str(citizen.id), now,
                ],
            )

    # Reload via ORM for the response serializer
    complaint = Complaint.objects.select_related('category', 'citizen__role').get(
        id=complaint_id
    )
    complaint._location_wkt = location_wkt  # stash for serializer
    return complaint


def submit_complaint(
    citizen: Profile,
    validated_data: dict,
    pending_attachments: list[PendingAttachment],
) -> Complaint:
    """
    High-level entry point for complaint submission.

    1. Build storage paths for each attachment.
    2. Create DB records atomically.
    3. Upload files to Supabase Storage (post-commit, compensating rollback on failure).
    4. Return the created Complaint.
    """
    category = validated_data['category']
    lat = float(validated_data['latitude'])
    lng = float(validated_data['longitude'])
    complaint_id_hint = str(uuid.uuid4())

    # Pre-build storage paths before the DB transaction
    attachment_paths = []
    attachment_bytes_map = {}  # storage_path → (bytes, mime_type)
    for att in pending_attachments:
        path = build_storage_path(complaint_id_hint, 'submission_evidence', att.original_name)
        attachment_paths.append((path, att.file_type, att.mime_type))
        attachment_bytes_map[path] = (att.file_bytes, att.mime_type)

    # Atomic DB write
    complaint = _create_complaint_in_db(
        citizen=citizen,
        category=category,
        description=validated_data['description'].strip(),
        latitude=lat,
        longitude=lng,
        location_address=validated_data.get('location_address', ''),
        inconvenience_details=validated_data.get('inconvenience_details', ''),
        expected_solution=validated_data.get('expected_solution', ''),
        attachment_paths=attachment_paths,
    )

    # Post-commit: upload to Supabase Storage
    failed_paths = []
    for path, (file_bytes, mime_type) in attachment_bytes_map.items():
        try:
            ok = upload_to_storage(path, file_bytes, mime_type)
            if not ok:
                failed_paths.append(path)
                logger.error('Storage upload failed for path: %s', path)
        except RuntimeError as exc:
            # SUPABASE_URL/SERVICE_ROLE_KEY not configured — skip uploads in dev.
            logger.warning('Storage not configured (%s). Skipping upload for %s.', exc, path)

    # Compensating: remove DB records for files that failed to upload
    if failed_paths:
        ComplaintAttachment.objects.filter(
            complaint_id=complaint.id,
            file_path__in=failed_paths,
        ).delete()
        logger.warning(
            '%d attachment(s) removed from DB after Storage upload failure for complaint %s.',
            len(failed_paths), complaint.complaint_number,
        )

    return complaint
