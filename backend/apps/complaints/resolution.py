"""
apps/complaints/resolution.py

Progress Update and Resolution Service (Phase 6).

Implements work progression and resolution according to User Stories and database_schema.md:
  - Authorized actors: Assigned Ground-Level Employee OR authorized Department Supervisor.
  - Work initiation: VERIFIED -> IN_PROGRESS (first progress update).
  - Ongoing progress updates on IN_PROGRESS (no duplicate status history rows).
  - Expected completion date tracking & deadline change notifications.
  - Final resolution submission: IN_PROGRESS -> RESOLVED.
  - Resolution proof uploads via Supabase Storage (complaint-media bucket, purpose='resolution_proof').
  - Resolution notifications to citizen and supervisor (trigger_event='resolution').
  - Strict authorization:
      * Ground-level employee: complaint.assigned_employee_id == authenticated_user.id
      * Supervisor: supervisor.department_id == complaint.assigned_department_id
"""

import uuid
import logging
from datetime import datetime, timezone, date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ClosureConfirmation,
    ComplaintResolution,
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
from apps.complaints.closure import CLOSURE_WINDOW_DAYS

logger = logging.getLogger(__name__)


def can_update_complaint_work(user: Profile, complaint: Complaint) -> bool:
    """
    Returns True if user is authorized to record progress or resolve the complaint:
      - The Ground-Level Employee assigned to this complaint, OR
      - An active Supervisor belonging to the complaint's assigned department.
    """
    if not user or user.account_status != Profile.ACCOUNT_STATUS_ACTIVE:
        return False

    if user.role_name == Role.GROUND_LEVEL_EMPLOYEE:
        return bool(
            complaint.assigned_employee_id
            and str(complaint.assigned_employee_id) == str(user.id)
        )

    if user.role_name == Role.SUPERVISOR:
        return bool(
            user.department_id
            and complaint.assigned_department_id
            and str(user.department_id) == str(complaint.assigned_department_id)
        )

    return False


def validate_user_can_update_work(user: Profile, complaint: Complaint) -> None:
    """
    Validates that the caller is authorized to record progress or resolve the complaint.
    Raises ValidationError on failure.
    """
    if not user:
        raise ValidationError('Authentication required.')

    if user.account_status != Profile.ACCOUNT_STATUS_ACTIVE:
        raise ValidationError('Inactive accounts cannot update or resolve complaints.')

    if user.role_name == Role.GROUND_LEVEL_EMPLOYEE:
        if not complaint.assigned_employee_id or str(complaint.assigned_employee_id) != str(user.id):
            raise ValidationError('You can only update or resolve complaints specifically assigned to you.')
        return

    if user.role_name == Role.SUPERVISOR:
        if not user.department_id:
            raise ValidationError('Supervisors must be assigned to a department to update complaints.')
        if not complaint.assigned_department_id or str(user.department_id) != str(complaint.assigned_department_id):
            raise ValidationError('You can only update or resolve complaints belonging to your department.')
        return

    raise ValidationError('Only the assigned Ground-Level Employee or authorized Department Supervisor can update or resolve complaints.')


