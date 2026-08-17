"""
tests/test_phase6_resolution.py

Phase 6 test suite: Progress Updates and Resolution.

Covers:
  - Progress updates & VERIFIED -> IN_PROGRESS on work initiation
  - Ongoing progress updates on IN_PROGRESS (no duplicate status history)
  - Authorized actors: Assigned Ground-Level Employee OR authorized Department Supervisor
  - Unauthorized callers rejected: Cross-dept supervisor, unassigned employee, citizen, department admin
  - Expected completion date handling & deadline notifications
  - Resolution submission: IN_PROGRESS -> RESOLVED, proof upload via Supabase Storage
  - Direct VERIFIED -> RESOLVED blocked
  - Status history audit & anti-spoofing
  - Regression guards
"""

import uuid
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from contextlib import nullcontext
from django.core.exceptions import ValidationError

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ComplaintCategory,
    ComplaintResolution,
    ComplaintStatusHistory,
    ComplaintAttachment,
    AttachmentPurpose,
    Notification,
    NotificationEventType,
)
from apps.complaints.resolution import (
    add_progress_update,
    resolve_complaint,
    can_update_complaint_work,
    validate_user_can_update_work,
)
from apps.complaints.services import PendingAttachment
from apps.users.models import Department, Profile, Role
from core.permissions.roles import IsAssignedEmployeeOrDepartmentSupervisor


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
    status=ComplaintStatus.VERIFIED,
) -> MagicMock:
    c = MagicMock(spec=Complaint)
    c.id = complaint_id or uuid.uuid4()
    c.complaint_number = 'CMP-2026-000001'
    c.citizen_id = citizen_id or uuid.uuid4()
    c.assigned_department_id = dept_id or uuid.uuid4()
    c.assigned_employee_id = employee_id
    c.status = status
    c.expected_completion_date = None
    c.description = 'Test complaint for progress/resolution'
    c.category = MagicMock()
    c.category.name = 'pothole'
    return c


# ===========================================================================
# 1-6: Progress Updates & Status Transitions
# ===========================================================================

class TestProgressUpdatesAndTransitions:

    # 1. Assigned employee can create progress update & transition VERIFIED -> IN_PROGRESS
    def test_assigned_employee_first_progress_update_transitions_verified_to_in_progress(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            status=ComplaintStatus.VERIFIED,
        )

        with patch('apps.complaints.resolution.ComplaintResolution.objects.create') as mock_res_create, \
             patch('apps.complaints.resolution.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.resolution.Notification.objects.bulk_create'):

            res_record, updated_complaint = add_progress_update(
                user=employee,
                complaint=complaint,
                progress_update='Procured asphalt and machinery. Commencing patch work.',
            )

            assert updated_complaint.status == ComplaintStatus.IN_PROGRESS

            mock_hist_create.assert_called_once()
            h_kwargs = mock_hist_create.call_args[1]
            assert h_kwargs['old_status'] == ComplaintStatus.VERIFIED
            assert h_kwargs['new_status'] == ComplaintStatus.IN_PROGRESS
            assert h_kwargs['changed_by'] == employee

            mock_res_create.assert_called_once()
            r_kwargs = mock_res_create.call_args[1]
            assert r_kwargs['progress_update'] == 'Procured asphalt and machinery. Commencing patch work.'
            assert r_kwargs['updated_by'] == employee

    # 2. Authorized Department Supervisor can create progress update
    def test_department_supervisor_can_create_progress_update(self):
        dept = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id, full_name='Supervisor Sam')
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            status=ComplaintStatus.VERIFIED,
        )

        with patch('apps.complaints.resolution.ComplaintResolution.objects.create') as mock_res_create, \
             patch('apps.complaints.resolution.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.resolution.Notification.objects.bulk_create'):

            res_record, updated_complaint = add_progress_update(
                user=supervisor,
                complaint=complaint,
                progress_update='Supervisor dispatched emergency equipment to site.',
            )

            assert updated_complaint.status == ComplaintStatus.IN_PROGRESS
            mock_hist_create.assert_called_once()
            assert mock_hist_create.call_args[1]['changed_by'] == supervisor
            assert mock_res_create.call_args[1]['updated_by'] == supervisor

    # 3. Subsequent progress updates on IN_PROGRESS do not duplicate status history
    def test_subsequent_progress_update_on_in_progress_does_not_duplicate_status_history(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            status=ComplaintStatus.IN_PROGRESS,  # Already IN_PROGRESS
        )

        with patch('apps.complaints.resolution.ComplaintResolution.objects.create') as mock_res_create, \
             patch('apps.complaints.resolution.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.resolution.Notification.objects.bulk_create'):

            res_record, updated_complaint = add_progress_update(
                user=employee,
                complaint=complaint,
                progress_update='Finished laying gravel foundation. Roller compaction underway.',
            )

            assert updated_complaint.status == ComplaintStatus.IN_PROGRESS
            mock_hist_create.assert_not_called()
            mock_res_create.assert_called_once()

    # 4. Cannot update progress before verification
    def test_unready_status_cannot_record_progress(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            status=ComplaintStatus.ASSIGNED,  # Still ASSIGNED, not yet verified
        )

        with pytest.raises(ValidationError, match='must be in VERIFIED or IN_PROGRESS'):
            add_progress_update(
                user=employee,
                complaint=complaint,
                progress_update='Attempted progress before verification',
            )


