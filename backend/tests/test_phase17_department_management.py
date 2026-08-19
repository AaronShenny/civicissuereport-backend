import pytest
from rest_framework import status
from django.urls import reverse
from rest_framework.test import APIClient
from apps.users.models import Role, Profile, Department
from apps.departments.models import DepartmentCategoryRule
from apps.complaints.models import Complaint

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def sys_admin_user():
    role, _ = Role.objects.get_or_create(role_name=Role.SYSTEM_ADMIN)
    return Profile.objects.create(full_name='Sys Admin', role=role, account_status='active', auth_provider='supabase')

@pytest.fixture
def department():
    return Department.objects.create(name='Test Department', description='Testing', is_active=True)

@pytest.fixture
def department_admin_user(department):
    role, _ = Role.objects.get_or_create(role_name=Role.DEPARTMENT_ADMIN)
    return Profile.objects.create(full_name='Dept Admin', role=role, department=department, account_status='active', auth_provider='supabase')

@pytest.fixture
def ground_level_employee_user(department):
    role, _ = Role.objects.get_or_create(role_name=Role.GROUND_LEVEL_EMPLOYEE)
    return Profile.objects.create(full_name='Employee', role=role, department=department, account_status='active', auth_provider='supabase')

@pytest.fixture
def citizen_user():
    role, _ = Role.objects.get_or_create(role_name=Role.CITIZEN)
    return Profile.objects.create(full_name='Citizen', role=role, account_status='active', auth_provider='supabase')


@pytest.fixture
def department_url():
    return reverse('department-list')

@pytest.fixture
def department_create_url():
    return reverse('department-create')

@pytest.fixture
def department_detail_url(department):
    return reverse('department-detail', args=[department.id])

@pytest.fixture
def department_performance_url(department):
    return reverse('department-performance', args=[department.id])

class TestDepartmentManagement:
    def test_sys_admin_create_department(self, api_client, sys_admin_user):
        api_client.force_authenticate(user=sys_admin_user)
        url = reverse('department-create')
        data = {'name': 'New Testing Dept', 'description': 'Test Dept'}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Department.objects.filter(name='New Testing Dept').exists()

    def test_sys_admin_update_department(self, api_client, sys_admin_user, department):
        api_client.force_authenticate(user=sys_admin_user)
        url = reverse('department-detail', args=[department.id])
        response = api_client.patch(url, {'description': 'Updated Desc'})
        assert response.status_code == status.HTTP_200_OK
        department.refresh_from_db()
        assert department.description == 'Updated Desc'

    def test_dept_admin_cannot_update_department(self, api_client, department_admin_user, department):
        api_client.force_authenticate(user=department_admin_user)
        url = reverse('department-detail', args=[department.id])
        response = api_client.patch(url, {'description': 'Hacked'})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_deactivation_safety_check(self, api_client, sys_admin_user, department, ground_level_employee_user):
        # The department has an active employee assigned.
        api_client.force_authenticate(user=sys_admin_user)
        url = reverse('department-detail', args=[department.id])
        response = api_client.patch(url, {'is_active': False})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Cannot deactivate department' in str(response.data)

    def test_performance_endpoint_idor(self, api_client, department_admin_user, sys_admin_user):
        other_dept = Department.objects.create(name='Other Dept', description='Other')
        api_client.force_authenticate(user=department_admin_user)
        
        # Dept admin tries to view other department's performance
        url = reverse('department-performance', args=[other_dept.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Sys admin can view it
        api_client.force_authenticate(user=sys_admin_user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_citizen_forbidden(self, api_client, citizen_user, department):
        api_client.force_authenticate(user=citizen_user)
        response = api_client.get(reverse('department-list'))
        assert response.status_code == status.HTTP_403_FORBIDDEN
