"""
apps/complaints/closure.py

Citizen Confirmation, Rejection, and Auto-Closure Service (Phase 7).

Rules extracted from User Stories and database_schema.md:
  1. Citizen Confirmation:
     - Allowed ONLY for the citizen who submitted the complaint (complaint.citizen_id == citizen.id).
     - Complaint must be in RESOLVED status.
     - Transitions RESOLVED -> CLOSED.
     - Sets closure_confirmation = 'confirmed'.
     - Creates status history record (changed_by = citizen.id).
     - Notifies assigned employee and department supervisor (trigger_event = 'closure').
  2. Citizen Rejection (Unsatisfactory resolution):
     - Allowed ONLY for the citizen who submitted the complaint.
     - Complaint must be in RESOLVED status with pending confirmation.
     - Rejection feedback/reason is mandatory.
     - Transitions RESOLVED -> IN_PROGRESS.
     - Sets closure_confirmation = 'rejected', clears closure_due_at.
     - Creates status history record (changed_by = citizen.id, change_reason = rejection_reason).
     - Notifies assigned employee and supervisor (trigger_event = 'status_change').
  3. Auto-Closure:
     - When resolution is submitted, a closure window (default 7 days) is set (closure_due_at).
     - Expired resolved complaints with pending confirmation are automatically transitioned to CLOSED.
     - Sets closure_confirmation = 'auto_closed'.
     - Creates status history record (changed_by = None / System).
     - Notifies citizen (trigger_event = 'closure').
  4. Post-Closure Finality:
     - Complaints in CLOSED status are terminal in the core lifecycle and cannot be directly reopened.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ClosureConfirmation,
    ComplaintStatusHistory,
    Notification,
    NotificationEventType,
    NotificationChannelType,
)
from apps.users.models import Profile, Role

logger = logging.getLogger(__name__)

# Default closure window in days before auto-closing a resolved complaint
CLOSURE_WINDOW_DAYS = getattr(settings, 'COMPLAINT_CLOSURE_WINDOW_DAYS', 7)


def validate_citizen_owns_complaint(citizen: Profile, complaint: Complaint) -> None:
    """
    Validates that the caller is an active Citizen who submitted the complaint.
    """
    if not citizen or citizen.role_name != Role.CITIZEN:
        raise ValidationError('Only Citizens can confirm or reject complaint resolutions.')

    if citizen.account_status != Profile.ACCOUNT_STATUS_ACTIVE:
        raise ValidationError('Inactive citizen accounts cannot confirm or reject complaints.')

    if str(complaint.citizen_id) != str(citizen.id):
        raise ValidationError('You can only confirm or reject resolutions for your own complaints.')


def confirm_resolution(
    citizen: Profile,
    complaint: Complaint,
    confirmation_remarks: str = '',
) -> Complaint:
    """
    Citizen confirms resolution of a complaint.

    Status transition:
      RESOLVED -> CLOSED
      closure_confirmation -> confirmed

    Raises:
      ValidationError: If not caller's complaint, or if complaint is not in RESOLVED status.
    """
    validate_citizen_owns_complaint(citizen, complaint)

    if complaint.status != ComplaintStatus.RESOLVED:
        raise ValidationError(
            f'Only complaints in RESOLVED status can be confirmed (current status: {complaint.status}).'
        )

    now = datetime.now(timezone.utc)
    remarks_cleaned = (confirmation_remarks or '').strip()

    with transaction.atomic():
        complaint.status = ComplaintStatus.CLOSED
        complaint.closure_confirmation = ClosureConfirmation.CONFIRMED
        complaint.updated_at = now
        complaint.save(update_fields=['status', 'closure_confirmation', 'updated_at'])

        ComplaintStatusHistory.objects.create(
            id=uuid.uuid4(),
            complaint=complaint,
            old_status=ComplaintStatus.RESOLVED,
            new_status=ComplaintStatus.CLOSED,
            changed_by=citizen,
            change_reason=remarks_cleaned or 'Resolution confirmed by citizen.',
            changed_at=now,
        )

        notifications = []
        # Notify assigned employee
        if complaint.assigned_employee_id:
            notifications.append(
                Notification(
                    id=uuid.uuid4(),
                    recipient_id=complaint.assigned_employee_id,
                    complaint_id=complaint.id,
                    trigger_event=NotificationEventType.CLOSURE,
                    channel=NotificationChannelType.IN_APP,
                    message_content=(
                        f'Citizen confirmed resolution of complaint {complaint.complaint_number}. '
                        'The complaint is now CLOSED.'
                    ),
                    created_at=now,
                )
            )

        # Notify department supervisor
        if complaint.assigned_department_id:
            supervisors = Profile.objects.filter(
                department_id=complaint.assigned_department_id,
                role__role_name=Role.SUPERVISOR,
                account_status=Profile.ACCOUNT_STATUS_ACTIVE,
            )
            for supervisor in supervisors:
                notifications.append(
                    Notification(
                        id=uuid.uuid4(),
                        recipient_id=supervisor.id,
                        complaint_id=complaint.id,
                        trigger_event=NotificationEventType.CLOSURE,
                        channel=NotificationChannelType.IN_APP,
                        message_content=(
                            f'Complaint {complaint.complaint_number} was confirmed and closed by citizen.'
                        ),
                        created_at=now,
                    )
                )

        if notifications:
            Notification.objects.bulk_create(notifications)

    logger.info(
        'Complaint %s confirmed and closed by citizen %s.',
        complaint.complaint_number, citizen.id,
    )
    return complaint


def reject_resolution(
    citizen: Profile,
    complaint: Complaint,
    rejection_reason: str,
) -> Complaint:
    """
    Citizen rejects the resolution of a complaint if the fix is unsatisfactory.

    Status transition:
      RESOLVED -> IN_PROGRESS
      closure_confirmation -> rejected
      closure_due_at -> NULL

    Raises:
      ValidationError: If rejection reason is empty or if complaint is not in RESOLVED status.
    """
    validate_citizen_owns_complaint(citizen, complaint)

    if complaint.status != ComplaintStatus.RESOLVED:
        raise ValidationError(
            f'Only complaints in RESOLVED status can be rejected (current status: {complaint.status}).'
        )

    reason_cleaned = (rejection_reason or '').strip()
    if not reason_cleaned or len(reason_cleaned) < 5:
        raise ValidationError('A valid rejection reason (minimum 5 characters) is mandatory to reject a resolution.')

    now = datetime.now(timezone.utc)

    with transaction.atomic():
        complaint.status = ComplaintStatus.IN_PROGRESS
        complaint.closure_confirmation = ClosureConfirmation.REJECTED
        complaint.closure_due_at = None
        complaint.updated_at = now
        complaint.save(update_fields=['status', 'closure_confirmation', 'closure_due_at', 'updated_at'])

        ComplaintStatusHistory.objects.create(
            id=uuid.uuid4(),
            complaint=complaint,
            old_status=ComplaintStatus.RESOLVED,
            new_status=ComplaintStatus.IN_PROGRESS,
            changed_by=citizen,
            change_reason=reason_cleaned,
            changed_at=now,
        )

        notifications = []
        # Notify assigned employee that resolution was rejected
        if complaint.assigned_employee_id:
            notifications.append(
                Notification(
                    id=uuid.uuid4(),
                    recipient_id=complaint.assigned_employee_id,
                    complaint_id=complaint.id,
                    trigger_event=NotificationEventType.STATUS_CHANGE,
                    channel=NotificationChannelType.IN_APP,
                    message_content=(
                        f'Citizen rejected resolution for complaint {complaint.complaint_number}. '
                        f'Reason: {reason_cleaned}. Status moved back to IN_PROGRESS.'
                    ),
                    created_at=now,
                )
            )

        # Notify department supervisor
        if complaint.assigned_department_id:
            supervisors = Profile.objects.filter(
                department_id=complaint.assigned_department_id,
                role__role_name=Role.SUPERVISOR,
                account_status=Profile.ACCOUNT_STATUS_ACTIVE,
            )
            for supervisor in supervisors:
                notifications.append(
                    Notification(
                        id=uuid.uuid4(),
                        recipient_id=supervisor.id,
                        complaint_id=complaint.id,
                        trigger_event=NotificationEventType.STATUS_CHANGE,
                        channel=NotificationChannelType.IN_APP,
                        message_content=(
                            f'Resolution for complaint {complaint.complaint_number} was rejected by citizen. '
                            f'Reason: {reason_cleaned}.'
                        ),
                        created_at=now,
                    )
                )

        if notifications:
            Notification.objects.bulk_create(notifications)

    logger.info(
        'Complaint %s resolution rejected by citizen %s. Returned to IN_PROGRESS.',
        complaint.complaint_number, citizen.id,
    )
    return complaint


def auto_close_expired_complaints(as_of_time: datetime = None) -> int:
    """
    Finds all RESOLVED complaints whose confirmation window has expired and closes them.

    Status transition:
      RESOLVED -> CLOSED
      closure_confirmation -> auto_closed
    """
    now = as_of_time or datetime.now(timezone.utc)
    expired_complaints = Complaint.objects.filter(
        status=ComplaintStatus.RESOLVED,
        closure_confirmation=ClosureConfirmation.PENDING,
        closure_due_at__lte=now,
    )

    closed_count = 0
    for complaint in expired_complaints:
        with transaction.atomic():
            complaint.status = ComplaintStatus.CLOSED
            complaint.closure_confirmation = ClosureConfirmation.AUTO_CLOSED
            complaint.updated_at = now
            complaint.save(update_fields=['status', 'closure_confirmation', 'updated_at'])

            ComplaintStatusHistory.objects.create(
                id=uuid.uuid4(),
                complaint=complaint,
                old_status=ComplaintStatus.RESOLVED,
                new_status=ComplaintStatus.CLOSED,
                changed_by=None,  # Automated system action
                change_reason='Automatically closed after expiration of the citizen confirmation window.',
                changed_at=now,
            )

            # Notify citizen of automatic closure
            Notification.objects.create(
                id=uuid.uuid4(),
                recipient_id=complaint.citizen_id,
                complaint_id=complaint.id,
                trigger_event=NotificationEventType.CLOSURE,
                channel=NotificationChannelType.IN_APP,
                message_content=(
                    f'Your complaint {complaint.complaint_number} has been automatically closed '
                    'following the expiration of the confirmation window.'
                ),
                created_at=now,
            )

            closed_count += 1

    logger.info('Auto-closed %d expired complaints.', closed_count)
    return closed_count
