import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, MagicMock

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

def mock_profile(role_name, department_id=None):
    profile = MagicMock()
    profile.id = "test-uuid"
    profile.role_name = role_name
    profile.is_system_admin = (role_name == "system_admin")
    profile.is_department_admin = (role_name == "department_admin")
    profile.is_supervisor = (role_name == "supervisor")
    profile.is_citizen = (role_name == "citizen")
    profile.is_ground_level_employee = (role_name == "ground_level_employee")
    profile.department_id = department_id
    profile.is_authenticated = True
    profile.account_status = 'active'
    profile.profile = profile # So request.user.profile works
    return profile

@pytest.fixture
def system_admin_user():
    return mock_profile("system_admin")

@pytest.fixture
def department_admin_user():
    return mock_profile("department_admin", department_id="00000000-0000-0000-0000-000000000001")

@pytest.fixture
def citizen_user():
    return mock_profile("citizen")

@pytest.fixture
def employee_user():
    return mock_profile("ground_level_employee")

@pytest.fixture
def supervisor_user():
    return mock_profile("supervisor", department_id="00000000-0000-0000-0000-000000000001")

@pytest.fixture
def base_reports_url():
    return reverse('admin-reports-analytics')

@pytest.fixture
def base_export_url():
    return reverse('admin-reports-export')

class TestReportsRBAC:
    def test_citizen_forbidden(self, api_client, citizen_user, base_reports_url):
        api_client.force_authenticate(user=citizen_user)
        response = api_client.get(base_reports_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_forbidden(self, api_client, employee_user, base_reports_url):
        api_client.force_authenticate(user=employee_user)
        response = api_client.get(base_reports_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_supervisor_forbidden(self, api_client, supervisor_user, base_reports_url):
        api_client.force_authenticate(user=supervisor_user)
        response = api_client.get(base_reports_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('apps.complaints.views.get_analytics_data')
    def test_dept_admin_allowed(self, mock_get_analytics, api_client, department_admin_user, base_reports_url):
        mock_get_analytics.return_value = {}
        api_client.force_authenticate(user=department_admin_user)
        with patch('apps.complaints.reporting.Complaint.objects.all'):
            response = api_client.get(base_reports_url)
            assert response.status_code == status.HTTP_200_OK

    @patch('apps.complaints.views.get_analytics_data')
    def test_sys_admin_allowed(self, mock_get_analytics, api_client, system_admin_user, base_reports_url):
        mock_get_analytics.return_value = {}
        api_client.force_authenticate(user=system_admin_user)
        with patch('apps.complaints.reporting.Complaint.objects.all'):
            response = api_client.get(base_reports_url)
            assert response.status_code == status.HTTP_200_OK


class TestReportingService:
    @patch('apps.complaints.models.Complaint.objects.all')
    def test_dept_admin_isolation(self, mock_all, department_admin_user):
        mock_qs = MagicMock()
        mock_all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        
        from apps.complaints.reporting import get_filtered_complaints_queryset
        qs = get_filtered_complaints_queryset(department_admin_user.profile, {'department': 'fake-id'})
        
        # Ensure the filter was called with assigned_department_id=dept_admin.department_id
        mock_qs.filter.assert_called_with(assigned_department_id=department_admin_user.profile.department_id)

    @patch('apps.complaints.views.get_analytics_data')
    def test_excel_export_mime(self, mock_get_analytics, api_client, system_admin_user, base_export_url):
        mock_get_analytics.return_value = {'summary': {'total': 0, 'pending': 0, 'resolved': 0, 'invalid': 0, 'avg_resolution_time': None}}
        api_client.force_authenticate(user=system_admin_user)
        
        with patch('apps.complaints.views.generate_excel_report', return_value=b'exceldata'), patch('apps.complaints.reporting.Complaint.objects.all'):
            response = api_client.get(base_export_url, {'format': 'xlsx'})
            assert response.status_code == status.HTTP_200_OK
            assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    @patch('apps.complaints.views.get_analytics_data')
    def test_pdf_export_mime(self, mock_get_analytics, api_client, system_admin_user, base_export_url):
        mock_get_analytics.return_value = {'summary': {'total': 0, 'pending': 0, 'resolved': 0, 'invalid': 0, 'avg_resolution_time': None}}
        api_client.force_authenticate(user=system_admin_user)
        
        with patch('apps.complaints.views.generate_pdf_report', return_value=b'pdfdata'), patch('apps.complaints.reporting.Complaint.objects.all'):
            response = api_client.get(base_export_url, {'format': 'pdf'})
            assert response.status_code == status.HTTP_200_OK
            assert response['Content-Type'] == 'application/pdf'