# ===========================================================================
# 5-8: Authorization & Department Isolation Checks
# ===========================================================================

class TestAuthorizationAndDepartmentIsolation:

    # 5. Supervisor from another department is rejected
    def test_cross_department_supervisor_cannot_update_progress(self):
        dept_a = make_mock_department(name='Public Works')
        dept_b = make_mock_department(name='Sanitation')
        foreign_supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept_b.id)
        complaint = make_mock_complaint(dept_id=dept_a.id, status=ComplaintStatus.VERIFIED)

        with pytest.raises(ValidationError, match='belonging to your department'):
            validate_user_can_update_work(foreign_supervisor, complaint)

    # 6. Supervisor without a department is rejected
    def test_supervisor_without_department_rejected(self):
        dept = make_mock_department()
        homeless_supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=None)
        complaint = make_mock_complaint(dept_id=dept.id, status=ComplaintStatus.VERIFIED)

        with pytest.raises(ValidationError, match='must be assigned to a department'):
            validate_user_can_update_work(homeless_supervisor, complaint)

    # 7. Unassigned employee in same department cannot update
    def test_unassigned_employee_cannot_update_progress(self):
        dept = make_mock_department()
        emp_a = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        emp_b = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, employee_id=emp_b.id, status=ComplaintStatus.VERIFIED)

        with pytest.raises(ValidationError, match='specifically assigned to you'):
            validate_user_can_update_work(emp_a, complaint)

    # 8. Citizen and Department Admin rejected
    def test_citizen_cannot_update_progress(self):
        citizen = make_mock_profile(Role.CITIZEN)
        complaint = make_mock_complaint(status=ComplaintStatus.VERIFIED)

        with pytest.raises(ValidationError, match='assigned Ground-Level Employee or authorized Department Supervisor'):
            validate_user_can_update_work(citizen, complaint)

    def test_department_admin_cannot_update_progress(self):
        dept = make_mock_department()
        dept_admin = make_mock_profile(Role.DEPARTMENT_ADMIN, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, status=ComplaintStatus.VERIFIED)

        with pytest.raises(ValidationError, match='assigned Ground-Level Employee or authorized Department Supervisor'):
            validate_user_can_update_work(dept_admin, complaint)

    # Helper function can_update_complaint_work verification
    def test_can_update_complaint_work_helper(self):
        dept_a = make_mock_department()
        dept_b = make_mock_department()
        emp = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept_a.id)
        other_emp = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept_a.id)
        sup_a = make_mock_profile(Role.SUPERVISOR, dept_id=dept_a.id)
        sup_b = make_mock_profile(Role.SUPERVISOR, dept_id=dept_b.id)
        citizen = make_mock_profile(Role.CITIZEN)

        complaint = make_mock_complaint(dept_id=dept_a.id, employee_id=emp.id)

        assert can_update_complaint_work(emp, complaint) is True
        assert can_update_complaint_work(sup_a, complaint) is True
        assert can_update_complaint_work(other_emp, complaint) is False
        assert can_update_complaint_work(sup_b, complaint) is False
        assert can_update_complaint_work(citizen, complaint) is False


