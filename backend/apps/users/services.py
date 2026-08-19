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

import secrets
import string
import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError as DRFValidationError


def create_employee(
    admin_profile: Profile,
    full_name: str,
    email: str,
    phone: str,
    role_id: int,
    department_id: str,
    jurisdiction_id: str,
    password: str = None
) -> Profile:
    """
    Creates a new employee account in Supabase Auth and provisions their Profile.
    """
    if admin_profile.is_department_admin:
        target_role = Role.objects.filter(id=role_id).first()
        if not target_role or target_role.role_name == Role.SYSTEM_ADMIN:
            raise DRFValidationError("Department Admins cannot assign this role.")
        # Dept admin MUST create within their own department
        department_id = admin_profile.department_id
    elif not admin_profile.is_system_admin:
        raise DRFValidationError("Unauthorized to create employees.")

    # 1. Create in Supabase Auth using Admin API
    if not password:
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(secrets.choice(alphabet) for _ in range(16))

    headers = {
        'apikey': settings.SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'email': email,
        'password': password,
        'user_metadata': {'full_name': full_name},
        'email_confirm': True
    }
    if phone:
        data['phone'] = phone

    url = f'{settings.SUPABASE_URL}/auth/v1/admin/users'
    r = requests.post(url, json=data, headers=headers)

    if r.status_code not in (200, 201):
        raise DRFValidationError(f"Failed to create user in Supabase: {r.text}")

    uid = r.json()['id']

    # 2. Update Profile created by trigger
    # Wait/check to ensure trigger completed
    profile = Profile.objects.filter(id=uid).first()
    if not profile:
        raise DRFValidationError("User created but Profile trigger failed.")

    profile.role_id = role_id
    profile.department_id = department_id
    profile.jurisdiction_id = jurisdiction_id or None
    profile.account_status = Profile.ACCOUNT_STATUS_ACTIVE
    profile.save()

    from apps.users.audit_logger import log_audit_event
    log_audit_event(
        actor=admin_profile,
        action="create_employee",
        entity_type="Profile",
        entity_id=str(profile.id),
        old_value=None,
        new_value={
            "role_id": role_id,
            "department_id": str(department_id) if department_id else None,
            "jurisdiction_id": str(jurisdiction_id) if jurisdiction_id else None,
            "full_name": full_name,
            "email": email
        }
    )

    return profile


def transfer_location(admin_profile: Profile, employee_id: str, new_jurisdiction_id: str) -> Profile:
    """
    Transfers an employee to a new jurisdiction/district.
    """
    try:
        employee = Profile.objects.get(id=employee_id)
    except Profile.DoesNotExist:
        raise DRFValidationError("Employee not found.")

    if admin_profile.is_department_admin:
        if employee.department_id != admin_profile.department_id:
            raise DRFValidationError("Cannot transfer employee of another department.")
    elif not admin_profile.is_system_admin:
        raise DRFValidationError("Unauthorized")

    old_jurisdiction = employee.jurisdiction_id

    employee.jurisdiction_id = new_jurisdiction_id or None
    employee.save()
    
    from apps.users.audit_logger import log_audit_event
    log_audit_event(
        actor=admin_profile,
        action="transfer_location",
        entity_type="Profile",
        entity_id=str(employee.id),
        old_value={"jurisdiction_id": str(old_jurisdiction) if old_jurisdiction else None},
        new_value={"jurisdiction_id": str(employee.jurisdiction_id) if employee.jurisdiction_id else None}
    )
    
    return employee


def transfer_department(admin_profile: Profile, employee_id: str, new_department_id: str) -> Profile:
    """
    Transfers an employee to a new department. System Admin ONLY.
    """
    if not admin_profile.is_system_admin:
        raise DRFValidationError("Only System Admins can transfer departments.")

    try:
        employee = Profile.objects.get(id=employee_id)
    except Profile.DoesNotExist:
        raise DRFValidationError("Employee not found.")

    old_department = employee.department_id

    employee.department_id = new_department_id or None
    employee.save()
    
    from apps.users.audit_logger import log_audit_event
    log_audit_event(
        actor=admin_profile,
        action="transfer_department",
        entity_type="Profile",
        entity_id=str(employee.id),
        old_value={"department_id": str(old_department) if old_department else None},
        new_value={"department_id": str(employee.department_id) if employee.department_id else None}
    )

    return employee

