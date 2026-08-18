"""
apps/complaints/ai/service.py

ComplaintSeverityService — orchestrates the full AI severity assessment workflow.

Responsibilities:
    1. Fetch the complaint description and submission-evidence attachments from DB.
    2. Download image bytes from Supabase Storage (for photo attachments only).
    3. Call the configured SeverityProvider.
    4. Validate the result (already done inside the provider chain).
    5. INSERT a new record into complaint_classifications (never overwrite old records).
    6. UPDATE complaints.severity_level and complaints.severity_score to the latest result.
    7. If confidence < AI_CONFIDENCE_THRESHOLD, INSERT a classification_review_task.
    8. Log all failures; never propagate exceptions that could corrupt the complaint.

Security:
    - The AI does NOT directly modify complaint.status.
    - The AI does NOT modify assigned_department_id or assigned_employee_id.
    - severity_level and severity_score from client input are NEVER read here;
      only AI-produced, server-validated values are persisted.
    - The SUPABASE_SERVICE_ROLE_KEY is used ONLY for Storage image downloads
      (same usage pattern as existing storage.py). It is never exposed to clients.
    - Database writes use the standard Django ORM (authenticated server-side).

Background Execution:
    This service is called from a Python threading.Thread launched after
    complaint submission. The thread runs inside the same process but
    independently of the HTTP request lifecycle.

    WHY threading.Thread (not Celery/Redis/Django-Q):
    - The project has no message broker or worker infrastructure (requirements.txt
      contains no Celery, Redis, or Django-Q).
    - Adding a broker would introduce a significant new infrastructure dependency
      for a single feature.
    - threading.Thread is available in the standard library, requires no
      deployment changes, and is already the pattern used for out-of-band work
      in similar lightweight Django services.
    - Django ORM connections are thread-safe when using connection pooling.
      Each thread gets its own DB connection from the pool (conn_max_age=600
      is already configured in base.py).
    - Failures in the background thread are caught and logged; they do NOT
      propagate to the HTTP response or corrupt the complaint.

    KNOWN LIMITATIONS of threading.Thread:
    - If the WSGI process is killed mid-thread (e.g., gunicorn worker restart),
      the in-flight classification may be lost without retry.
    - There is no distributed task queue, so classification cannot be retried
      automatically by a separate worker.
    - For high-throughput production use, a proper task queue (Celery, etc.)
      would be preferable. This is documented as a known architectural limitation.
    - Threading does NOT provide true async I/O. It uses OS threads. For a
      Django WSGI application, this is the standard concurrency approach.

    The classification NEVER affects the HTTP 201 response returned to the citizen.
    If the thread fails, the complaint is already committed and safe.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import connection

if TYPE_CHECKING:
    from apps.complaints.ai.interfaces import SeverityProvider
    from apps.complaints.ai.schemas import SeverityResult

logger = logging.getLogger(__name__)

# Supported MIME types for inline Gemini image input.
_GEMINI_SUPPORTED_IMAGE_MIMES = {
    'image/jpeg', 'image/png', 'image/webp', 'image/gif',
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_confidence_threshold() -> float:
    """
    Returns the configured AI confidence threshold (0–100).

    Reads AI_CONFIDENCE_THRESHOLD from Django settings (set via environment
    variable AI_CONFIDENCE_THRESHOLD).

    Default: 70.0  — assessments with confidence below this are flagged for
    manual review in classification_review_tasks.

    NOTE: 70.0 is a documented application-level default, NOT an authoritative
    business rule from the database schema or user stories.
    """
    return float(getattr(settings, 'AI_CONFIDENCE_THRESHOLD', 70.0))


def _download_image_from_storage(file_path: str, mime_type: str) -> bytes | None:
    """
    Downloads a file from Supabase Storage using the service-role key.

    WHY service-role key is used here:
        - The background thread runs without an authenticated user session;
          there is no Supabase JWT to use for RLS-governed Storage access.
        - The service-role key is already used by the existing storage.py module
          for complaint media uploads (SUPABASE_SERVICE_ROLE_KEY). This is
          consistent with the existing architecture.
        - Usage is restricted exclusively to Storage object reads for the
          complaint-media bucket. It is never returned to clients or logged.
        - The key never leaves the server-side process.

    Returns:
        Raw bytes of the image, or None if download fails.
    """
    import httpx

    supabase_url = getattr(settings, 'SUPABASE_URL', None)
    service_role_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None)

    if not supabase_url or not service_role_key:
        logger.warning(
            'Supabase Storage not configured — skipping image download for AI assessment. '
            'Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in environment.'
        )
        return None

    bucket = 'complaint-media'
    url = f'{supabase_url}/storage/v1/object/{bucket}/{file_path}'
    headers = {'Authorization': f'Bearer {service_role_key}'}

    try:
        resp = httpx.get(url, headers=headers, timeout=20.0)
        if resp.status_code == 200:
            return resp.content
        logger.warning(
            'Storage image download returned HTTP %s for path %s',
            resp.status_code, file_path
        )
        return None
    except Exception as exc:
        logger.warning('Storage image download failed for %s: %s', file_path, exc)
        return None


def _fetch_image_data_for_complaint(complaint_id: str) -> list[dict]:
    """
    Fetches submission_evidence photo attachments for a complaint and
    downloads their bytes from Supabase Storage.

    Returns:
        List of dicts: [{'mime_type': str, 'data': bytes}, ...]
        Excludes any attachments that fail to download.
    """
    from apps.complaints.models import ComplaintAttachment, AttachmentPurpose, AttachmentFileType

    attachments = ComplaintAttachment.objects.filter(
        complaint_id=complaint_id,
        purpose=AttachmentPurpose.SUBMISSION_EVIDENCE,
        file_type=AttachmentFileType.PHOTO,
    ).values('file_path', 'mime_type')

    image_data = []
    for att in attachments:
        mime = att['mime_type'] or ''
        if mime not in _GEMINI_SUPPORTED_IMAGE_MIMES:
            logger.debug(
                'Skipping attachment with unsupported MIME type for AI: %s', mime
            )
            continue
        raw = _download_image_from_storage(att['file_path'], mime)
        if raw:
            image_data.append({'mime_type': mime, 'data': raw})

    return image_data


def _insert_classification_record(
    complaint_id: str,
    result: 'SeverityResult',
    model_name: str,
    now: datetime,
) -> str:
    """
    Inserts a new record into complaint_classifications.

    NEVER overwrites existing records — each AI run creates a new row.
    Returns the UUID of the newly created classification record.
    """
    classification_id = str(uuid.uuid4())
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO complaint_classifications (
                id,
                complaint_id,
                detected_category_id,
                confidence_score,
                severity_level,
                severity_score,
                model_name,
                model_version,
                is_manual_override,
                classified_by,
                classified_at
            ) VALUES (
                %s, %s, NULL, %s, %s, %s, %s, %s, FALSE, NULL, %s
            )
            """,
            [
                classification_id,
                complaint_id,
                round(result.confidence, 2),
                result.severity_level,
                round(result.severity_score, 2),
                model_name,
                'phase8-v1',           # model_version
                now,
            ],
        )
    return classification_id


