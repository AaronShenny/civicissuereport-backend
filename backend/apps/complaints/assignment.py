"""
apps/complaints/assignment.py

Supervisor Employee Assignment & Reassignment Service (Phase 4).

Follows User Stories and database_schema.md:
  - Supervisor is the primary actor for employee assignment.
  - Department isolation is strictly enforced server-side.
  - Assignment transitions status: UNDER_VERIFICATION -> ASSIGNED.
  - Every assignment creates an immutable audit record in complaint_assignments.
  - Reassignment creates a new history record without deleting past history.
  - Notifications are generated for newly assigned employees.
"""

import uuid
import logging
from datetime import datetime, timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ComplaintAssignment,
    ComplaintStatusHistory,
    Notification,
    NotificationEventType,
    NotificationChannelType,
)
from apps.users.models import Profile, Role

logger = logging.getLogger(__name__)


def validate_supervisor_can_assign(supervisor: Profile, complaint: Complaint) -> None:
    """
    Validates supervisor permissions and department ownership of the complaint.
    """
    if not supervisor or not supervisor.is_supervisor:
        raise ValidationError('Only users with the Supervisor role can assign complaints.')

    if not supervisor.department_id:
        raise ValidationError('Supervisor must belong to a department to assign complaints.')

    if not complaint.assigned_department_id:
        raise ValidationError('Complaint must be routed to a department before employee assignment.')

    if str(complaint.assigned_department_id) != str(supervisor.department_id):
        raise ValidationError('Supervisors can only assign complaints belonging to their own department.')


def validate_target_employee(employee: Profile, supervisor: Profile) -> None:
    """
    Validates target employee role, active status, and department match.
    """
    if not employee:
        raise ValidationError('Target employee does not exist.')

    if employee.role_name != Role.GROUND_LEVEL_EMPLOYEE:
        raise ValidationError('Complaints can only be assigned to Ground-Level Employees.')

    if employee.account_status != Profile.ACCOUNT_STATUS_ACTIVE:
        raise ValidationError('Cannot assign complaints to an inactive employee.')

    if str(employee.department_id) != str(supervisor.department_id):
        raise ValidationError(
            'Cannot assign an employee from another department. '
            f'Supervisor department: {supervisor.department_id}, Employee department: {employee.department_id}.'
        )


def assign_employee_to_complaint(
    supervisor: Profile,
    complaint: Complaint,
    employee: Profile,
    assignment_reason: str = '',
) -> Complaint:
    """
    Assigns an unassigned complaint to a Ground-Level Employee.

    Atomic workflow:
      1. Validate supervisor, department ownership, and employee eligibility.
      2. Check complaint is in UNDER_VERIFICATION and not currently assigned.
      3. Set complaint.assigned_employee_id and status = ASSIGNED.
      4. Insert complaint_assignments record.
      5. Insert complaint_status_history record (UNDER_VERIFICATION -> ASSIGNED).
      6. Create in-app notification for the assigned employee.

    Returns:
      Updated Complaint instance.
    """
    # 1. Validations
    validate_supervisor_can_assign(supervisor, complaint)
    validate_target_employee(employee, supervisor)

    if complaint.status != ComplaintStatus.UNDER_VERIFICATION:
        raise ValidationError(
            f'Complaint must be in UNDER_VERIFICATION status to be assigned (current status: {complaint.status}).'
        )

    if complaint.assigned_employee_id is not None:
        raise ValidationError(
            'Complaint is already assigned to an employee. Use the reassignment action instead.'
        )

    with transaction.atomic():
        now = datetime.now(timezone.utc)
        old_status = complaint.status

        # 2. Update complaint state
        complaint.assigned_employee_id = employee.id
        complaint.status = ComplaintStatus.ASSIGNED
        complaint.updated_at = now
        complaint.save(update_fields=['assigned_employee_id', 'status', 'updated_at'])

        # 3. Create assignment history record
        ComplaintAssignment.objects.create(
            id=uuid.uuid4(),
            complaint=complaint,
            department=complaint.assigned_department,
            employee=employee,
            assigned_by=supervisor,
            assignment_reason=assignment_reason.strip() if assignment_reason else None,
            assignment_date=now,
        )

        # 4. Create status history record
        ComplaintStatusHistory.objects.create(
            id=uuid.uuid4(),
            complaint=complaint,
            old_status=old_status,
            new_status=ComplaintStatus.ASSIGNED,
            changed_by=supervisor,
            change_reason=assignment_reason.strip() if assignment_reason else f'Assigned to {employee.full_name} by supervisor.',
            changed_at=now,
        )

        # 5. Create notification for assigned employee
        Notification.objects.create(
            id=uuid.uuid4(),
            recipient=employee,
            complaint=complaint,
            trigger_event=NotificationEventType.ASSIGNMENT,
            channel=NotificationChannelType.IN_APP,
            message_content=(
                f'You have been assigned complaint {complaint.complaint_number} '
                f'({complaint.category.name if complaint.category else "General"}).'
            ),
            created_at=now,
        )

        from apps.users.audit_logger import log_audit_event
        log_audit_event(
            actor=supervisor,
            action="assign_complaint",
            entity_type="Complaint",
            entity_id=str(complaint.id),
            old_value={"assigned_employee_id": None},
            new_value={"assigned_employee_id": str(employee.id)}
        )

        logger.info(
            'Complaint %s assigned to employee %s (%s) by supervisor %s',
            complaint.complaint_number, employee.id, employee.full_name, supervisor.id,
        )
        return complaint


