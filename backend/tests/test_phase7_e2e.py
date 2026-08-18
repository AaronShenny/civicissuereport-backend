import pytest
import uuid
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from apps.users.models import Profile, Role, Department
from apps.departments.models import DepartmentCategoryRule
from apps.complaints.models import Complaint, ComplaintCategory, ComplaintStatus, ComplaintStatusHistory

@pytest.mark.django_db(transaction=True)
class TestE2ELifecycleRealAPI:
    def test_full_lifecycle_via_api(self):
        client = APIClient()
        
        # 1. Setup users
        citizen_role, _ = Role.objects.get_or_create(role_name=Role.CITIZEN)
        supervisor_role, _ = Role.objects.get_or_create(role_name=Role.SUPERVISOR)
        employee_role, _ = Role.objects.get_or_create(role_name=Role.GROUND_LEVEL_EMPLOYEE)

        dept, _ = Department.objects.get_or_create(id=uuid.uuid4(), name="Test Dept", is_active=True)
        cat, _ = ComplaintCategory.objects.get_or_create(name="Test Category", is_active=True)
        DepartmentCategoryRule.objects.get_or_create(category=cat, department=dept, is_active=True, priority_rank=1)

        citizen = Profile.objects.create(id=uuid.uuid4(), email="citizen@example.com", role=citizen_role, full_name="Citizen")
        supervisor = Profile.objects.create(id=uuid.uuid4(), email="sup@example.com", role=supervisor_role, department=dept, full_name="Supervisor")
        employee = Profile.objects.create(id=uuid.uuid4(), email="emp@example.com", role=employee_role, department=dept, full_name="Employee")

        # 2. Submit Complaint
        client.force_authenticate(user=citizen)
        submit_url = reverse('complaint-list')  # assuming this is the URL for ListCreate
        payload = {
            'category_id': cat.id,
            'description': 'Test complaint E2E',
            'latitude': 12.34,
            'longitude': 56.78,
            'google_maps_url': 'https://maps.google.com/?q=12.34,56.78',
        }
        res = client.post(submit_url, payload)
        assert res.status_code == status.HTTP_201_CREATED, res.data
        complaint_id = res.data['id']
        complaint = Complaint.objects.get(id=complaint_id)
        
        print("Success so far")

