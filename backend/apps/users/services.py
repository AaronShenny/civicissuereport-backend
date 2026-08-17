"""
apps/users/services.py

Business logic for user/profile operations.

All validation that must not live in views or serializers lives here.
Views delegate to services; services own the business rules.
"""

from django.core.exceptions import ValidationError
from apps.users.models import Profile, Role
from core.permissions.roles import profiles_share_department


def validate_supervisor_assignment(employee_profile: Profile, supervisor_profile: Profile) -> None:
    """
    Validates that a supervisor assignment is legal.

    Rules enforced (from database_schema.md and User Stories):
    1. The supervisor must have the 'supervisor' role.
    2. The employee must have the 'ground_level_employee' role.
    3. Both must belong to the same department.

    Raises ValidationError with a descriptive message on any violation.
    These are hard rules — the frontend must never be trusted for this check.
    """
    if supervisor_profile.role_name != Role.SUPERVISOR:
        raise ValidationError(
            f'User {supervisor_profile.id} does not have the supervisor role '
            f'(role: {supervisor_profile.role_name}).'
        )

    if employee_profile.role_name != Role.GROUND_LEVEL_EMPLOYEE:
        raise ValidationError(
            f'User {employee_profile.id} does not have the ground_level_employee role '
            f'(role: {employee_profile.role_name}).'
        )

    if not profiles_share_department(employee_profile, supervisor_profile):
        raise ValidationError(
            'A ground-level employee and their supervisor must belong to the same department. '
            f'Employee department: {employee_profile.department_id}, '
            f'Supervisor department: {supervisor_profile.department_id}.'
        )


def validate_staff_has_department(profile: Profile) -> None:
    """
    Validates that a staff profile has a department.
    Raises ValidationError if a non-citizen, non-system-admin has no department.
    """
    no_dept_roles = {Role.CITIZEN, Role.SYSTEM_ADMIN}
    if profile.role_name not in no_dept_roles and profile.department_id is None:
        raise ValidationError(
            f'Staff members with the role "{profile.role_name}" must be assigned to a department.'
        )