def add_progress_update(
    user: Profile,
    complaint: Complaint,
    progress_update: str = '',
    remarks: str = '',
    expected_completion_date: date = None,
) -> tuple[ComplaintResolution, Complaint]:
    """
    Records an interim progress update for an assigned complaint.
    Authorized for assigned Ground-Level Employee or department Supervisor.

    Status transitions:
      - If VERIFIED: transitions VERIFIED -> IN_PROGRESS and creates 1 status history record.
      - If IN_PROGRESS: status remains IN_PROGRESS (no duplicate status history created).

    Raises:
      ValidationError: If complaint is not in VERIFIED or IN_PROGRESS status, or if progress text is missing.
    """
    validate_user_can_update_work(user, complaint)

    if complaint.status not in [ComplaintStatus.VERIFIED, ComplaintStatus.IN_PROGRESS]:
        raise ValidationError(
            f'Complaint must be in VERIFIED or IN_PROGRESS status to record progress (current status: {complaint.status}).'
        )

    progress_text = (progress_update or '').strip()
    remarks_text = (remarks or '').strip()
    if not progress_text and not remarks_text:
        raise ValidationError('Progress update details or remarks are required.')

    now = datetime.now(timezone.utc)
    old_status = complaint.status
    deadline_changed = False

    with transaction.atomic():
        # Handle deadline updates
        if expected_completion_date:
            if complaint.expected_completion_date != expected_completion_date:
                deadline_changed = True
                complaint.expected_completion_date = expected_completion_date

        # Handle VERIFIED -> IN_PROGRESS transition on first work action
        if old_status == ComplaintStatus.VERIFIED:
            complaint.status = ComplaintStatus.IN_PROGRESS
            complaint.updated_at = now
            complaint.save(update_fields=['status', 'expected_completion_date', 'updated_at'])

            ComplaintStatusHistory.objects.create(
                id=uuid.uuid4(),
                complaint=complaint,
                old_status=ComplaintStatus.VERIFIED,
                new_status=ComplaintStatus.IN_PROGRESS,
                changed_by=user,
                change_reason=progress_text or remarks_text or f'Work initiated by {user.full_name}.',
                changed_at=now,
            )
        else:
            # Already IN_PROGRESS; save any updated fields without creating duplicate status history
            complaint.updated_at = now
            complaint.save(update_fields=['expected_completion_date', 'updated_at'])

        # Record progress update entry
        resolution_record = ComplaintResolution.objects.create(
            id=uuid.uuid4(),
            complaint=complaint,
            updated_by=user,
            progress_update=progress_text or None,
            remarks=remarks_text or None,
            expected_completion_date=expected_completion_date,
            is_final_resolution=False,
            created_at=now,
        )

        # Citizen progress notification
        notifications = [
            Notification(
                id=uuid.uuid4(),
                recipient_id=complaint.citizen_id,
                complaint_id=complaint.id,
                trigger_event=NotificationEventType.STATUS_CHANGE if old_status == ComplaintStatus.VERIFIED else NotificationEventType.SUBMISSION,
                channel=NotificationChannelType.IN_APP,
                message_content=(
                    f'Progress update on complaint {complaint.complaint_number}: '
                    f'{progress_text or remarks_text}'
                ),
                created_at=now,
            )
        ]

        # Deadline alert notification if deadline changed
        if deadline_changed:
            notifications.append(
                Notification(
                    id=uuid.uuid4(),
                    recipient_id=complaint.citizen_id,
                    complaint_id=complaint.id,
                    trigger_event=NotificationEventType.DEADLINE_CHANGE,
                    channel=NotificationChannelType.IN_APP,
                    message_content=(
                        f'Expected completion date for complaint {complaint.complaint_number} '
                        f'is set to {expected_completion_date}.'
                    ),
                    created_at=now,
                )
            )

        Notification.objects.bulk_create(notifications)

    logger.info(
        'Progress update recorded for complaint %s by %s %s (Status: %s)',
        complaint.complaint_number, user.role_name, user.id, complaint.status,
    )
    return resolution_record, complaint


