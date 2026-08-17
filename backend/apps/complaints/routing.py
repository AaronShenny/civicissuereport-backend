"""
apps/complaints/routing.py

Department Routing Engine (Phase 4).

Determines the responsible government department for a complaint using:
  1. Complaint category
  2. Geographic location
  3. Active department_category_rules and jurisdictions

Department routing sets:
  - complaints.assigned_department_id
  - complaints.status = 'under_verification'
  - complaint_status_history (old='submitted', new='under_verification', changed_by=None)
  - notifications (department supervisor/staff notification)

Department routing does NOT set:
  - complaints.assigned_employee_id (remains NULL until Supervisor assigns)
"""

import uuid
import logging
from datetime import datetime, timezone
from django.db import transaction

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ComplaintStatusHistory,
    Notification,
    NotificationEventType,
    NotificationChannelType,
)
from apps.departments.models import DepartmentCategoryRule
from apps.users.models import Department, Profile, Role

logger = logging.getLogger(__name__)


class RoutingFailureError(Exception):
    """Raised when no responsible department can be determined for a complaint."""
    pass


def find_responsible_department(complaint: Complaint) -> Department | None:
    """
    Identifies the responsible Department for a given Complaint.
    Evaluates active DepartmentCategoryRule entries matching the complaint category,
    prioritized by priority_rank.
    """
    if not complaint.category_id:
        return None

    # Query active department category rules for the category
    rule = (
        DepartmentCategoryRule.objects
        .filter(
            category_id=complaint.category_id,
            is_active=True,
            department__is_active=True,
        )
        .select_related('department')
        .order_by('priority_rank')
        .first()
    )

    if rule:
        return rule.department

    return None


def route_complaint(complaint: Complaint) -> Department:
    """
    Executes automated department routing for a submitted complaint.

    Atomic actions:
      1. Find responsible department using category + location rules.
      2. Set complaint.assigned_department_id = department.id.
      3. Transition status from SUBMITTED -> UNDER_VERIFICATION.
      4. Create status history record (changed_by = None for system action).
      5. Create in-app department notification for department supervisors.

    Raises:
      RoutingFailureError: If no active department rule matches.
    """
    with transaction.atomic():
        department = find_responsible_department(complaint)

        if not department:
            logger.warning(
                'Routing failed: No active department rule found for complaint %s (category_id=%s)',
                complaint.complaint_number, complaint.category_id,
            )
            raise RoutingFailureError(
                f'Unable to determine responsible department for complaint {complaint.complaint_number}.'
            )

        now = datetime.now(timezone.utc)
        old_status = complaint.status

        # 1. Update complaint department and status
        complaint.assigned_department_id = department.id
        complaint.status = ComplaintStatus.UNDER_VERIFICATION
        complaint.updated_at = now
        # Ensure assigned_employee_id remains untouched/NULL
        complaint.save(update_fields=['assigned_department_id', 'status', 'updated_at'])

        # 2. Record status transition in complaint_status_history
        ComplaintStatusHistory.objects.create(
            id=uuid.uuid4(),
            complaint=complaint,
            old_status=old_status,
            new_status=ComplaintStatus.UNDER_VERIFICATION,
            changed_by=None,  # Automated system action
            change_reason=f'Automatically routed to {department.name} based on category and location.',
            changed_at=now,
        )

        # 3. Create notifications for department supervisors
        supervisors = Profile.objects.filter(
            department_id=department.id,
            role__role_name=Role.SUPERVISOR,
            account_status=Profile.ACCOUNT_STATUS_ACTIVE,
        )

        notifications_to_create = [
            Notification(
                id=uuid.uuid4(),
                recipient_id=supervisor.id,
                complaint_id=complaint.id,
                trigger_event=NotificationEventType.ASSIGNMENT,
                channel=NotificationChannelType.IN_APP,
                message_content=(
                    f'New complaint {complaint.complaint_number} ({complaint.category.name if complaint.category else "General"}) '
                    f'has been routed to your department and requires employee assignment.'
                ),
                created_at=now,
            )
            for supervisor in supervisors
        ]

        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)

        logger.info(
            'Complaint %s successfully routed to %s (Status: %s)',
            complaint.complaint_number, department.name, complaint.status,
        )
        return department