def _sync_complaint_severity(
    complaint_id: str,
    result: 'SeverityResult',
    now: datetime,
    base_priority: str = None,
) -> None:
    """
    Synchronises complaints.severity_level and complaints.severity_score
    with the latest classification result, and calculates the final
    operational priority using the AI priority modifier.

    This is an UPDATE on the complaints table — it never changes status,
    assignment, or any lifecycle fields.
    """
    from apps.complaints.priority import calculate_final_priority
    final_priority = calculate_final_priority(base_priority, result.severity_level) if base_priority else None

    with connection.cursor() as cursor:
        if final_priority:
            cursor.execute(
                """
                UPDATE complaints
                   SET severity_level = %s,
                       severity_score = %s,
                       priority_category = %s,
                       updated_at     = %s
                 WHERE id = %s
                """,
                [
                    result.severity_level,
                    round(result.severity_score, 2),
                    final_priority,
                    now,
                    complaint_id,
                ],
            )
        else:
            cursor.execute(
                """
                UPDATE complaints
                   SET severity_level = %s,
                       severity_score = %s,
                       updated_at     = %s
                 WHERE id = %s
                """,
                [
                    result.severity_level,
                    round(result.severity_score, 2),
                    now,
                    complaint_id,
                ],
            )


def _create_review_task_if_needed(
    complaint_id: str,
    classification_id: str,
    confidence: float,
    threshold: float,
    now: datetime,
) -> None:
    """
    If confidence < threshold, inserts a record into classification_review_tasks
    so a human reviewer can examine the result.

    Uses the existing classification_review_tasks schema from database_schema.md.
    Does NOT create a new table.
    """
    if confidence >= threshold:
        return

    task_id = str(uuid.uuid4())
    reason = (
        f'AI confidence {confidence:.1f}% is below the configured threshold '
        f'{threshold:.1f}%. Manual review is required.'
    )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO classification_review_tasks (
                id,
                complaint_id,
                classification_id,
                assigned_to,
                reason,
                status,
                reviewed_by,
                review_remarks,
                reviewed_at,
                created_at
            ) VALUES (
                %s, %s, %s, NULL, %s, 'pending', NULL, NULL, NULL, %s
            )
            """,
            [task_id, complaint_id, classification_id, reason, now],
        )
    logger.info(
        'Low-confidence classification review task created for complaint %s '
        '(confidence=%.1f%%, threshold=%.1f%%).',
        complaint_id, confidence, threshold,
    )


# ---------------------------------------------------------------------------
# ComplaintSeverityService
# ---------------------------------------------------------------------------

class ComplaintSeverityService:
    """
    Orchestrates the full severity assessment pipeline for a complaint.

    The provider is injected, allowing tests to mock it without any real
    API calls.
    """

    def __init__(self, provider: 'SeverityProvider'):
        self.provider = provider

    def assess_complaint(self, complaint_id: str) -> None:
        """
        Run the full assessment pipeline for a given complaint.

        This method is designed to be called from a background thread.
        All exceptions are caught and logged; failures do NOT propagate
        upward or affect the complaint record in any way.

        Steps:
            1. Fetch description from DB.
            2. Fetch and download photo attachments from Storage.
            3. Call the AI provider.
            4. Insert classification record.
            5. Sync severity fields on the complaint.
            6. Create review task if confidence is below threshold.
        """
        from apps.complaints.models import Complaint

        logger.info('Starting AI severity assessment for complaint %s.', complaint_id)

        # Step 1: Fetch description and base priority
        try:
            complaint = Complaint.objects.only(
                'id', 'description', 'complaint_number', 'priority_category'
            ).get(id=complaint_id)
        except Complaint.DoesNotExist:
            logger.error(
                'AI assessment: complaint %s not found in database.', complaint_id
            )
            return
        except Exception as exc:
            logger.error(
                'AI assessment: DB error fetching complaint %s: %s', complaint_id, exc
            )
            return

        description = complaint.description or ''

        # Step 2: Fetch image data
        try:
            image_data = _fetch_image_data_for_complaint(str(complaint_id))
        except Exception as exc:
            logger.warning(
                'AI assessment: error fetching images for complaint %s: %s. '
                'Proceeding with text-only assessment.',
                complaint_id, exc,
            )
            image_data = []

        # Step 3: Call the AI provider
        from apps.complaints.ai.interfaces import SeverityProviderError
        try:
            result = self.provider.assess(
                description=description,
                image_data=image_data,
            )
        except SeverityProviderError as exc:
            logger.error(
                'AI assessment: provider failed for complaint %s: %s. '
                'Complaint is unaffected.',
                complaint_id, exc,
            )
            return
        except Exception as exc:
            logger.error(
                'AI assessment: unexpected provider error for complaint %s: %s. '
                'Complaint is unaffected.',
                complaint_id, exc,
            )
            return

        now = datetime.now(timezone.utc)
        model_name = getattr(self.provider, '_model', 'gemini-3.6-flash')
        threshold = _get_confidence_threshold()

        # Step 4: Insert classification record
        try:
            classification_id = _insert_classification_record(
                complaint_id=str(complaint_id),
                result=result,
                model_name=model_name,
                now=now,
            )
        except Exception as exc:
            logger.error(
                'AI assessment: failed to insert classification for complaint %s: %s. '
                'Complaint is unaffected.',
                complaint_id, exc,
            )
            return

        # Step 5: Sync severity and compute final operational priority
        try:
            _sync_complaint_severity(
                complaint_id=str(complaint_id),
                result=result,
                now=now,
                base_priority=complaint.priority_category,
            )
        except Exception as exc:
            logger.error(
                'AI assessment: failed to sync severity fields for complaint %s: %s. '
                'Classification record %s was saved.',
                complaint_id, exc, classification_id,
            )
            # Do not return — still attempt review task creation

        # Step 6: Create review task if confidence is low
        try:
            _create_review_task_if_needed(
                complaint_id=str(complaint_id),
                classification_id=classification_id,
                confidence=result.confidence,
                threshold=threshold,
                now=now,
            )
        except Exception as exc:
            logger.error(
                'AI assessment: failed to create review task for complaint %s: %s.',
                complaint_id, exc,
            )

        logger.info(
            'AI severity assessment complete for complaint %s: '
            'level=%s, score=%.1f, confidence=%.1f%%.',
            complaint.complaint_number,
            result.severity_level,
            result.severity_score,
            result.confidence,
        )


# ---------------------------------------------------------------------------
# Background thread entry point
# ---------------------------------------------------------------------------

def run_severity_assessment_in_background(complaint_id: str) -> None:
    """
    Launches the AI severity assessment in a daemon background thread.

    Called immediately after a complaint is committed to the database.

    The thread is a daemon thread — it will not prevent the process from
    exiting, and its lifecycle is tied to the main process.

    Failure handling:
        - Provider errors are logged (not raised).
        - DB errors are logged (not raised).
        - The complaint is NEVER deleted, corrupted, or status-changed on failure.

    Architecture note:
        This uses Python's standard threading.Thread as the background mechanism.
        See service.py module docstring for the full rationale and limitations.
    """
    import threading

    from apps.complaints.ai.providers.gemini import GeminiSeverityProvider

    provider = GeminiSeverityProvider()
    service = ComplaintSeverityService(provider=provider)

    def _run():
        # Close the inherited DB connection from the parent thread.
        # Django will open a new connection for the worker thread automatically.
        connection.close()
        try:
            service.assess_complaint(complaint_id=complaint_id)
        except Exception as exc:
            # Last-resort catch — should never reach here given internal handling.
            logger.error(
                'AI severity background thread unhandled exception for %s: %s',
                complaint_id, exc,
            )

    thread = threading.Thread(
        target=_run,
        name=f'ai-severity-{complaint_id}',
        daemon=True,
    )
    thread.start()
    logger.debug('AI severity background thread started for complaint %s.', complaint_id)
