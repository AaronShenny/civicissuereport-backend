import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APIClient
from apps.users.models import Profile, Role, Department

def make_mock_role(name):
    role = MagicMock(spec=Role)
    role.role_name = name
    return role

def make_mock_profile(role_name, dept_id=None, sys_admin=False, dept_admin=False):
    p = MagicMock(spec=Profile)
    p.id = "12345678-1234-1234-1234-123456789012"
    p.role_name = role_name
    p.role = make_mock_role(role_name)
    p.department_id = dept_id
    p.is_system_admin = sys_admin
    p.is_department_admin = dept_admin
    p.is_authenticated = True
    p.account_status = 'active'
    p.profile = p
    return p

class TestEmployeeManagement:
    @patch('apps.users.views.transfer_department')
    def test_system_admin_can_transfer_department(self, mock_transfer):
        mock_transfer.return_value = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE)
        client = APIClient()
        sys_admin = make_mock_profile(Role.SYSTEM_ADMIN, sys_admin=True)
        
        with patch('core.authentication.supabase.SupabaseAuthentication.authenticate') as mock_auth:
            mock_auth.return_value = (sys_admin, None)
            res = client.post(reverse('employee-transfer-department', kwargs={'pk': '12345678-1234-1234-1234-123456789012'}), {'department_id': '22222222-2222-2222-2222-222222222222'}, format='json')
            assert res.status_code == 200

    @patch('apps.users.views.transfer_department')
    def test_department_admin_cannot_transfer_department(self, mock_transfer):
        client = APIClient()
        dept_admin = make_mock_profile(Role.DEPARTMENT_ADMIN, dept_admin=True)
        
        with patch('core.authentication.supabase.SupabaseAuthentication.authenticate') as mock_auth:
            mock_auth.return_value = (dept_admin, None)
            res = client.post(reverse('employee-transfer-department', kwargs={'pk': '12345678-1234-1234-1234-123456789012'}), {'department_id': '22222222-2222-2222-2222-222222222222'}, format='json')
            assert res.status_code == 403

    @patch('apps.users.views.transfer_location')
    def test_department_admin_can_transfer_location(self, mock_transfer):
        mock_transfer.return_value = make_mock_profile(Role.GROUND_LEVEL_EMPLOYEE)
        client = APIClient()
        dept_admin = make_mock_profile(Role.DEPARTMENT_ADMIN, dept_admin=True)
        
        with patch('core.authentication.supabase.SupabaseAuthentication.authenticate') as mock_auth:
            mock_auth.return_value = (dept_admin, None)
            res = client.post(reverse('employee-transfer-location', kwargs={'pk': '12345678-1234-1234-1234-123456789012'}), {'jurisdiction_id': '33333333-3333-3333-3333-333333333333'}, format='json')
            assert res.status_code == 200
