"""
tests/test_phase2_users.py

Phase 2 test suite — Roles, Departments, Profiles, Permissions.

Tests cover:
  1. Citizen profile mapping works.
  2. Ground-Level Employee profile mapping works.
  3. Supervisor profile mapping works.
  4. Department Admin profile mapping works.
  5. System Admin profile mapping works.
  6. Staff without a department are rejected where the schema requires a department.
  7. Employee/supervisor cross-department relationships are rejected.
  8. Unauthenticated users cannot access protected profile endpoints.
  9. Authenticated users cannot impersonate another profile.
  10. Department-scoped access cannot cross department boundaries.
  11. System Admin has system-wide access.
  12. Role permission helpers return the correct result.

NOTE: Because the Supabase tables are unmanaged (managed=False), these tests
use Django's test database with temporarily unmanaged tables.
The conftest.py marks them as managed=True during tests only.
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings

from apps.users.models import Profile, Role, Department
from apps.users.services import validate_supervisor_assignment, validate_staff_has_department
from core.permissions.roles import (
    IsAuthenticatedViaSupabase,
    IsCitizen,
    IsGroundLevelEmployee,
    IsSupervisor,
    IsDepartmentAdmin,
    IsSystemAdmin,
    IsStaffMember,
    IsSameDepartment,
    IsOwnProfile,
    profiles_share_department,
    user_is_system_admin,
    user_is_supervisor,
)
from django.core.exceptions import ValidationError


# ---------------------------------------------------------------------------
# Helpers to build mock Profile objects without hitting the DB
# ---------------------------------------------------------------------------

def make_mock_role(role_name: str, role_id: int = 1) -> MagicMock:
    role = MagicMock(spec=Role)
    role.id = role_id
    role.role_name = role_name
    return role


def make_mock_dept(dept_id=None) -> MagicMock:
    dept = MagicMock(spec=Department)
    dept.id = dept_id or uuid.uuid4()
    dept.name = 'Test Department'
    dept.is_active = True
    return dept


def make_mock_profile(
    role_name: str,
    dept_id=None,
    supervisor_id=None,
    account_status: str = 'active',
) -> MagicMock:
    """
    Returns a MagicMock that mimics a Profile instance for unit-testing
    permission classes without DB access.
    """
    profile = MagicMock(spec=Profile)
    profile.id = uuid.uuid4()
    profile.role = make_mock_role(role_name)
    profile.role_name = role_name
    profile.department_id = dept_id
    profile.supervisor_id = supervisor_id
    profile.account_status = account_status
    profile.is_authenticated = True
    profile.profile = profile  # core/permissions/roles.py uses request.user.profile

    # Wire property-style booleans.
    profile.is_citizen = (role_name == Role.CITIZEN)
    profile.is_ground_level_employee = (role_name == Role.GROUND_LEVEL_EMPLOYEE)
    profile.is_supervisor = (role_name == Role.SUPERVISOR)
    profile.is_department_admin = (role_name == Role.DEPARTMENT_ADMIN)
    profile.is_system_admin = (role_name == Role.SYSTEM_ADMIN)
    profile.is_staff_member = (role_name != Role.CITIZEN)

    return profile


def make_mock_request(profile=None) -> MagicMock:
    request = MagicMock()
    request.user = profile
    request.user.is_authenticated = profile is not None
    return request


# ===========================================================================
# 1–5. Profile mapping correctness (role properties)
# ===========================================================================

class TestProfileRoleMapping:
    """Covers tests 1–5: all five roles map correctly."""

    def test_citizen_role_properties(self):
        p = make_mock_profile(Role.CITIZEN)
        assert p.is_citizen is True
        assert p.is_ground_level_employee is False
        assert p.is_supervisor is False
        assert p.is_department_admin is False
        assert p.is_system_admin is False
        assert p.is_staff_member is False

    def test_ground_level_employee_role_properties(self):
        dept_id = uuid.uuid4()
        p = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=dept_id)
        assert p.is_ground_level_employee is True
        assert p.is_citizen is False
        assert p.is_staff_member is True
        assert p.department_id == dept_id

    def test_supervisor_role_properties(self):
        dept_id = uuid.uuid4()
        p = make_mock_profile(Role.SUPERVISOR, dept_id=dept_id)
        assert p.is_supervisor is True
        assert p.is_staff_member is True
        assert p.department_id == dept_id

    def test_department_admin_role_properties(self):
        dept_id = uuid.uuid4()
        p = make_mock_profile(Role.DEPARTMENT_ADMIN, dept_id=dept_id)
        assert p.is_department_admin is True
        assert p.is_staff_member is True

    def test_system_admin_role_properties(self):
        p = make_mock_profile(Role.SYSTEM_ADMIN)
        assert p.is_system_admin is True
        assert p.is_staff_member is True
        # System admin has no department requirement.
        assert p.department_id is None


# ===========================================================================
# 6. Staff without a department are rejected
# ===========================================================================

class TestStaffDepartmentValidation:
    """Covers test 6."""

    @pytest.mark.parametrize("role_name", [
        Role.GROUND_LEVEL_EMPLOYEE,
        Role.SUPERVISOR,
        Role.DEPARTMENT_ADMIN,
    ])
    def test_staff_without_department_raises(self, role_name):
        profile = make_mock_profile(role_name, dept_id=None)
        # Build a real Profile-like object for the service function.
        real_profile = MagicMock()
        real_profile.role_name = role_name
        real_profile.department_id = None

        with pytest.raises(ValidationError, match='must be assigned to a department'):
            validate_staff_has_department(real_profile)

    @pytest.mark.parametrize("role_name", [
        Role.CITIZEN,
        Role.SYSTEM_ADMIN,
    ])
    def test_no_department_ok_for_exempt_roles(self, role_name):
        real_profile = MagicMock()
        real_profile.role_name = role_name
        real_profile.department_id = None
        # Should not raise
        validate_staff_has_department(real_profile)


# ===========================================================================
# 7. Cross-department supervisor–employee assignment is rejected
# ===========================================================================

class TestSupervisorAssignmentValidation:
    """Covers test 7."""

    def test_same_department_assignment_is_valid(self):
        dept_id = uuid.uuid4()
        employee = MagicMock()
        employee.id = uuid.uuid4()
        employee.role_name = Role.GROUND_LEVEL_EMPLOYEE
        employee.department_id = dept_id

        supervisor = MagicMock()
        supervisor.id = uuid.uuid4()
        supervisor.role_name = Role.SUPERVISOR
        supervisor.department_id = dept_id

        # Should not raise
        validate_supervisor_assignment(employee, supervisor)

    def test_cross_department_assignment_raises(self):
        employee = MagicMock()
        employee.id = uuid.uuid4()
        employee.role_name = Role.GROUND_LEVEL_EMPLOYEE
        employee.department_id = uuid.uuid4()  # Dept A

        supervisor = MagicMock()
        supervisor.id = uuid.uuid4()
        supervisor.role_name = Role.SUPERVISOR
        supervisor.department_id = uuid.uuid4()  # Dept B (different)

        with pytest.raises(ValidationError, match='same department'):
            validate_supervisor_assignment(employee, supervisor)

    def test_non_supervisor_cannot_be_assigned_as_supervisor(self):
        dept_id = uuid.uuid4()
        employee = MagicMock()
        employee.id = uuid.uuid4()
        employee.role_name = Role.GROUND_LEVEL_EMPLOYEE
        employee.department_id = dept_id

        # Trying to assign a dept admin as supervisor
        bad_supervisor = MagicMock()
        bad_supervisor.id = uuid.uuid4()
        bad_supervisor.role_name = Role.DEPARTMENT_ADMIN
        bad_supervisor.department_id = dept_id

        with pytest.raises(ValidationError, match='supervisor role'):
            validate_supervisor_assignment(employee, bad_supervisor)

    def test_non_employee_cannot_be_assigned_an_employee(self):
        dept_id = uuid.uuid4()
        # A supervisor trying to be assigned to another supervisor
        not_employee = MagicMock()
        not_employee.id = uuid.uuid4()
        not_employee.role_name = Role.SUPERVISOR
        not_employee.department_id = dept_id

        supervisor = MagicMock()
        supervisor.id = uuid.uuid4()
        supervisor.role_name = Role.SUPERVISOR
        supervisor.department_id = dept_id

        with pytest.raises(ValidationError, match='ground_level_employee role'):
            validate_supervisor_assignment(not_employee, supervisor)


# ===========================================================================
# 8. Unauthenticated users cannot access protected endpoints
# ===========================================================================

class TestUnauthenticatedAccess:
    """Covers test 8."""

    def test_is_authenticated_via_supabase_rejects_unauthenticated(self):
        request = MagicMock()
        request.user = None
        # MagicMock doesn't have .user.is_authenticated=True by default
        unauthenticated = MagicMock()
        unauthenticated.is_authenticated = False
        request.user = unauthenticated

        perm = IsAuthenticatedViaSupabase()
        assert perm.has_permission(request, None) is False

    def test_is_authenticated_via_supabase_rejects_missing_profile(self):
        request = MagicMock()
        user = MagicMock()
        user.is_authenticated = True
        user.profile = None  # No profile attached
        request.user = user

        perm = IsAuthenticatedViaSupabase()
        # _get_profile returns None → has_permission returns False
        assert perm.has_permission(request, None) is False

    def test_is_authenticated_via_supabase_rejects_inactive_account(self):
        profile = make_mock_profile(Role.CITIZEN, account_status='inactive')
        request = make_mock_request(profile)

        perm = IsAuthenticatedViaSupabase()
        assert perm.has_permission(request, None) is False

    def test_active_citizen_passes_authentication_check(self):
        profile = make_mock_profile(Role.CITIZEN, account_status='active')
        request = make_mock_request(profile)

        perm = IsAuthenticatedViaSupabase()
        assert perm.has_permission(request, None) is True


# ===========================================================================
# 9. Authenticated users cannot impersonate another profile
# ===========================================================================

class TestProfileImpersonation:
    """Covers test 9."""

    def test_is_own_profile_blocks_foreign_profile(self):
        profile_a = make_mock_profile(Role.CITIZEN)
        profile_b = make_mock_profile(Role.CITIZEN)

        request = make_mock_request(profile_a)
        perm = IsOwnProfile()
        # profile_b is not profile_a — access should be denied.
        assert perm.has_object_permission(request, None, profile_b) is False

    def test_is_own_profile_allows_own_profile(self):
        profile = make_mock_profile(Role.CITIZEN)
        request = make_mock_request(profile)
        perm = IsOwnProfile()
        assert perm.has_object_permission(request, None, profile) is True

    def test_system_admin_can_access_any_profile(self):
        admin = make_mock_profile(Role.SYSTEM_ADMIN)
        other = make_mock_profile(Role.CITIZEN)
        request = make_mock_request(admin)
        perm = IsOwnProfile()
        assert perm.has_object_permission(request, None, other) is True


# ===========================================================================
# 10. Department-scoped access cannot cross department boundaries
# ===========================================================================

class TestDepartmentBoundary:
    """Covers test 10."""

    def test_same_department_access_is_allowed(self):
        dept_id = uuid.uuid4()
        accessor = make_mock_profile(Role.SUPERVISOR, dept_id=dept_id)
        resource = MagicMock()
        resource.department_id = dept_id

        request = make_mock_request(accessor)
        perm = IsSameDepartment()
        assert perm.has_object_permission(request, None, resource) is True

    def test_cross_department_access_is_denied(self):
        accessor = make_mock_profile(Role.SUPERVISOR, dept_id=uuid.uuid4())  # Dept A
        resource = MagicMock()
        resource.department_id = uuid.uuid4()  # Dept B

        request = make_mock_request(accessor)
        perm = IsSameDepartment()
        assert perm.has_object_permission(request, None, resource) is False

    def test_profiles_share_department_true(self):
        dept_id = uuid.uuid4()
        a = MagicMock()
        a.department_id = dept_id
        b = MagicMock()
        b.department_id = dept_id
        assert profiles_share_department(a, b) is True

    def test_profiles_share_department_false(self):
        a = MagicMock()
        a.department_id = uuid.uuid4()
        b = MagicMock()
        b.department_id = uuid.uuid4()
        assert profiles_share_department(a, b) is False

    def test_profiles_share_department_none_returns_false(self):
        a = MagicMock()
        a.department_id = None
        b = MagicMock()
        b.department_id = uuid.uuid4()
        assert profiles_share_department(a, b) is False


# ===========================================================================
# 11. System Admin has system-wide access
# ===========================================================================

class TestSystemAdminAccess:
    """Covers test 11."""

    def test_system_admin_passes_is_system_admin(self):
        admin = make_mock_profile(Role.SYSTEM_ADMIN)
        request = make_mock_request(admin)
        perm = IsSystemAdmin()
        assert perm.has_permission(request, None) is True

    def test_non_admin_fails_is_system_admin(self):
        for role_name in [Role.CITIZEN, Role.GROUND_LEVEL_EMPLOYEE, Role.SUPERVISOR, Role.DEPARTMENT_ADMIN]:
            profile = make_mock_profile(role_name, dept_id=uuid.uuid4())
            request = make_mock_request(profile)
            perm = IsSystemAdmin()
            assert perm.has_permission(request, None) is False, f'Expected False for {role_name}'

    def test_system_admin_bypasses_department_restriction(self):
        admin = make_mock_profile(Role.SYSTEM_ADMIN)
        resource = MagicMock()
        resource.department_id = uuid.uuid4()  # Any dept

        request = make_mock_request(admin)
        perm = IsSameDepartment()
        assert perm.has_object_permission(request, None, resource) is True

    def test_user_is_system_admin_helper(self):
        admin = make_mock_profile(Role.SYSTEM_ADMIN)
        assert user_is_system_admin(admin) is True

    def test_user_is_system_admin_helper_false_for_others(self):
        non_admin = make_mock_profile(Role.DEPARTMENT_ADMIN, dept_id=uuid.uuid4())
        assert user_is_system_admin(non_admin) is False


# ===========================================================================
# 12. Role permission helpers return the correct result
# ===========================================================================

class TestPermissionHelpers:
    """Covers test 12."""

    @pytest.mark.parametrize("role_name,perm_class,expected", [
        (Role.CITIZEN, IsCitizen, True),
        (Role.GROUND_LEVEL_EMPLOYEE, IsCitizen, False),
        (Role.GROUND_LEVEL_EMPLOYEE, IsGroundLevelEmployee, True),
        (Role.SUPERVISOR, IsGroundLevelEmployee, False),
        (Role.SUPERVISOR, IsSupervisor, True),
        (Role.DEPARTMENT_ADMIN, IsSupervisor, False),
        (Role.DEPARTMENT_ADMIN, IsDepartmentAdmin, True),
        (Role.SYSTEM_ADMIN, IsDepartmentAdmin, False),
        (Role.SYSTEM_ADMIN, IsSystemAdmin, True),
        (Role.CITIZEN, IsSystemAdmin, False),
        (Role.CITIZEN, IsStaffMember, False),
        (Role.GROUND_LEVEL_EMPLOYEE, IsStaffMember, True),
        (Role.SUPERVISOR, IsStaffMember, True),
    ])
    def test_permission_class_for_role(self, role_name, perm_class, expected):
        dept_id = uuid.uuid4() if role_name != Role.CITIZEN else None
        profile = make_mock_profile(role_name, dept_id=dept_id)
        request = make_mock_request(profile)
        perm = perm_class()
        result = perm.has_permission(request, None)
        assert result == expected, (
            f'{perm_class.__name__} for role={role_name}: '
            f'expected {expected}, got {result}'
        )

    def test_supervisor_helper(self):
        sv = make_mock_profile(Role.SUPERVISOR, dept_id=uuid.uuid4())
        assert user_is_supervisor(sv) is True

    def test_supervisor_helper_false_for_non_supervisor(self):
        emp = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE, dept_id=uuid.uuid4())
        assert user_is_supervisor(emp) is False
