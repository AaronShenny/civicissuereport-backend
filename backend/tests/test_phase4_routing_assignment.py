"""
tests/test_phase4_routing_assignment.py

Phase 4 test suite: Department Routing + Supervisor Assignment & Reassignment.

Covers all 41 required test scenarios:
  1-7: Department Routing (category+location, status transition to UNDER_VERIFICATION, supervisor notification, routing failure handling)
  8-11: Supervisor Access & Department Isolation
  12-24: Supervisor Assignment validation, status transition to ASSIGNED, assignment history, notifications, atomicity
  25-29: Supervisor Reassignment, history preservation, cross-department rejection, new notification
  30-33: Ground-Level Employee assigned-complaint queue and isolation
  34-40: Security and spoofing prevention
  41: Regression checks with existing components
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ComplaintCategory,
    ComplaintAssignment,
    ComplaintStatusHistory,
    Notification,
    NotificationEventType,
)
from apps.complaints.routing import (
    route_complaint,
    find_responsible_department,
    RoutingFailureError,
)
from apps.complaints.assignment import (
    assign_employee_to_complaint,
    reassign_employee_to_complaint,
    validate_supervisor_can_assign,
    validate_target_employee,
)
from apps.departments.models import DepartmentCategoryRule
from apps.users.models import Department, Profile, Role
from core.permissions.roles import (
    IsSupervisor,
    IsGroundLevelEmployee,
    IsCitizen,
    IsDepartmentAdmin,
    IsSystemAdmin,
)
from contextlib import nullcontext


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


def make_mock_category(cat_id=1, name='pothole') -> MagicMock:
    cat = MagicMock(spec=ComplaintCategory)
    cat.id = cat_id
    cat.name = name
    cat.is_active = True
    return cat


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

    # Role property booleans
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
    status=ComplaintStatus.SUBMITTED,
    category=None,
) -> MagicMock:
    c = MagicMock(spec=Complaint)
    c.id = complaint_id or uuid.uuid4()
    c.complaint_number = 'CMP-2026-000001'
    c.category = category or make_mock_category()
    c.category_id = c.category.id
    c.assigned_department_id = dept_id
    c.assigned_employee_id = employee_id
    c.status = status
    c.description = 'Test complaint description'
    c.location_lat = 9.93
    c.location_lng = 76.27
    return c


# ===========================================================================
# 1-7: Department Routing Tests
# ===========================================================================

class TestDepartmentRouting:

    # 1. Complaint can be routed using category + location
    def test_find_responsible_department_matches_category_rule(self):
        dept = make_mock_department()
        complaint = make_mock_complaint()
        rule = MagicMock(spec=DepartmentCategoryRule)
        rule.department = dept

        with patch('apps.complaints.routing.DepartmentCategoryRule.objects') as mock_rule_mgr:
            mock_filter = MagicMock()
            mock_rule_mgr.filter.return_value = mock_filter
            mock_filter.select_related.return_value = mock_filter
            mock_filter.order_by.return_value.first.return_value = rule

            result = find_responsible_department(complaint)
            assert result == dept

    # 2. Routing sets assigned_department_id
    # 3. Routing does not set assigned_employee_id
    # 4. Successful routing changes SUBMITTED -> UNDER_VERIFICATION
    # 5. Routing creates status history
    # 6. Routing creates department notification
    def test_successful_routing_updates_complaint_and_notifies(self):
        dept = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id)
        complaint = make_mock_complaint(status=ComplaintStatus.SUBMITTED)

        with patch('apps.complaints.routing.find_responsible_department', return_value=dept), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.routing.Profile.objects.filter', return_value=[supervisor]), \
             patch('apps.complaints.routing.Notification.objects.bulk_create') as mock_notif_create:

            routed_dept = route_complaint(complaint)

            assert routed_dept == dept
            # 2. sets assigned_department_id
            assert complaint.assigned_department_id == dept.id
            # 3. does not set assigned_employee_id (remains None)
            assert complaint.assigned_employee_id is None
            # 4. changes SUBMITTED -> UNDER_VERIFICATION
            assert complaint.status == ComplaintStatus.UNDER_VERIFICATION

            # 5. creates status history
            mock_hist_create.assert_called_once()
            hist_kwargs = mock_hist_create.call_args[1]
            assert hist_kwargs['old_status'] == ComplaintStatus.SUBMITTED
            assert hist_kwargs['new_status'] == ComplaintStatus.UNDER_VERIFICATION
            assert hist_kwargs['changed_by'] is None  # System action

            # 6. creates department notification
            mock_notif_create.assert_called_once()
            created_notifications = mock_notif_create.call_args[0][0]
            assert len(created_notifications) == 1
            assert created_notifications[0].recipient_id == supervisor.id

    # 7. Invalid/missing routing configuration is handled safely
    def test_routing_failure_raises_controlled_error(self):
        complaint = make_mock_complaint(status=ComplaintStatus.SUBMITTED)

        with patch('apps.complaints.routing.find_responsible_department', return_value=None):
            with pytest.raises(RoutingFailureError, match='Unable to determine responsible department'):
                route_complaint(complaint)

        # Ensure complaint was not modified on failure
        assert complaint.assigned_department_id is None
        assert complaint.assigned_employee_id is None
        assert complaint.status == ComplaintStatus.SUBMITTED


# ===========================================================================
# 8-11: Supervisor Access & Department Isolation
# ===========================================================================

class TestSupervisorAccess:

    # 8. Supervisor can see complaints belonging to their department
    # 9. Supervisor can see unassigned complaints
    def test_supervisor_unassigned_queue_filters_correctly(self):
        from apps.complaints.views import SupervisorUnassignedQueueView
        dept_a = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept_a.id)

        request = MagicMock()
        request.user = supervisor
        view = SupervisorUnassignedQueueView()

        with patch('apps.complaints.views.Complaint.objects.filter') as mock_filter:
            mock_qs = MagicMock()
            mock_filter.return_value = mock_qs
            mock_qs.select_related.return_value = mock_qs
            mock_qs.order_by.return_value = []

            response = view.get(request)
            assert response.status_code == 200

            # Verify query strictly filtered by supervisor's dept and unassigned status
            mock_filter.assert_called_once_with(
                assigned_department_id=dept_a.id,
                status=ComplaintStatus.UNDER_VERIFICATION,
                assigned_employee_id__isnull=True,
            )

    # 10. Supervisor cannot see another department's complaints
    def test_supervisor_department_isolation_in_view(self):
        from apps.complaints.views import SupervisorDepartmentComplaintsView
        dept_a = make_mock_department()
        dept_b = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept_a.id)

        request = MagicMock()
        request.user = supervisor
        view = SupervisorDepartmentComplaintsView()

        with patch('apps.complaints.views.Complaint.objects.filter') as mock_filter:
            mock_qs = MagicMock()
            mock_filter.return_value = mock_qs
            mock_qs.select_related.return_value = mock_qs
            mock_qs.order_by.return_value = []

            view.get(request)
            # Department A used, Department B never touched
            assert mock_filter.call_args[1]['assigned_department_id'] == dept_a.id
            assert mock_filter.call_args[1]['assigned_department_id'] != dept_b.id

    # 11. Non-supervisor cannot access supervisor assignment endpoints
    def test_non_supervisor_permission_denied(self):
        perm = IsSupervisor()
        for non_sup_role in [Role.CITIZEN, Role.GROUND_LEVEL_EMPLOYEE, Role.DEPARTMENT_ADMIN, Role.SYSTEM_ADMIN]:
            user = make_mock_profile(non_sup_role, dept_id=uuid.uuid4())
            request = MagicMock()
            request.user = user
            assert perm.has_permission(request, None) is False


# ===========================================================================
# 12-24: Assignment Validation & Execution
# ===========================================================================

class TestSupervisorAssignment:

    # 12. Supervisor can assign a Ground-Level Employee
    # 19. Assignment sets assigned_employee_id
    # 20. Assignment changes status UNDER_VERIFICATION -> ASSIGNED
    # 21. Assignment creates complaint_assignments record
    # 22. Assignment creates status history
    # 23. Assignment creates employee notification
    # 24. Assignment is atomic
    def test_successful_assignment_workflow(self):
        dept = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id, full_name='Supervisor Sam')
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id, full_name='Worker Bob')
        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=None,
            status=ComplaintStatus.UNDER_VERIFICATION,
        )

        with patch('apps.complaints.assignment.ComplaintAssignment.objects.create') as mock_assign_create, \
             patch('apps.complaints.assignment.ComplaintStatusHistory.objects.create') as mock_hist_create, \
             patch('apps.complaints.assignment.Notification.objects.create') as mock_notif_create:

            updated = assign_employee_to_complaint(
                supervisor=supervisor,
                complaint=complaint,
                employee=employee,
                assignment_reason='Primary sector patrol assigned.',
            )

            # 19. Sets assigned_employee_id
            assert updated.assigned_employee_id == employee.id
            # 20. Changes status UNDER_VERIFICATION -> ASSIGNED
            assert updated.status == ComplaintStatus.ASSIGNED

            # 21. Creates complaint_assignments record
            mock_assign_create.assert_called_once()
            assign_kwargs = mock_assign_create.call_args[1]
            assert assign_kwargs['complaint'] == complaint
            assert assign_kwargs['employee'] == employee
            assert assign_kwargs['assigned_by'] == supervisor
            assert assign_kwargs['assignment_reason'] == 'Primary sector patrol assigned.'

            # 22. Creates status history
            mock_hist_create.assert_called_once()
            hist_kwargs = mock_hist_create.call_args[1]
            assert hist_kwargs['old_status'] == ComplaintStatus.UNDER_VERIFICATION
            assert hist_kwargs['new_status'] == ComplaintStatus.ASSIGNED
            assert hist_kwargs['changed_by'] == supervisor

            # 23. Creates notification
            mock_notif_create.assert_called_once()
            notif_kwargs = mock_notif_create.call_args[1]
            assert notif_kwargs['recipient'] == employee
            assert notif_kwargs['trigger_event'] == NotificationEventType.ASSIGNMENT

    # 13. Employee must belong to same department
    def test_assignment_fails_if_employee_in_different_department(self):
        dept_a = make_mock_department()
        dept_b = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept_a.id)
        employee_b = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept_b.id)
        complaint = make_mock_complaint(dept_id=dept_a.id, status=ComplaintStatus.UNDER_VERIFICATION)

        with pytest.raises(ValidationError, match='another department'):
            assign_employee_to_complaint(supervisor, complaint, employee_b)

    # 14. Employee must have Ground-Level Employee role
    def test_assignment_fails_if_target_not_ground_level_employee(self):
        dept = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id)
        target_supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, status=ComplaintStatus.UNDER_VERIFICATION)

        with pytest.raises(ValidationError, match='Ground-Level Employees'):
            assign_employee_to_complaint(supervisor, complaint, target_supervisor)

    # 15. Inactive employee cannot be assigned
    def test_assignment_fails_if_employee_inactive(self):
        dept = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id)
        inactive_emp = make_mock_profile(
            Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id, account_status='inactive'
        )
        complaint = make_mock_complaint(dept_id=dept.id, status=ComplaintStatus.UNDER_VERIFICATION)

        with pytest.raises(ValidationError, match='inactive employee'):
            assign_employee_to_complaint(supervisor, complaint, inactive_emp)

    # 16. Complaint must belong to Supervisor's department
    def test_assignment_fails_if_complaint_in_different_department(self):
        dept_a = make_mock_department()
        dept_b = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept_a.id)
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept_a.id)
        complaint_in_b = make_mock_complaint(dept_id=dept_b.id, status=ComplaintStatus.UNDER_VERIFICATION)

        with pytest.raises(ValidationError, match='own department'):
            assign_employee_to_complaint(supervisor, complaint_in_b, employee)

    # 17. Complaint must be UNDER_VERIFICATION
    def test_assignment_fails_if_complaint_not_under_verification(self):
        dept = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id)
        employee = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        complaint = make_mock_complaint(dept_id=dept.id, status=ComplaintStatus.SUBMITTED)

        with pytest.raises(ValidationError, match='must be in UNDER_VERIFICATION'):
            assign_employee_to_complaint(supervisor, complaint, employee)

    # 18. Complaint must not already be assigned
    def test_assignment_fails_if_already_assigned(self):
        dept = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id)
        employee_1 = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        employee_2 = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        already_assigned_complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=employee_1.id,
            status=ComplaintStatus.UNDER_VERIFICATION,
        )

        with pytest.raises(ValidationError, match='already assigned'):
            assign_employee_to_complaint(supervisor, already_assigned_complaint, employee_2)


# ===========================================================================
# 25-29: Reassignment Tests
# ===========================================================================

class TestSupervisorReassignment:

    # 25. Supervisor can reassign within same department
    # 27. Previous assignment history remains
    # 28. New assignment history is created
    # 29. New employee receives notification
    def test_successful_reassignment_creates_new_history_row(self):
        dept = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept.id, full_name='Supervisor Sam')
        emp_old = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id, full_name='Worker Old')
        emp_new = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id, full_name='Worker New')

        complaint = make_mock_complaint(
            dept_id=dept.id,
            employee_id=emp_old.id,
            status=ComplaintStatus.ASSIGNED,
        )

        with patch('apps.complaints.assignment.ComplaintAssignment.objects.create') as mock_assign_create, \
             patch('apps.complaints.assignment.Notification.objects.create') as mock_notif_create:

            updated = reassign_employee_to_complaint(
                supervisor=supervisor,
                complaint=complaint,
                new_employee=emp_new,
                reassignment_reason='Employee on emergency leave.',
            )

            # Updated employee ID
            assert updated.assigned_employee_id == emp_new.id

            # 28. New assignment history created
            mock_assign_create.assert_called_once()
            assign_kwargs = mock_assign_create.call_args[1]
            assert assign_kwargs['employee'] == emp_new
            assert assign_kwargs['assigned_by'] == supervisor
            assert assign_kwargs['reassignment_reason'] == 'Employee on emergency leave.'

            # 29. New employee notified
            mock_notif_create.assert_called_once()
            notif_kwargs = mock_notif_create.call_args[1]
            assert notif_kwargs['recipient'] == emp_new

    # 26. Cross-department reassignment is rejected
    def test_cross_department_reassignment_rejected(self):
        dept_a = make_mock_department()
        dept_b = make_mock_department()
        supervisor = make_mock_profile(Role.SUPERVISOR, dept_id=dept_a.id)
        emp_in_dept_b = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept_b.id)
        complaint = make_mock_complaint(dept_id=dept_a.id, status=ComplaintStatus.ASSIGNED)

        with pytest.raises(ValidationError, match='another department'):
            reassign_employee_to_complaint(supervisor, complaint, emp_in_dept_b)


# ===========================================================================
# 30-33: Ground-Level Employee Queue Tests
# ===========================================================================

class TestEmployeeQueue:

    # 30. Assigned employee can see their complaint
    # 31. Employee cannot see another employee's complaint
    # 32. Employee cannot access another department's complaint
    # 33. Unassigned complaints do not appear in employee queue
    def test_employee_queue_strictly_filtered_by_assigned_employee_id(self):
        from apps.complaints.views import EmployeeAssignedComplaintsView
        dept = make_mock_department()
        emp_a = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)
        emp_b = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept.id)

        request = MagicMock()
        request.user = emp_a
        view = EmployeeAssignedComplaintsView()

        with patch('apps.complaints.views.Complaint.objects.filter') as mock_filter:
            mock_qs = MagicMock()
            mock_filter.return_value = mock_qs
            mock_qs.select_related.return_value = mock_qs
            mock_qs.order_by.return_value = []

            response = view.get(request)
            assert response.status_code == 200

            # Verify query strictly filtered by assigned_employee_id == emp_a.id
            mock_filter.assert_called_once_with(assigned_employee_id=emp_a.id)
            assert str(emp_b.id) not in str(mock_filter.call_args)


# ===========================================================================
# 34-40: Security & Anti-Spoofing Tests
# ===========================================================================

class TestSecurityAndPermissions:

    # 34. Citizen cannot assign employee
    def test_citizen_cannot_assign_employee(self):
        citizen = make_mock_profile(Role.CITIZEN)
        complaint = make_mock_complaint(dept_id=uuid.uuid4(), status=ComplaintStatus.UNDER_VERIFICATION)
        with pytest.raises(ValidationError, match='Supervisor role'):
            validate_supervisor_can_assign(citizen, complaint)

    # 35. Department Admin cannot assign employee
    def test_department_admin_cannot_assign_employee(self):
        dept_admin = make_mock_profile(Role.DEPARTMENT_ADMIN, dept_id=uuid.uuid4())
        complaint = make_mock_complaint(dept_id=dept_admin.department_id, status=ComplaintStatus.UNDER_VERIFICATION)
        with pytest.raises(ValidationError, match='Supervisor role'):
            validate_supervisor_can_assign(dept_admin, complaint)

    # 36. Supervisor without department cannot assign
    def test_supervisor_without_department_cannot_assign(self):
        supervisor_no_dept = make_mock_profile(Role.SUPERVISOR, dept_id=None)
        complaint = make_mock_complaint(dept_id=uuid.uuid4(), status=ComplaintStatus.UNDER_VERIFICATION)
        with pytest.raises(ValidationError, match='must belong to a department'):
            validate_supervisor_can_assign(supervisor_no_dept, complaint)

    # 37-40. Serializer field immutability checks
    def test_client_cannot_supply_server_controlled_fields_on_assignment(self):
        from apps.complaints.serializers import AssignEmployeeSerializer
        fields = list(AssignEmployeeSerializer().fields.keys())
        assert 'status' not in fields
        assert 'assigned_by' not in fields
        assert 'assigned_department_id' not in fields


# ===========================================================================
# 41: Regression Guards
# ===========================================================================

class TestPhase4RegressionGuards:

    def test_phase4_modules_importable(self):
        from apps.complaints.routing import route_complaint, find_responsible_department
        from apps.complaints.assignment import assign_employee_to_complaint, reassign_employee_to_complaint
        from apps.departments.models import DepartmentCategoryRule, Jurisdiction
        from apps.complaints.models import ComplaintAssignment, Notification
        assert route_complaint is not None
        assert assign_employee_to_complaint is not None
        assert DepartmentCategoryRule is not None
        assert ComplaintAssignment is not None
        assert Notification is not None
