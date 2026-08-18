"""
apps/complaints/verification.py

Ground-Level Employee Verification Service (Phase 5).

Implements on-site verification workflows according to User Stories and database_schema.md:
  - Employee verifies complaint: ASSIGNED -> VERIFIED -> IN_PROGRESS or ASSIGNED -> INVALID -> CLOSED.
  - Strict assignment-based access: complaint.assigned_employee_id == authenticated_user.id.
  - Creates immutable verification records in complaint_verifications.
  - Records atomic status transitions in complaint_status_history.
  - Handles verification evidence attachments via Supabase Storage.
  - Generates citizen and department verification notifications.
"""

import uuid
import logging
from datetime import datetime, timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ComplaintVerification,
    VerificationResultType,
    ComplaintStatusHistory,
    ComplaintAttachment,
    AttachmentPurpose,
    Notification,
    NotificationEventType,
    NotificationChannelType,
)
from apps.complaints.storage import (
    build_storage_path,
    upload_to_storage,
)
from apps.users.models import Profile, Role

logger = logging.getLogger(__name__)


def validate_employee_can_verify(employee: Profile, complaint: Complaint) -> None:
    """
    Validates that the authenticated user is an active Ground-Level Employee
    assigned to the specific complaint.
    """
    if not employee or employee.role_name != Role.GROUND_LEVEL_EMPLOYEE:
        raise ValidationError('Only Ground-Level Employees can submit verification for this complaint.')

    if employee.account_status != Profile.ACCOUNT_STATUS_ACTIVE:
        raise ValidationError('Inactive employees cannot perform verification.')

    if not complaint.assigned_employee_id or str(complaint.assigned_employee_id) != str(employee.id):
        raise ValidationError('You can only verify complaints specifically assigned to you.')

    if complaint.status != ComplaintStatus.ASSIGNED:
        raise ValidationError(
            f'Complaint must be in ASSIGNED status to be verified (current status: {complaint.status}).'
        )

    if ComplaintVerification.objects.filter(complaint_id=complaint.id).exists():
        raise ValidationError('This complaint has already been verified.')


