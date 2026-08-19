import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import Role

@pytest.fixture
def api_client():
    return APIClient()

def mock_profile(role_name, user_id='00000000-0000-0000-0000-000000000000', department_id=None):
    profile = MagicMock()
    profile.id = user_id
    profile.account_status = 'active'
    type(profile).role_name = getattr(type(profile), 'role_name', property(lambda self: role_name))
    profile.department_id = department_id
    
    profile.is_system_admin = (role_name == Role.SYSTEM_ADMIN)
    profile.is_department_admin = (role_name == Role.DEPARTMENT_ADMIN)
    profile.is_supervisor = (role_name == Role.SUPERVISOR)
    profile.is_ground_level_employee = (role_name == Role.GROUND_LEVEL_EMPLOYEE)
    profile.is_citizen = (role_name == Role.CITIZEN)
    
    user = MagicMock()
    user.id = user_id
    user.is_authenticated = True
    user.profile = profile
    return user

@pytest.fixture
def system_admin_user():
    return mock_profile(Role.SYSTEM_ADMIN, user_id='sys-admin-uuid')

@pytest.fixture
def department_admin_user():
    return mock_profile(Role.DEPARTMENT_ADMIN, user_id='dept-admin-uuid', department_id='dept-123')

@pytest.fixture
def other_department_admin_user():
    return mock_profile(Role.DEPARTMENT_ADMIN, user_id='other-dept-admin-uuid', department_id='dept-456')

@pytest.fixture
def supervisor_user():
    return mock_profile(Role.SUPERVISOR, user_id='supervisor-uuid', department_id='dept-123')

@pytest.fixture
def other_supervisor_user():
    return mock_profile(Role.SUPERVISOR, user_id='other-supervisor-uuid', department_id='dept-456')

@pytest.fixture
def employee_user():
    return mock_profile(Role.GROUND_LEVEL_EMPLOYEE, user_id='employee-uuid', department_id='dept-123')

@pytest.fixture
def other_employee_user():
    return mock_profile(Role.GROUND_LEVEL_EMPLOYEE, user_id='other-employee-uuid', department_id='dept-456')

@pytest.fixture
def citizen_user():
    return mock_profile(Role.CITIZEN, user_id='citizen-uuid')

@pytest.fixture
def other_citizen_user():
    return mock_profile(Role.CITIZEN, user_id='other-citizen-uuid')

@pytest.fixture
def complaint_id():
    return '11111111-1111-1111-1111-111111111111'

@pytest.fixture
def mock_complaint(complaint_id):
    c = MagicMock()
    c.id = complaint_id
    c.citizen_id = 'citizen-uuid'
    c.assigned_department_id = 'dept-123'
    c.assigned_employee_id = 'employee-uuid'
    c.complaint_number = 'CMP-2026-000001'
    return c

