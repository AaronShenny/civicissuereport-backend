"""
core/permissions/roles.py

Reusable DRF permission classes for the Smart Public Complaint Management System.

Authorization is always enforced server-side.  The authenticated user's role
and department come from the verified Supabase JWT → public.profiles lookup
performed by SupabaseAuthentication.

Never trust role or department values sent by the React frontend.

Role hierarchy (ascending authority):
  citizen
  ground_level_employee
  supervisor
  department_admin
  system_admin
"""

from rest_framework.permissions import BasePermission
from apps.users.models import Role


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_profile(request):
    """
    Returns the Profile attached to the request by SupabaseAuthentication,
    or None if the user is not authenticated or has no profile loaded.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return None
    # SupabaseAuthentication attaches the profile as request.user after Phase 2
    # upgrade.  It falls back to None if profile lookup failed.
    profile = getattr(user, 'profile', None)
    return profile


def _has_role(request, role_name: str) -> bool:
    profile = _get_profile(request)
    if profile is None:
        return False
    return profile.role_name == role_name


def _has_any_role(request, role_names) -> bool:
    profile = _get_profile(request)
    if profile is None:
        return False
    return profile.role_name in role_names


# ---------------------------------------------------------------------------
# Base permission — requires Supabase authentication AND a loaded profile
# ---------------------------------------------------------------------------

class IsAuthenticatedViaSupabase(BasePermission):
    """
    Passes only when:
    1. The request carries a valid Supabase JWT.
    2. The JWT maps to an existing, active public.profiles record.
    """

    message = 'Authentication via Supabase JWT is required.'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            return False
        profile = getattr(user, 'profile', None)
        if profile is None:
            return False
        return profile.account_status == 'active'


# ---------------------------------------------------------------------------
# Role-level permission classes
# ---------------------------------------------------------------------------

class IsCitizen(BasePermission):
    """Passes for authenticated users with the 'citizen' role."""
    message = 'Citizen role required.'

    def has_permission(self, request, view):
        return _has_role(request, Role.CITIZEN)


class IsGroundLevelEmployee(BasePermission):
    """Passes for authenticated users with the 'ground_level_employee' role."""
    message = 'Ground-Level Employee role required.'

    def has_permission(self, request, view):
        return _has_role(request, Role.GROUND_LEVEL_EMPLOYEE)


class IsSupervisor(BasePermission):
    """Passes for authenticated users with the 'supervisor' role."""
    message = 'Supervisor role required.'

    def has_permission(self, request, view):
        return _has_role(request, Role.SUPERVISOR)


class IsDepartmentAdmin(BasePermission):
    """Passes for authenticated users with the 'department_admin' role."""
    message = 'Department Admin role required.'

    def has_permission(self, request, view):
        return _has_role(request, Role.DEPARTMENT_ADMIN)


class IsSystemAdmin(BasePermission):
    """Passes for authenticated users with the 'system_admin' role."""
    message = 'System Admin role required.'

    def has_permission(self, request, view):
        return _has_role(request, Role.SYSTEM_ADMIN)


class IsStaffMember(BasePermission):
    """
    Passes for any authenticated non-citizen role.
    (ground_level_employee | supervisor | department_admin | system_admin)
    """
    message = 'Staff member role required.'

    STAFF_ROLES = {
        Role.GROUND_LEVEL_EMPLOYEE,
        Role.SUPERVISOR,
        Role.DEPARTMENT_ADMIN,
        Role.SYSTEM_ADMIN,
    }

    def has_permission(self, request, view):
        return _has_any_role(request, self.STAFF_ROLES)


class IsDepartmentStaff(BasePermission):
    """
    Passes for roles that belong to a department:
    ground_level_employee | supervisor | department_admin
    (NOT system_admin — they are system-wide, not department-scoped)
    """
    message = 'Department staff role required.'

    DEPARTMENT_ROLES = {
        Role.GROUND_LEVEL_EMPLOYEE,
        Role.SUPERVISOR,
        Role.DEPARTMENT_ADMIN,
    }

    def has_permission(self, request, view):
        return _has_any_role(request, self.DEPARTMENT_ROLES)


class IsSupervisorOrAbove(BasePermission):
    """Passes for supervisor | department_admin | system_admin."""
    message = 'Supervisor or higher role required.'

    SUPERVISOR_PLUS = {
        Role.SUPERVISOR,
        Role.DEPARTMENT_ADMIN,
        Role.SYSTEM_ADMIN,
    }

    def has_permission(self, request, view):
        return _has_any_role(request, self.SUPERVISOR_PLUS)


class IsDepartmentAdminOrSystemAdmin(BasePermission):
    """Passes for department_admin | system_admin."""
    message = 'Department Admin or System Admin role required.'

    def has_permission(self, request, view):
        return _has_any_role(request, {Role.DEPARTMENT_ADMIN, Role.SYSTEM_ADMIN})


# ---------------------------------------------------------------------------
# Object-level permission — same-department check
# ---------------------------------------------------------------------------

class IsSameDepartment(BasePermission):
    """
    Object-level permission.

    Ensures a staff member can only act on objects that belong to their own
    department.  System Admins bypass this check (they are system-wide).

    Usage:
        permission_classes = [IsAuthenticatedViaSupabase, IsSameDepartment]

    The view object must expose a `department_id` attribute or a
    `get_department_id()` method.
    """
    message = 'Access is restricted to your own department.'

    def has_object_permission(self, request, view, obj):
        profile = _get_profile(request)
        if profile is None:
            return False

        # System admins have cross-department access.
        if profile.is_system_admin:
            return True

        # Resolve the object's department ID.
        if hasattr(obj, 'department_id'):
            obj_dept = obj.department_id
        elif hasattr(obj, 'department') and obj.department is not None:
            obj_dept = obj.department.id
        else:
            # Object has no department context — deny by default.
            return False

        return profile.department_id is not None and profile.department_id == obj_dept


# ---------------------------------------------------------------------------
# Object-level permission — own profile only
# ---------------------------------------------------------------------------

class IsOwnProfile(BasePermission):
    """
    Object-level permission.
    Ensures a user can only access/modify their own profile.
    System admins may access any profile.
    """
    message = 'You can only access your own profile.'

    def has_object_permission(self, request, view, obj):
        profile = _get_profile(request)
        if profile is None:
            return False
        if profile.is_system_admin:
            return True
        # obj is a Profile instance.
        return str(obj.id) == str(profile.id)


# ---------------------------------------------------------------------------
# Helper functions (for use inside service/view code)
# ---------------------------------------------------------------------------

def user_is_system_admin(profile) -> bool:
    return profile is not None and profile.is_system_admin


def user_is_department_admin(profile) -> bool:
    return profile is not None and profile.is_department_admin


def user_is_supervisor(profile) -> bool:
    return profile is not None and profile.is_supervisor


def user_is_ground_level_employee(profile) -> bool:
    return profile is not None and profile.is_ground_level_employee


def user_is_citizen(profile) -> bool:
    return profile is not None and profile.is_citizen


def profiles_share_department(profile_a, profile_b) -> bool:
    """
    Returns True when both profiles belong to the same department.
    Used to validate supervisor–employee relationships.
    """
    if profile_a is None or profile_b is None:
        return False
    if profile_a.department_id is None or profile_b.department_id is None:
        return False
    return profile_a.department_id == profile_b.department_id


# ---------------------------------------------------------------------------
# Object-level permission — assigned employee or department supervisor
# ---------------------------------------------------------------------------

class IsAssignedEmployeeOrDepartmentSupervisor(BasePermission):
    """
    Passes for active Ground-Level Employees or active Supervisors.
    Object-level checks (in has_object_permission) enforce that:
      - Ground-level employee is assigned to the complaint (complaint.assigned_employee_id == user.id)
      - Supervisor belongs to the assigned department (supervisor.department_id == complaint.assigned_department_id)
    """
    message = 'Only the assigned Ground-Level Employee or authorized Department Supervisor can perform this action.'

    def has_permission(self, request, view):
        profile = _get_profile(request)
        if profile is None or profile.account_status != 'active':
            return False
        return profile.role_name in {Role.GROUND_LEVEL_EMPLOYEE, Role.SUPERVISOR}

    def has_object_permission(self, request, view, obj):
        profile = _get_profile(request)
        if profile is None or profile.account_status != 'active':
            return False

        # obj is a Complaint instance
        if profile.role_name == Role.GROUND_LEVEL_EMPLOYEE:
            return bool(
                obj.assigned_employee_id is not None
                and str(obj.assigned_employee_id) == str(profile.id)
            )
        elif profile.role_name == Role.SUPERVISOR:
            return bool(
                profile.department_id is not None
                and obj.assigned_department_id is not None
                and str(profile.department_id) == str(obj.assigned_department_id)
            )
        return False

