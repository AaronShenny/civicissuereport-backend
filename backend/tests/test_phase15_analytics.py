import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import Role

@pytest.fixture
def api_client():
    return APIClient()

def mock_profile(role_name, department_id=None):
    profile = MagicMock()
    profile.id = '00000000-0000-0000-0000-000000000000'
    profile.account_status = 'active'
    type(profile).role_name = getattr(type(profile), 'role_name', property(lambda self: role_name))
    profile.department_id = department_id
    
    # Permission helper mocks
    profile.is_system_admin = (role_name == Role.SYSTEM_ADMIN)
    profile.is_department_admin = (role_name == Role.DEPARTMENT_ADMIN)
    profile.is_supervisor = (role_name == Role.SUPERVISOR)
    profile.is_ground_level_employee = (role_name == Role.GROUND_LEVEL_EMPLOYEE)
    profile.is_citizen = (role_name == Role.CITIZEN)
    
    user = MagicMock()
    user.is_authenticated = True
    user.profile = profile
    return user

@pytest.fixture
def system_admin_user():
    return mock_profile(Role.SYSTEM_ADMIN)

@pytest.fixture
def department_admin_user():
    return mock_profile(Role.DEPARTMENT_ADMIN, department_id='dept-123')

@pytest.fixture
def supervisor_user():
    return mock_profile(Role.SUPERVISOR, department_id='dept-123')

@pytest.fixture
def employee_user():
    return mock_profile(Role.GROUND_LEVEL_EMPLOYEE, department_id='dept-123')

@pytest.fixture
def citizen_user():
    return mock_profile(Role.CITIZEN)

@pytest.fixture
def dashboard_url():
    return reverse('admin-analytics-dashboard')

@pytest.mark.django_db
class TestDashboardAnalyticsRBAC:
    def test_citizen_forbidden(self, api_client, citizen_user, dashboard_url):
        api_client.force_authenticate(user=citizen_user)
        response = api_client.get(dashboard_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_forbidden(self, api_client, employee_user, dashboard_url):
        api_client.force_authenticate(user=employee_user)
        response = api_client.get(dashboard_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('apps.complaints.analytics.get_dashboard_analytics')
    def test_supervisor_allowed(self, mock_get_analytics, api_client, supervisor_user, dashboard_url):
        mock_get_analytics.return_value = {}
        api_client.force_authenticate(user=supervisor_user)
        response = api_client.get(dashboard_url)
        assert response.status_code == status.HTTP_200_OK

    @patch('apps.complaints.analytics.get_dashboard_analytics')
    def test_dept_admin_allowed(self, mock_get_analytics, api_client, department_admin_user, dashboard_url):
        mock_get_analytics.return_value = {}
        api_client.force_authenticate(user=department_admin_user)
        response = api_client.get(dashboard_url)
        assert response.status_code == status.HTTP_200_OK

    @patch('apps.complaints.analytics.get_dashboard_analytics')
    def test_sys_admin_allowed(self, mock_get_analytics, api_client, system_admin_user, dashboard_url):
        mock_get_analytics.return_value = {}
        api_client.force_authenticate(user=system_admin_user)
        response = api_client.get(dashboard_url)
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestDashboardAnalyticsService:
    @patch('apps.complaints.analytics.get_analytics_data')
    @patch('apps.complaints.analytics.Profile.objects.filter')
    @patch('apps.complaints.analytics.Complaint.objects.all')
    def test_dept_admin_isolation(self, mock_complaint_all, mock_profile_filter, mock_get_analytics, department_admin_user):
        """
        Verify that department admins are securely filtered to their own department,
        even if they try to pass a malicious department query parameter.
        """
        mock_get_analytics.return_value = {'summary': {}}
        mock_qs = MagicMock()
        mock_complaint_all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        
        mock_profile_qs = MagicMock()
        mock_profile_filter.return_value = mock_profile_qs
        mock_profile_qs.annotate.return_value = mock_profile_qs
        mock_profile_qs.values.return_value = mock_profile_qs
        mock_profile_qs.order_by.return_value = []
        
        from apps.complaints.analytics import get_dashboard_analytics
        data = get_dashboard_analytics(department_admin_user.profile, {'department': 'fake-id'})
        
        # Verify it used the user's department ID, ignoring 'fake-id'
        mock_qs.filter.assert_any_call(assigned_department_id=department_admin_user.profile.department_id)
        
        # Verify employee workload was filtered correctly
        mock_profile_filter.assert_any_call(
            department_id=department_admin_user.profile.department_id,
            role__role_name=Role.GROUND_LEVEL_EMPLOYEE
        )