@pytest.mark.django_db
class TestStaffDetailView:
    @patch('apps.complaints.views.get_object_or_404')
    @patch('apps.complaints.views.StaffComplaintDetailSerializer')
    def test_assigned_employee_allowed(self, mock_serializer, mock_get_obj, api_client, employee_user, mock_complaint, complaint_id):
        mock_get_obj.return_value = mock_complaint
        mock_serializer.return_value.data = {'id': complaint_id}
        
        api_client.force_authenticate(user=employee_user)
        url = reverse('complaint-detail-staff', kwargs={'pk': complaint_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK

    @patch('apps.complaints.views.get_object_or_404')
    def test_employee_from_another_department_forbidden(self, mock_get_obj, api_client, other_employee_user, mock_complaint, complaint_id):
        mock_get_obj.return_value = mock_complaint
        
        api_client.force_authenticate(user=other_employee_user)
        url = reverse('complaint-detail-staff', kwargs={'pk': complaint_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('apps.complaints.views.get_object_or_404')
    @patch('apps.complaints.views.StaffComplaintDetailSerializer')
    def test_supervisor_correct_scope_allowed(self, mock_serializer, mock_get_obj, api_client, supervisor_user, mock_complaint, complaint_id):
        mock_get_obj.return_value = mock_complaint
        mock_serializer.return_value.data = {'id': complaint_id}
        
        api_client.force_authenticate(user=supervisor_user)
        url = reverse('complaint-detail-staff', kwargs={'pk': complaint_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK

    @patch('apps.complaints.views.get_object_or_404')
    def test_supervisor_from_wrong_department_forbidden(self, mock_get_obj, api_client, other_supervisor_user, mock_complaint, complaint_id):
        mock_get_obj.return_value = mock_complaint
        
        api_client.force_authenticate(user=other_supervisor_user)
        url = reverse('complaint-detail-staff', kwargs={'pk': complaint_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('apps.complaints.views.get_object_or_404')
    @patch('apps.complaints.views.StaffComplaintDetailSerializer')
    def test_dept_admin_correct_department_allowed(self, mock_serializer, mock_get_obj, api_client, department_admin_user, mock_complaint, complaint_id):
        mock_get_obj.return_value = mock_complaint
        mock_serializer.return_value.data = {'id': complaint_id}
        
        api_client.force_authenticate(user=department_admin_user)
        url = reverse('complaint-detail-staff', kwargs={'pk': complaint_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK

    @patch('apps.complaints.views.get_object_or_404')
    def test_dept_admin_from_wrong_department_forbidden(self, mock_get_obj, api_client, other_department_admin_user, mock_complaint, complaint_id):
        mock_get_obj.return_value = mock_complaint
        
        api_client.force_authenticate(user=other_department_admin_user)
        url = reverse('complaint-detail-staff', kwargs={'pk': complaint_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('apps.complaints.views.get_object_or_404')
    @patch('apps.complaints.views.StaffComplaintDetailSerializer')
    def test_system_admin_allowed(self, mock_serializer, mock_get_obj, api_client, system_admin_user, mock_complaint, complaint_id):
        mock_get_obj.return_value = mock_complaint
        mock_serializer.return_value.data = {'id': complaint_id}
        
        api_client.force_authenticate(user=system_admin_user)
        url = reverse('complaint-detail-staff', kwargs={'pk': complaint_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK

    @patch('apps.complaints.views.get_object_or_404')
    def test_citizen_forbidden(self, mock_get_obj, api_client, citizen_user, mock_complaint, complaint_id):
        mock_get_obj.return_value = mock_complaint
        
        api_client.force_authenticate(user=citizen_user)
        url = reverse('complaint-detail-staff', kwargs={'pk': complaint_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDepartmentComplaintsView:
    @patch('apps.complaints.views.Complaint.objects.filter')
    def test_dept_admin_own_department_only(self, mock_filter, api_client, department_admin_user):
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        mock_qs.select_related.return_value.order_by.return_value = []
        
        api_client.force_authenticate(user=department_admin_user)
        url = reverse('admin-department-complaints')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        mock_filter.assert_called_with(assigned_department_id='dept-123')

    @patch('apps.complaints.views.Complaint.objects.filter')
    def test_malicious_department_query_ignored(self, mock_filter, api_client, department_admin_user):
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        mock_qs.select_related.return_value.order_by.return_value = []
        
        api_client.force_authenticate(user=department_admin_user)
        url = reverse('admin-department-complaints')
        # Attending to bypass via query parameter
        response = api_client.get(url, {'department': 'dept-456'})
        
        assert response.status_code == status.HTTP_200_OK
        # Query parameter is ignored for department admins
        mock_filter.assert_called_with(assigned_department_id='dept-123')

    def test_citizen_forbidden(self, api_client, citizen_user):
        api_client.force_authenticate(user=citizen_user)
        url = reverse('admin-department-complaints')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_forbidden(self, api_client, employee_user):
        api_client.force_authenticate(user=employee_user)
        url = reverse('admin-department-complaints')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_supervisor_forbidden(self, api_client, supervisor_user):
        api_client.force_authenticate(user=supervisor_user)
        url = reverse('admin-department-complaints')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestPIIProtection:
    def test_staff_serializer_fields(self):
        from apps.complaints.serializers import StaffComplaintDetailSerializer
        
        # Instantiate serializer class and verify Meta fields list
        fields = StaffComplaintDetailSerializer.Meta.fields
        # Should not expose citizen profile
        assert 'citizen' not in fields
        assert 'citizen_id' not in fields
        # Check standard fields are present
        assert 'complaint_number' in fields
        assert 'description' in fields
        assert 'location_lat' in fields


@pytest.mark.django_db
class TestExistingCitizenBehavior:
    @patch('apps.complaints.serializers.ComplaintDetailSerializer.to_representation')
    @patch('apps.complaints.views.Complaint.objects.filter')
    def test_citizen_detail_remains_protected(self, mock_filter, mock_to_rep, api_client, citizen_user, complaint_id):
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        mock_qs.select_related.return_value.prefetch_related.return_value.get.return_value = MagicMock(citizen_id='citizen-uuid')
        mock_to_rep.return_value = {'id': complaint_id}
        
        api_client.force_authenticate(user=citizen_user)
        url = reverse('complaint-detail', kwargs={'pk': complaint_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Citizen filter must be in place
        mock_filter.assert_called_with(citizen_id=citizen_user.id)
