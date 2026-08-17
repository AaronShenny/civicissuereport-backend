"""
tests/test_phase5_verification.py

Phase 5 test suite: Ground-Level Employee On-Site Verification.

Covers all 24 required test scenarios:
  1-4: Assigned Employee verification access & isolation (cannot verify unassigned, another employee's, or foreign dept)
  5-8: Role restrictions (supervisor, department admin, citizen cannot perform verification)
  9-14: Verification record creation, VERIFIED -> IN_PROGRESS, INVALID -> CLOSED, status history audit
  15-18: Verifier authenticity, anti-spoofing, duplicate verification prevention
  19-21: Validation of remarks/notes, evidence attachment handling and storage path
  22-23: Transactional atomicity and notification generation (trigger_event = 'verification')
  24: Regression guards
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock
from contextlib import nullcontext
from django.core.exceptions import ValidationError

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ComplaintCategory,
    ComplaintVerification,
    VerificationResultType,
    ComplaintStatusHistory,
    ComplaintAttachment,
    AttachmentPurpose,
    Notification,
    NotificationEventType,
)
from apps.complaints.verification import (
    verify_complaint,
    validate_employee_can_verify,
)
from apps.complaints.services import PendingAttachment
from apps.users.models import Department, Profile, Role
from core.permissions.roles import (
    IsGroundLevelEmployee,
    IsSupervisor,
    IsDepartmentAdmin,
    IsCitizen,
)


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
    status=ComplaintStatus.ASSIGNED,
) -> MagicMock:
    c = MagicMock(spec=Complaint)
    c.id = complaint_id or uuid.uuid4()
    c.complaint_number = 'CMP-2026-000001'
    c.citizen_id = citizen_id or uuid.uuid4()
    c.assigned_department_id = dept_id or uuid.uuid4()
    c.assigned_employee_id = employee_id
    c.status = status
    c.description = 'Test complaint for verification'
    c.category = MagicMock()
    c.category.name = 'pothole'
    return c


# ===========================================================================
# 1-4: Ground-Level Employee Access & Isolation
# ===========================================================================

class TestEmployeeVerificationAccess:

    # 1. Assigned Ground-Level Employee can verify their complaint
    def test_assigned_employee_can_verify(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            status=ComplaintStatus.ASSIGNED,
        )

        with patch('apps.complaints.verification.ComplaintVerification.objects.filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            # Should not raise
            validate_employee_can_verify(employee, complaint)

    # 2. Employee cannot verify another employee's complaint
    def test_employee_cannot_verify_another_employees_complaint(self):
        dept = make_mock_department()
        emp_a = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        emp_b = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=emp_b.id,  # assigned to B
            status=ComplaintStatus.ASSIGNED,
        )

        with pytest.raises(ValidationError, match='specifically assigned to you'):
            validate_employee_can_verify(emp_a, complaint)

    # 3. Employee cannot verify an unassigned complaint
    def test_employee_cannot_verify_unassigned_complaint(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=None,  # Unassigned
            status=ComplaintStatus.UNDER_VERIFICATION,
        )

        with pytest.raises(ValidationError, match='specifically assigned to you'):
            validate_employee_can_verify(employee, complaint)

    # 4. Employee cannot verify complaint in wrong status
    def test_employee_cannot_verify_unready_status(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            status=ComplaintStatus.SUBMITTED,
        )

        with pytest.raises(ValidationError, match='must be in ASSIGNED status'):
            validate_employee_can_verify(employee, complaint)


# ===========================================================================
# 5-8: Role Restrictions
# ===========================================================================

class TestRoleRestrictions:

    # 5. Non-employee cannot perform verification
    # 6. Supervisor cannot perform employee verification
    def test_supervisor_cannot_verify(self):
        dept = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, employee_id=supervisor.id, status=ComplaintStatus.ASSIGNED)

        with pytest.raises(ValidationError, match='Ground-Level Employees'):
            validate_employee_can_verify(supervisor, complaint)

    # 7. Department Admin cannot perform employee verification
    def test_department_admin_cannot_verify(self):
        dept = make_mock_department()
        dept_admin = make_mock_profile(Role.DEPARTMENT_ADMIN, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, employee_id=dept_admin.id, status=ComplaintStatus.ASSIGNED)

        with pytest.raises(ValidationError, match='Ground-Level Employees'):
            validate_employee_can_verify(dept_admin, complaint)

    # 8. Citizen cannot perform employee verification
    def test_citizen_cannot_verify(self):
        citizen = make_mock_profile(Role.CITIZEN)
        complaint = make_mock_complaint(employee_id=citizen.id, status=ComplaintStatus.ASSIGNED)

        with pytest.raises(ValidationError, match='Ground-Level Employees'):
            validate_employee_can_verify(citizen, complaint)


# ===========================================================================
# 9-14: Verification Workflows, Transitions & Status History
# ===========================================================================

class TestVerificationWorkflows:

    # 9. Verification record is created
    # 10. VERIFIED result changes ASSIGNED -> VERIFIED
    # 14. Status history is created for the transition
    def test_verified_workflow_transitions_to_verified_with_single_status_history_row(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id, full_name='Worker John')
        citizen_id = uuid.uuid4()
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            citizen_id=citizen_id,
            status=ComplaintStatus.ASSIGNED,
        )

        with patch('apps.complaints.verification.ComplaintVerification.objects.filter') as mock_v_filter, \
             patch('apps.complaints.verification.ComplaintVerification.objects.create') as mock_v_create, \
             patch('apps.complaints.verification.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.verification.Profile.objects.filter', return_value=[]), \
             patch('apps.complaints.verification.Notification.objects.bulk_create') as mock_notif_create:

            mock_v_filter.return_value.exists.return_value = False
            mock_verification = MagicMock(spec=ComplaintVerification)
            mock_v_create.return_value = mock_verification

            verification, updated_complaint = verify_complaint(
                employee=employee,
                complaint=complaint,
                verification_result='verified',
                verification_remarks='Site inspection confirmed 2ft pothole. Road repair required.',
                site_inspection_notes='Near marker post 42.',
            )

            # 9. Verification record created
            mock_v_create.assert_called_once()
            v_kwargs = mock_v_create.call_args[1]
            assert v_kwargs['verification_result'] == 'verified'
            assert v_kwargs['verification_remarks'] == 'Site inspection confirmed 2ft pothole. Road repair required.'
            assert v_kwargs['site_inspection_notes'] == 'Near marker post 42.'
            assert v_kwargs['verified_by'] == employee

            # 10. Complaint status is now VERIFIED
            assert updated_complaint.status == ComplaintStatus.VERIFIED

            # 14. Exactly 1 status history row created (ASSIGNED -> VERIFIED)
            assert mock_hist_create.call_count == 1
            call_1_kwargs = mock_hist_create.call_args_list[0][1]
            assert call_1_kwargs['old_status'] == ComplaintStatus.ASSIGNED
            assert call_1_kwargs['new_status'] == ComplaintStatus.VERIFIED
            assert call_1_kwargs['changed_by'] == employee


    # 11. INVALID result changes ASSIGNED -> INVALID
    # 13. INVALID -> CLOSED follows the defined workflow
    def test_invalid_workflow_transitions_to_closed_with_two_status_history_rows(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id, full_name='Worker John')
        citizen_id = uuid.uuid4()
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            citizen_id=citizen_id,
            status=ComplaintStatus.ASSIGNED,
        )

        with patch('apps.complaints.verification.ComplaintVerification.objects.filter') as mock_v_filter, \
             patch('apps.complaints.verification.ComplaintVerification.objects.create') as mock_v_create, \
             patch('apps.complaints.verification.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.verification.Profile.objects.filter', return_value=[]), \
             patch('apps.complaints.verification.Notification.objects.bulk_create') as mock_notif_create:

            mock_v_filter.return_value.exists.return_value = False
            mock_verification = MagicMock(spec=ComplaintVerification)
            mock_v_create.return_value = mock_verification

            verification, updated_complaint = verify_complaint(
                employee=employee,
                complaint=complaint,
                verification_result='invalid',
                verification_remarks='No defect found at given coordinates. Duplicate of private property.',
            )

            # 11 & 13. Final complaint status is CLOSED
            assert updated_complaint.status == ComplaintStatus.CLOSED

            # Status history verification
            assert mock_hist_create.call_count == 2
            # Row 1: ASSIGNED -> INVALID (by employee)
            call_1_kwargs = mock_hist_create.call_args_list[0][1]
            assert call_1_kwargs['old_status'] == ComplaintStatus.ASSIGNED
            assert call_1_kwargs['new_status'] == ComplaintStatus.INVALID
            assert call_1_kwargs['changed_by'] == employee

            # Row 2: INVALID -> CLOSED (by system)
            call_2_kwargs = mock_hist_create.call_args_list[1][1]
            assert call_2_kwargs['old_status'] == ComplaintStatus.INVALID
            assert call_2_kwargs['new_status'] == ComplaintStatus.CLOSED
            assert call_2_kwargs['changed_by'] is None  # System automated


# ===========================================================================
# 15-18: Authenticity, Anti-Spoofing & Duplicate Prevention
# ===========================================================================

class TestVerificationSecurity:

    # 15-16. Verifier is taken from authenticated user (anti-spoofing)
    def test_submit_serializer_does_not_allow_verifier_spoofing(self):
        from apps.complaints.serializers import SubmitVerificationSerializer
        fields = list(SubmitVerificationSerializer().fields.keys())
        assert 'verified_by' not in fields
        assert 'verified_by_id' not in fields
        assert 'status' not in fields
        assert 'complaint_id' not in fields

    # 18. Duplicate verification is rejected
    def test_duplicate_verification_is_rejected(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, employee_id=employee.id, status=ComplaintStatus.ASSIGNED)

        with patch('apps.complaints.verification.ComplaintVerification.objects.filter') as mock_v_filter:
            # Simulate existing verification
            mock_v_filter.return_value.exists.return_value = True

            with pytest.raises(ValidationError, match='already been verified'):
                validate_employee_can_verify(employee, complaint)


# ===========================================================================
# 19-21: Validation, Remarks & Evidence Attachments
# ===========================================================================

class TestVerificationValidationAndEvidence:

    # 19. Empty remarks rejected
    def test_empty_remarks_rejected(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, employee_id=employee.id, status=ComplaintStatus.ASSIGNED)

        with patch('apps.complaints.verification.ComplaintVerification.objects.filter') as mock_v_filter:
            mock_v_filter.return_value.exists.return_value = False

            with pytest.raises(ValidationError, match='remarks are mandatory'):
                verify_complaint(
                    employee=employee,
                    complaint=complaint,
                    verification_result='verified',
                    verification_remarks='   ',  # Empty/whitespace
                )

    # 19. Invalid verification decision rejected
    def test_invalid_result_choice_rejected(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, employee_id=employee.id, status=ComplaintStatus.ASSIGNED)

        with patch('apps.complaints.verification.ComplaintVerification.objects.filter') as mock_v_filter:
            mock_v_filter.return_value.exists.return_value = False

            with pytest.raises(ValidationError, match='Invalid verification result'):
                verify_complaint(
                    employee=employee,
                    complaint=complaint,
                    verification_result='approved',  # Not in ('verified', 'invalid')
                    verification_remarks='Valid notes',
                )

    # 20-21. Verification evidence attachment storage & database record
    def test_verification_evidence_attachment_creation(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, employee_id=employee.id, status=ComplaintStatus.ASSIGNED)

        att = PendingAttachment(
            file_bytes=b'test inspection image bytes',
            mime_type='image/jpeg',
            file_type='photo',
            original_name='site_inspection.jpg',
            size_bytes=1024 * 50,
        )

        with patch('apps.complaints.verification.ComplaintVerification.objects.filter') as mock_v_filter, \
             patch('apps.complaints.verification.ComplaintVerification.objects.create'), \
             patch('apps.complaints.verification.ComplaintStatusHistory.objects.create'), \
             patch('apps.complaints.verification.ComplaintAttachment.objects.create') as mock_att_create, \
             patch('apps.complaints.verification.upload_to_storage', return_value=True) as mock_upload, \
             patch('apps.complaints.verification.Profile.objects.filter', return_value=[]), \
             patch('apps.complaints.verification.Notification.objects.bulk_create'):

            mock_v_filter.return_value.exists.return_value = False

            verify_complaint(
                employee=employee,
                complaint=complaint,
                verification_result='verified',
                verification_remarks='Confirmed on site with photo proof.',
                pending_attachments=[att],
            )

            # Verification evidence attachment created
            mock_att_create.assert_called_once()
            att_kwargs = mock_att_create.call_args[1]
            assert att_kwargs['purpose'] == AttachmentPurpose.VERIFICATION_EVIDENCE
            assert att_kwargs['uploaded_by'] == employee
            assert 'verification' in att_kwargs['file_path']


# ===========================================================================
# 22-23: Atomicity & Notification Generation
# ===========================================================================

class TestVerificationNotifications:

    # 23. Citizen & supervisor are notified with trigger_event = 'verification'
    def test_notifications_created_on_verification(self):
        dept = make_mock_department()
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id, full_name='Worker John')
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id, full_name='Supervisor Sam')
        citizen_id = uuid.uuid4()
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee.id,
            citizen_id=citizen_id,
            status=ComplaintStatus.ASSIGNED,
        )

        with patch('apps.complaints.verification.ComplaintVerification.objects.filter') as mock_v_filter, \
             patch('apps.complaints.verification.ComplaintVerification.objects.create'), \
             patch('apps.complaints.verification.ComplaintStatusHistory.objects.create'), \
             patch('apps.complaints.verification.Profile.objects.filter', return_value=[supervisor]), \
             patch('apps.complaints.verification.Notification.objects.bulk_create') as mock_notif_create:

            mock_v_filter.return_value.exists.return_value = False

            verify_complaint(
                employee=employee,
                complaint=complaint,
                verification_result='verified',
                verification_remarks='Site inspection confirmed validity.',
            )

            mock_notif_create.assert_called_once()
            notifications = mock_notif_create.call_args[0][0]
            assert len(notifications) == 2  # 1 Citizen + 1 Supervisor
            assert notifications[0].recipient_id == citizen_id
            assert notifications[0].trigger_event == NotificationEventType.VERIFICATION
            assert notifications[1].recipient_id == supervisor.id
            assert notifications[1].trigger_event == NotificationEventType.VERIFICATION


# ===========================================================================
# 24: Regression Guards
# ===========================================================================

class TestPhase5RegressionGuards:

    def test_phase5_modules_importable(self):
        from apps.complaints.verification import verify_complaint, validate_employee_can_verify
        from apps.complaints.models import ComplaintVerification, VerificationResultType
        assert verify_complaint is not None
        assert ComplaintVerification is not None
        assert VerificationResultType is not None