# ===========================================================================
# 9-12: Expected Completion Date & Notifications
# ===========================================================================

class TestExpectedCompletionDateAndDeadline:

    def test_expected_completion_date_triggers_deadline_notification(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        citizen_id = uuid.uuid4()
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            citizen_id=citizen_id,
            status=ComplaintStatus.IN_PROGRESS,
        )
        complaint.expected_completion_date = None

        target_date = date.today() + timedelta(days=5)

        with patch('apps.complaints.resolution.ComplaintResolution.objects.create'), \
             patch('apps.complaints.resolution.Notification.objects.bulk_create') as mock_notif_create:

            add_progress_update(
                user=employee,
                complaint=complaint,
                progress_update='Expected completion in 5 days',
                expected_completion_date=target_date,
            )

            assert complaint.expected_completion_date == target_date
            mock_notif_create.assert_called_once()
            notifications = mock_notif_create.call_args[0][0]
            events = [n.trigger_event for n in notifications]
            assert NotificationEventType.DEADLINE_CHANGE in events


# ===========================================================================
# 13-17: Resolution Workflow, Proof & Authorization
# ===========================================================================

class TestResolutionWorkflow:

    # 13. Resolution from VERIFIED directly is rejected
    def test_verified_directly_to_resolved_is_rejected(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            status=ComplaintStatus.VERIFIED,  # Not yet IN_PROGRESS
        )

        with pytest.raises(ValidationError, match='must be in IN_PROGRESS status'):
            resolve_complaint(
                user=employee,
                complaint=complaint,
                resolution_details='Pothole completely filled and leveled.',
                pending_attachments=[MagicMock()],
            )

    # 14. Assigned employee can submit resolution
    def test_assigned_employee_can_resolve(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id, full_name='Worker John')
        citizen_id = uuid.uuid4()
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            citizen_id=citizen_id,
            status=ComplaintStatus.IN_PROGRESS,
        )

        proof_att = PendingAttachment(
            file_bytes=b'resolution photo proof',
            mime_type='image/jpeg',
            file_type='photo',
            original_name='completed_fix.jpg',
            size_bytes=1024 * 100,
        )

        with patch('apps.complaints.resolution.ComplaintResolution.objects.create') as mock_res_create, \
             patch('apps.complaints.resolution.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.resolution.ComplaintAttachment.objects.create') as mock_att_create, \
             patch('apps.complaints.resolution.upload_to_storage', return_value=True), \
             patch('apps.complaints.resolution.Profile.objects.filter', return_value=[]), \
             patch('apps.complaints.resolution.Notification.objects.bulk_create') as mock_notif_create:

            resolution, updated_complaint = resolve_complaint(
                user=employee,
                complaint=complaint,
                resolution_details='Pothole completely filled with cold-mix asphalt, compacted and flush with road surface.',
                remarks='Road reopened to normal traffic.',
                pending_attachments=[proof_att],
            )

            assert updated_complaint.status == ComplaintStatus.RESOLVED

            mock_hist_create.assert_called_once()
            h_kwargs = mock_hist_create.call_args[1]
            assert h_kwargs['old_status'] == ComplaintStatus.IN_PROGRESS
            assert h_kwargs['new_status'] == ComplaintStatus.RESOLVED
            assert h_kwargs['changed_by'] == employee

            mock_res_create.assert_called_once()
            assert mock_res_create.call_args[1]['is_final_resolution'] is True
            assert mock_res_create.call_args[1]['updated_by'] == employee

    # 15. Authorized Department Supervisor can submit resolution
    def test_department_supervisor_can_resolve(self):
        dept = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id, full_name='Supervisor Sam')
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            status=ComplaintStatus.IN_PROGRESS,
        )

        proof_att = PendingAttachment(
            file_bytes=b'supervisor proof',
            mime_type='image/png',
            file_type='photo',
            original_name='final_check.png',
            size_bytes=1024 * 50,
        )

        with patch('apps.complaints.resolution.ComplaintResolution.objects.create') as mock_res_create, \
             patch('apps.complaints.resolution.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.resolution.ComplaintAttachment.objects.create'), \
             patch('apps.complaints.resolution.upload_to_storage', return_value=True), \
             patch('apps.complaints.resolution.Profile.objects.filter', return_value=[]), \
             patch('apps.complaints.resolution.Notification.objects.bulk_create'):

            resolution, updated_complaint = resolve_complaint(
                user=supervisor,
                complaint=complaint,
                resolution_details='Supervisor verified and completed resolution on behalf of the department.',
                pending_attachments=[proof_att],
            )

            assert updated_complaint.status == ComplaintStatus.RESOLVED
            assert mock_hist_create.call_args[1]['changed_by'] == supervisor
            assert mock_res_create.call_args[1]['updated_by'] == supervisor

    # 16. Cross-department supervisor cannot resolve
    def test_cross_department_supervisor_cannot_resolve(self):
        dept_a = make_mock_department()
        dept_b = make_mock_department()
        foreign_supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept_b.id)
        complaint = make_mock_complaint(dept_id=dept_a.id, status=ComplaintStatus.IN_PROGRESS)

        with pytest.raises(ValidationError, match='belonging to your department'):
            resolve_complaint(
                user=foreign_supervisor,
                complaint=complaint,
                resolution_details='Unauthorized resolution attempt',
                pending_attachments=[MagicMock()],
            )

    # 17. Resolution requires mandatory proof attachment
    def test_resolution_missing_proof_rejected(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, employee_id=employee.id, status=ComplaintStatus.IN_PROGRESS)

        with pytest.raises(ValidationError, match='Resolution proof .* is mandatory'):
            resolve_complaint(
                user=employee,
                complaint=complaint,
                resolution_details='Attempted resolution without proof',
                pending_attachments=[],
            )


# ===========================================================================
# 18-20: Security & Anti-Spoofing
# ===========================================================================

class TestResolutionSecurity:

    def test_submit_progress_serializer_fields(self):
        from apps.complaints.serializers import SubmitProgressUpdateSerializer
        fields = list(SubmitProgressUpdateSerializer().fields.keys())
        assert 'status' not in fields
        assert 'updated_by' not in fields
        assert 'updated_by_id' not in fields
        assert 'complaint_id' not in fields

    def test_submit_resolution_serializer_fields(self):
        from apps.complaints.serializers import SubmitResolutionSerializer
        fields = list(SubmitResolutionSerializer().fields.keys())
        assert 'status' not in fields
        assert 'resolved_by' not in fields
        assert 'updated_by' not in fields
        assert 'complaint_id' not in fields


# ===========================================================================
# 21: Regression Guards
# ===========================================================================

class TestPhase6RegressionGuards:

    def test_phase6_modules_importable(self):
        from apps.complaints.resolution import add_progress_update, resolve_complaint, can_update_complaint_work
        from apps.complaints.models import ComplaintResolution
        assert add_progress_update is not None
        assert resolve_complaint is not None
        assert can_update_complaint_work is not None
        assert ComplaintResolution is not None