def resolve_complaint(
    user: Profile,
    complaint: Complaint,
    resolution_details: str,
    remarks: str = '',
    pending_attachments: list = None,
) -> tuple[ComplaintResolution, Complaint]:
    """
    Submits final resolution and proof for an active complaint.
    Authorized for assigned Ground-Level Employee or department Supervisor.

    Status transition:
      IN_PROGRESS -> RESOLVED

    Validations:
      - Complaint must be in IN_PROGRESS status (direct VERIFIED -> RESOLVED is rejected).
      - resolution_details is mandatory.
      - At least one resolution proof attachment is mandatory.

    Returns:
      (ComplaintResolution, Complaint)
    """
    validate_user_can_update_work(user, complaint)

    if complaint.status != ComplaintStatus.IN_PROGRESS:
        raise ValidationError(
            f'Complaint must be in IN_PROGRESS status to be resolved (current status: {complaint.status}). '
            'If verified, submit a progress update to start work before resolving.'
        )

    res_details_cleaned = (resolution_details or '').strip()
    if not res_details_cleaned:
        raise ValidationError('Resolution details are mandatory before marking a complaint as resolved.')

    pending_attachments = pending_attachments or []
    if not pending_attachments:
        raise ValidationError('Resolution proof (at least one photo or document) is mandatory to resolve a complaint.')

    now = datetime.now(timezone.utc)
    old_status = complaint.status

    # Pre-build storage paths
    attachment_records = []
    attachment_bytes_map = {}
    primary_proof_path = None

    for att in pending_attachments:
        path = build_storage_path(str(complaint.id), 'resolution_proof', att.original_name)
        if not primary_proof_path:
            primary_proof_path = path
        attachment_records.append((path, att.file_type, att.mime_type))
        attachment_bytes_map[path] = (att.file_bytes, att.mime_type)

    with transaction.atomic():
        # 1. Update complaint status to RESOLVED and set closure confirmation window
        complaint.status = ComplaintStatus.RESOLVED
        complaint.closure_confirmation = ClosureConfirmation.PENDING
        complaint.closure_due_at = now + timedelta(days=CLOSURE_WINDOW_DAYS)
        complaint.updated_at = now
        complaint.save(update_fields=['status', 'closure_confirmation', 'closure_due_at', 'updated_at'])

        # 2. Record status history (IN_PROGRESS -> RESOLVED)
        ComplaintStatusHistory.objects.create(
            id=uuid.uuid4(),
            complaint=complaint,
            old_status=old_status,
            new_status=ComplaintStatus.RESOLVED,
            changed_by=user,
            change_reason=res_details_cleaned,
            changed_at=now,
        )

        # 3. Create attachment DB records
        for storage_path, file_type, mime_type in attachment_records:
            ComplaintAttachment.objects.create(
                id=uuid.uuid4(),
                complaint=complaint,
                file_path=storage_path,
                file_type=file_type,
                mime_type=mime_type,
                purpose=AttachmentPurpose.RESOLUTION_PROOF,
                uploaded_by=user,
                uploaded_at=now,
            )

        # 4. Insert final ComplaintResolution record
        resolution = ComplaintResolution.objects.create(
            id=uuid.uuid4(),
            complaint=complaint,
            updated_by=user,
            resolution_details=res_details_cleaned,
            remarks=remarks.strip() if remarks else None,
            resolution_proof_url=primary_proof_path,
            is_final_resolution=True,
            created_at=now,
        )

        # 5. Create Notification for the Citizen
        notifications = [
            Notification(
                id=uuid.uuid4(),
                recipient_id=complaint.citizen_id,
                complaint_id=complaint.id,
                trigger_event=NotificationEventType.RESOLUTION,
                channel=NotificationChannelType.IN_APP,
                message_content=(
                    f'Your complaint {complaint.complaint_number} has been marked as RESOLVED. '
                    f'Resolution: {res_details_cleaned}'
                ),
                created_at=now,
            )
        ]

        # 6. Notify Department Supervisor (if not the actor)
        supervisors = Profile.objects.filter(
            department_id=complaint.assigned_department_id,
            role__role_name=Role.SUPERVISOR,
            account_status=Profile.ACCOUNT_STATUS_ACTIVE,
        )
        for supervisor in supervisors:
            if str(supervisor.id) != str(user.id):
                notifications.append(
                    Notification(
                        id=uuid.uuid4(),
                        recipient_id=supervisor.id,
                        complaint_id=complaint.id,
                        trigger_event=NotificationEventType.RESOLUTION,
                        channel=NotificationChannelType.IN_APP,
                        message_content=(
                            f'Complaint {complaint.complaint_number} was resolved by {user.full_name}.'
                        ),
                        created_at=now,
                    )
                )

        Notification.objects.bulk_create(notifications)

    # Post-commit: upload resolution proof files to Supabase Storage
    failed_paths = []
    for path, (file_bytes, mime_type) in attachment_bytes_map.items():
        try:
            ok = upload_to_storage(path, file_bytes, mime_type)
            if not ok:
                failed_paths.append(path)
                logger.error('Storage upload failed for resolution proof: %s', path)
        except RuntimeError as exc:
            logger.warning('Storage not configured (%s). Skipping upload for %s.', exc, path)

    if failed_paths:
        ComplaintAttachment.objects.filter(
            complaint_id=complaint.id,
            file_path__in=failed_paths,
        ).delete()
        logger.warning(
            '%d resolution attachment(s) removed after upload failure for complaint %s.',
            len(failed_paths), complaint.complaint_number,
        )

    logger.info(
        'Complaint %s resolved by %s %s. Final status: %s',
        complaint.complaint_number, user.role_name, user.id, complaint.status,
    )
    return resolution, complaint