def verify_complaint(
    employee: Profile,
    complaint: Complaint,
    verification_result: str,
    verification_remarks: str,
    site_inspection_notes: str = '',
    pending_attachments: list = None,
) -> tuple[ComplaintVerification, Complaint]:
    """
    Submits a verification decision for an assigned complaint.

    Valid outcomes:
      - 'verified' -> Transitions ASSIGNED -> VERIFIED -> IN_PROGRESS
      - 'invalid'  -> Transitions ASSIGNED -> INVALID -> CLOSED

    Atomic workflow:
      1. Validate employee and complaint state.
      2. Insert complaint_verifications record.
      3. Insert verification attachments if provided.
      4. Perform two-step status transition + status history records.
      5. Post-commit: upload evidence to Supabase Storage.
      6. Create notification for citizen and supervisor.

    Returns:
      (ComplaintVerification, Complaint)
    """
    validate_employee_can_verify(employee, complaint)

    result_cleaned = (verification_result or '').strip().lower()
    if result_cleaned not in [VerificationResultType.VERIFIED, VerificationResultType.INVALID]:
        raise ValidationError(
            f'Invalid verification result "{verification_result}". Must be "verified" or "invalid".'
        )

    remarks_cleaned = (verification_remarks or '').strip()
    if not remarks_cleaned:
        raise ValidationError('Verification remarks are mandatory and cannot be empty.')

    now = datetime.now(timezone.utc)
    pending_attachments = pending_attachments or []

    # Pre-build attachment storage paths
    attachment_records = []
    attachment_bytes_map = {}
    for att in pending_attachments:
        path = build_storage_path(str(complaint.id), 'verification_evidence', att.original_name)
        attachment_records.append((path, att.file_type, att.mime_type))
        attachment_bytes_map[path] = (att.file_bytes, att.mime_type)

    with transaction.atomic():
        # 1. Create verification record
        verification = ComplaintVerification.objects.create(
            id=uuid.uuid4(),
            complaint=complaint,
            verified_by=employee,
            site_inspection_notes=site_inspection_notes.strip() if site_inspection_notes else None,
            verification_result=result_cleaned,
            verification_remarks=remarks_cleaned,
            verified_at=now,
        )

        # 2. Insert attachment DB records
        for storage_path, file_type, mime_type in attachment_records:
            ComplaintAttachment.objects.create(
                id=uuid.uuid4(),
                complaint=complaint,
                file_path=storage_path,
                file_type=file_type,
                mime_type=mime_type,
                purpose=AttachmentPurpose.VERIFICATION_EVIDENCE,
                uploaded_by=employee,
                uploaded_at=now,
            )

        # 3. Status progression
        if result_cleaned == VerificationResultType.VERIFIED:
            # ASSIGNED -> VERIFIED (Employee action)
            complaint.status = ComplaintStatus.VERIFIED
            complaint.updated_at = now
            complaint.save(update_fields=['status', 'updated_at'])

            ComplaintStatusHistory.objects.create(
                id=uuid.uuid4(),
                complaint=complaint,
                old_status=ComplaintStatus.ASSIGNED,
                new_status=ComplaintStatus.VERIFIED,
                changed_by=employee,
                change_reason=remarks_cleaned,
                changed_at=now,
            )

        else:  # INVALID outcome
            # Step 3a: ASSIGNED -> INVALID (Employee action)
            ComplaintStatusHistory.objects.create(
                id=uuid.uuid4(),
                complaint=complaint,
                old_status=ComplaintStatus.ASSIGNED,
                new_status=ComplaintStatus.INVALID,
                changed_by=employee,
                change_reason=remarks_cleaned,
                changed_at=now,
            )

            # Step 3b: INVALID -> CLOSED (System closure)
            complaint.status = ComplaintStatus.CLOSED
            complaint.updated_at = now
            complaint.save(update_fields=['status', 'updated_at'])

            ComplaintStatusHistory.objects.create(
                id=uuid.uuid4(),
                complaint=complaint,
                old_status=ComplaintStatus.INVALID,
                new_status=ComplaintStatus.CLOSED,
                changed_by=None,  # Automated system closure
                change_reason='Automatically closed due to invalid verification.',
                changed_at=now,
            )

        # 4. Create Notification for the Citizen
        notifications_to_create = [
            Notification(
                id=uuid.uuid4(),
                recipient_id=complaint.citizen_id,
                complaint_id=complaint.id,
                trigger_event=NotificationEventType.VERIFICATION,
                channel=NotificationChannelType.IN_APP,
                message_content=(
                    f'Your complaint {complaint.complaint_number} has been verified as '
                    f'{result_cleaned.upper()}. Remarks: {remarks_cleaned}'
                ),
                created_at=now,
            )
        ]

        # 5. Notify Department Supervisor if assigned
        supervisors = Profile.objects.filter(
            department_id=complaint.assigned_department_id,
            role__role_name=Role.SUPERVISOR,
            account_status=Profile.ACCOUNT_STATUS_ACTIVE,
        )
        for supervisor in supervisors:
            notifications_to_create.append(
                Notification(
                    id=uuid.uuid4(),
                    recipient_id=supervisor.id,
                    complaint_id=complaint.id,
                    trigger_event=NotificationEventType.VERIFICATION,
                    channel=NotificationChannelType.IN_APP,
                    message_content=(
                        f'Complaint {complaint.complaint_number} verified as {result_cleaned.upper()} '
                        f'by {employee.full_name}.'
                    ),
                    created_at=now,
                )
            )

        Notification.objects.bulk_create(notifications_to_create)

        from apps.users.audit_logger import log_audit_event
        log_audit_event(
            actor=employee,
            action="verify_complaint",
            entity_type="Complaint",
            entity_id=str(complaint.id),
            old_value={"status": ComplaintStatus.ASSIGNED},
            new_value={"status": complaint.status, "verification_result": result_cleaned}
        )

    # Post-commit: upload evidence files to Supabase Storage
    failed_paths = []
    for path, (file_bytes, mime_type) in attachment_bytes_map.items():
        try:
            ok = upload_to_storage(path, file_bytes, mime_type)
            if not ok:
                failed_paths.append(path)
                logger.error('Storage upload failed for verification evidence: %s', path)
        except RuntimeError as exc:
            logger.warning('Storage not configured (%s). Skipping upload for %s.', exc, path)

    if failed_paths:
        ComplaintAttachment.objects.filter(
            complaint_id=complaint.id,
            file_path__in=failed_paths,
        ).delete()
        logger.warning(
            '%d verification attachment(s) removed after upload failure for complaint %s.',
            len(failed_paths), complaint.complaint_number,
        )

    logger.info(
        'Complaint %s verified as %s by %s. Final status: %s',
        complaint.complaint_number, result_cleaned, employee.id, complaint.status,
    )
    return verification, complaint