def reassign_employee_to_complaint(
    supervisor: Profile,
    complaint: Complaint,
    new_employee: Profile,
    reassignment_reason: str = '',
) -> Complaint:
    """
    Reassigns an assigned complaint to a different Ground-Level Employee within the same department.

    Atomic workflow:
      1. Validate supervisor, department ownership, and new employee eligibility.
      2. Set complaint.assigned_employee_id = new_employee.id.
      3. Insert NEW complaint_assignments record with reassignment_reason (historical records preserved).
      4. Create in-app notification for the newly assigned employee.

    Returns:
      Updated Complaint instance.
    """
    validate_supervisor_can_assign(supervisor, complaint)
    validate_target_employee(new_employee, supervisor)

    with transaction.atomic():
        now = datetime.now(timezone.utc)
        old_employee_id = complaint.assigned_employee_id

        # Update complaint assigned employee
        complaint.assigned_employee_id = new_employee.id
        complaint.updated_at = now
        complaint.save(update_fields=['assigned_employee_id', 'updated_at'])

        # Record new assignment history row (never overwrite old ones)
        ComplaintAssignment.objects.create(
            id=uuid.uuid4(),
            complaint=complaint,
            department=complaint.assigned_department,
            employee=new_employee,
            assigned_by=supervisor,
            assignment_date=now,
            reassignment_reason=reassignment_reason.strip() if reassignment_reason else f'Reassigned by supervisor {supervisor.full_name}.',
        )

        # Create notification for the newly assigned employee
        Notification.objects.create(
            id=uuid.uuid4(),
            recipient=new_employee,
            complaint=complaint,
            trigger_event=NotificationEventType.ASSIGNMENT,
            channel=NotificationChannelType.IN_APP,
            message_content=(
                f'You have been assigned complaint {complaint.complaint_number} via reassignment.'
            ),
            created_at=now,
        )

        from apps.users.audit_logger import log_audit_event
        log_audit_event(
            actor=supervisor,
            action="reassign_complaint",
            entity_type="Complaint",
            entity_id=str(complaint.id),
            old_value={"assigned_employee_id": str(old_employee_id) if old_employee_id else None},
            new_value={"assigned_employee_id": str(new_employee.id)}
        )

        logger.info(
            'Complaint %s reassigned to employee %s (%s) by supervisor %s',
            complaint.complaint_number, new_employee.id, new_employee.full_name, supervisor.id,
        )
        return complaint
