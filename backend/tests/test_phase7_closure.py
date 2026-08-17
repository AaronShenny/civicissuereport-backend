"""
tests/test_phase7_closure.py

Phase 7 test suite: Citizen Confirmation, Rejection, and Auto-Closure.

Covers:
  - Citizen confirmation: RESOLVED -> CLOSED (closure_confirmation = 'confirmed')
  - Citizen rejection: RESOLVED -> IN_PROGRESS (closure_confirmation = 'rejected', mandatory reason)
  - Ownership & role enforcement (only submitting citizen can confirm/reject)
  - Status prerequisites (only RESOLVED complaints can be confirmed/rejected)
  - Auto-closure of expired resolved complaints (closure_confirmation = 'auto_closed', changed_by = None)
  - Notifications for confirmation, rejection, and auto-closure
  - Post-closure finality (closed complaints cannot be confirmed/rejected)
  - Regression guards
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from contextlib import nullcontext
from django.core.exceptions import ValidationError

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ClosureConfirmation,
    ComplaintStatusHistory,
    Notification,
    NotificationEventType,
)
from apps.complaints.closure import (
    confirm_resolution,
    reject_resolution,
    auto_close_expired_complaints,
    validate_citizen_owns_complaint,
)
from apps.users.models import Department, Profile, Role


@pytest.fixture(autouse=True)
def mock_atomic_transaction():
    with patch('django.db.transaction.atomic', side_effect=nullcontext):
        yield


# ---------------------------------------------------------------------------
# Test Fixtures & Mock Builders
# ---------------------------------------------------------------------------

def make_mock_department(dept_id=None, name='Public Works') -> MagicMock:
    dept = MagicMock(spec=Department)
    dept.id = dept_id or uuid.uuid4()
    dept.name = name
    dept.is_active = True
    return dept


def make_mock_profile(
    role_name: str,
    dept_id=None,
    full_name='Test User',
    account_status='active',
) -> MagicMock:
    profile = MagicMock(spec=Profile)
    profile.id = uuid.uuid4()
    profile.full_name = full_name
    profile.role_name = role_name
    profile.role = MagicMock()
    profile.role.role_name = role_name
    profile.department_id = dept_id
    profile.account_status = account_status
    profile.is_authenticated = True
    profile.profile = profile

    profile.is_citizen = (role_name == Role.CITIZEN)
    profile.is_ground_level_employee = (role_name == Role.GROUND_LEVEL_EMPLOYEE)
    profile.is_supervisor = (role_name == Role.SUPERVISOR)
    profile.is_department_admin = (role_name == Role.DEPARTMENT_ADMIN)
    profile.is_system_admin = (role_name == Role.SYSTEM_ADMIN)
    profile.is_staff_member = (role_name != Role.CITIZEN)
    return profile


def make_mock_complaint(
    complaint_id=None,
    dept_id=None,
    employee_id=None,
    citizen_id=None,
    status=ComplaintStatus.RESOLVED,
    closure_confirmation=ClosureConfirmation.PENDING,
) -> MagicMock:
    c = MagicMock(spec=Complaint)
    c.id = complaint_id or uuid.uuid4()
    c.complaint_number = 'CMP-2026-000001'
    c.citizen_id = citizen_id or uuid.uuid4()
    c.assigned_department_id = dept_id or uuid.uuid4()
    c.assigned_employee_id = employee_id or uuid.uuid4()
    c.status = status
    c.closure_confirmation = closure_confirmation
    c.closure_due_at = datetime.now(timezone.utc) + timedelta(days=7)
    c.description = 'Test complaint for closure'
    c.category = MagicMock()
    c.category.name = 'pothole'
    return c


# ===========================================================================
# 1-6: Citizen Confirmation Workflow
# ===========================================================================

class TestCitizenConfirmation:

    # 1. Citizen can confirm resolution of their own complaint (RESOLVED -> CLOSED)
    # 2. Status history created on confirmation
    # 3. closure_confirmation set to confirmed
    def test_citizen_confirms_resolution_transitions_to_closed(self):
        dept = make_mock_department()
        citizen = make_mock_profile(Role.CITIZEN, full_name='Citizen Jane')
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            citizen_id=citizen.id,
            status=ComplaintStatus.RESOLVED,
        )

        with patch('apps.complaints.closure.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.closure.Profile.objects.filter', return_value=[]), \
             patch('apps.complaints.closure.Notification.objects.bulk_create') as mock_notif_create:

            updated_complaint = confirm_resolution(
                citizen=citizen,
                complaint=complaint,
                confirmation_remarks='Pothole fix verified on site. Thank you!',
            )

            # Status updated to CLOSED
            assert updated_complaint.status == ComplaintStatus.CLOSED
            assert updated_complaint.closure_confirmation == ClosureConfirmation.CONFIRMED

            # Status history record created
            mock_hist_create.assert_called_once()
            h_kwargs = mock_hist_create.call_args[1]
            assert h_kwargs['old_status'] == ComplaintStatus.RESOLVED
            assert h_kwargs['new_status'] == ComplaintStatus.CLOSED
            assert h_kwargs['changed_by'] == citizen
            assert 'Pothole fix verified' in h_kwargs['change_reason']

            # Closure notification sent
            mock_notif_create.assert_called_once()
            notifications = mock_notif_create.call_args[0][0]
            assert any(n.trigger_event == NotificationEventType.CLOSURE for n in notifications)

    # 4. Citizen cannot confirm another citizen's complaint
    def test_citizen_cannot_confirm_other_citizen_complaint(self):
        citizen_a = make_mock_profile(Role.CITIZEN)
        citizen_b = make_mock_profile(Role.CITIZEN)
        complaint = make_mock_complaint(citizen_id=citizen_b.id, status=ComplaintStatus.RESOLVED)

        with pytest.raises(ValidationError, match='your own complaints'):
            confirm_resolution(citizen=citizen_a, complaint=complaint)

    # 5. Non-citizen cannot confirm resolution
    def test_staff_cannot_confirm_resolution(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, employee_id=employee.id, status=ComplaintStatus.RESOLVED)

        with pytest.raises(ValidationError, match='Only Citizens'):
            confirm_resolution(citizen=employee, complaint=complaint)

    # 6. Cannot confirm a non-resolved complaint
    def test_cannot_confirm_unresolved_complaint(self):
        citizen = make_mock_profile(Role.CITIZEN)
        complaint = make_mock_complaint(citizen_id=citizen.id, status=ComplaintStatus.IN_PROGRESS)

        with pytest.raises(ValidationError, match='Only complaints in RESOLVED status'):
            confirm_resolution(citizen=citizen, complaint=complaint)


# ===========================================================================
# 7-12: Citizen Rejection Workflow
# ===========================================================================

class TestCitizenRejection:

    # 7. Citizen can reject resolution with mandatory reason (RESOLVED -> IN_PROGRESS)
    # 8. Status history created on rejection
    # 9. closure_confirmation set to rejected, closure_due_at reset
    def test_citizen_rejects_resolution_transitions_to_in_progress(self):
        dept = make_mock_department()
        citizen = make_mock_profile(Role.CITIZEN, full_name='Citizen Jane')
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            citizen_id=citizen.id,
            status=ComplaintStatus.RESOLVED,
        )

        with patch('apps.complaints.closure.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.closure.Profile.objects.filter', return_value=[]), \
             patch('apps.complaints.closure.Notification.objects.bulk_create') as mock_notif_create:

            updated_complaint = reject_resolution(
                citizen=citizen,
                complaint=complaint,
                rejection_reason='The patch has already sunk and water is accumulating again.',
            )

            # Status returned to IN_PROGRESS
            assert updated_complaint.status == ComplaintStatus.IN_PROGRESS
            assert updated_complaint.closure_confirmation == ClosureConfirmation.REJECTED
            assert updated_complaint.closure_due_at is None

            # Status history record created
            mock_hist_create.assert_called_once()
            h_kwargs = mock_hist_create.call_args[1]
            assert h_kwargs['old_status'] == ComplaintStatus.RESOLVED
            assert h_kwargs['new_status'] == ComplaintStatus.IN_PROGRESS
            assert h_kwargs['changed_by'] == citizen
            assert 'patch has already sunk' in h_kwargs['change_reason']

            # Notification sent
            mock_notif_create.assert_called_once()

    # 10. Empty or too short rejection reason rejected
    def test_empty_rejection_reason_rejected(self):
        citizen = make_mock_profile(Role.CITIZEN)
        complaint = make_mock_complaint(citizen_id=citizen.id, status=ComplaintStatus.RESOLVED)

        with pytest.raises(ValidationError, match='rejection reason .* is mandatory'):
            reject_resolution(citizen=citizen, complaint=complaint, rejection_reason='bad')

    # 11. Citizen cannot reject another citizen's complaint
    def test_citizen_cannot_reject_other_citizen_complaint(self):
        citizen_a = make_mock_profile(Role.CITIZEN)
        citizen_b = make_mock_profile(Role.CITIZEN)
        complaint = make_mock_complaint(citizen_id=citizen_b.id, status=ComplaintStatus.RESOLVED)

        with pytest.raises(ValidationError, match='your own complaints'):
            reject_resolution(citizen=citizen_a, complaint=complaint, rejection_reason='Not fixed properly.')


# ===========================================================================
# 13-16: Auto-Closure & Post-Closure Finality
# ===========================================================================

class TestAutoClosureAndFinality:

    # 13-14. Auto-closure closes expired resolved complaints
    def test_auto_close_expired_complaints(self):
        now = datetime.now(timezone.utc)
        expired_complaint = make_mock_complaint(
            status=ComplaintStatus.RESOLVED,
            closure_confirmation=ClosureConfirmation.PENDING,
        )
        expired_complaint.closure_due_at = now - timedelta(hours=1)  # Expired

        with patch('apps.complaints.closure.Complaint.objects.filter', return_value=[expired_complaint]), \
             patch('apps.complaints.closure.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.closure.Notification.objects.create') as mock_notif_create:

            closed_count = auto_close_expired_complaints(as_of_time=now)

            assert closed_count == 1
            assert expired_complaint.status == ComplaintStatus.CLOSED
            assert expired_complaint.closure_confirmation == ClosureConfirmation.AUTO_CLOSED

            # Changed by is None for automated system action
            mock_hist_create.assert_called_once()
            h_kwargs = mock_hist_create.call_args[1]
            assert h_kwargs['changed_by'] is None
            assert h_kwargs['old_status'] == ComplaintStatus.RESOLVED
            assert h_kwargs['new_status'] == ComplaintStatus.CLOSED

    # 16. Post-closure finality: closed complaints cannot be confirmed or rejected
    def test_closed_complaints_cannot_be_confirmed_or_rejected(self):
        citizen = make_mock_profile(Role.CITIZEN)
        closed_complaint = make_mock_complaint(citizen_id=citizen.id, status=ComplaintStatus.CLOSED)

        with pytest.raises(ValidationError, match='Only complaints in RESOLVED status'):
            confirm_resolution(citizen=citizen, complaint=closed_complaint)

        with pytest.raises(ValidationError, match='Only complaints in RESOLVED status'):
            reject_resolution(citizen=citizen, complaint=closed_complaint, rejection_reason='Attempted post-closure reject')


# ===========================================================================
# 17: Regression Guards
# ===========================================================================

class TestPhase7RegressionGuards:

    def test_phase7_modules_importable(self):
        from apps.complaints.closure import confirm_resolution, reject_resolution, auto_close_expired_complaints
        from apps.complaints.models import ClosureConfirmation
        assert confirm_resolution is not None
        assert reject_resolution is not None
        assert auto_close_expired_complaints is not None
        assert ClosureConfirmation is not None
