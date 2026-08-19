import pytest
import uuid
from unittest.mock import patch
from datetime import datetime, timezone
from django.urls import reverse
from rest_framework.test import APIClient
from apps.complaints.models import Complaint, ComplaintCategory, ComplaintStatus
from apps.users.models import Profile, Role, Department

# Use mock objects for users
def make_mock_category() -> ComplaintCategory:
    cat = ComplaintCategory(
        id=1,
        name='pothole',
        is_active=True,
        requires_attachment=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    cat.save()
    return cat

def make_mock_profile(role_name: str, sys_admin=False, dept_admin=False) -> Profile:
    r = Role(role_name=role_name)
    p = Profile(
        id=uuid.uuid4(),
        role=r,
        account_status='active',
    )
    p.is_system_admin = sys_admin
    p.is_department_admin = dept_admin
    p.is_authenticated = True
    p.profile = p
    return p

@pytest.mark.django_db
class TestDuplicateDetection:

    def setup_method(self):
        self.client = APIClient()
        self.citizen = make_mock_profile(Role.CITIZEN)
        self.category = make_mock_category()
        
    def test_same_category_same_district_under_10m(self):
        c1 = Complaint.objects.create(
            id=uuid.uuid4(),
            complaint_number='CMP-TEST-1',
            citizen_id=self.citizen.id,
            category=self.category,
            description='Main',
            location='', location_lat=9.9312328, location_lng=76.2673041,
            district='Ernakulam',
            status=ComplaintStatus.SUBMITTED,
            reporter_count=1,
            submitted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        c2 = Complaint.objects.create(
            id=uuid.uuid4(),
            complaint_number='CMP-TEST-2',
            citizen_id=self.citizen.id,
            category=self.category,
            description='Dup',
            location='', location_lat=9.9313128, location_lng=76.2673041,
            district='Ernakulam',
            status=ComplaintStatus.SUBMITTED,
            submitted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        from apps.complaints.duplicates import detect_and_link_duplicate
        is_dup = detect_and_link_duplicate(c2)
        assert is_dup is True
        
        c1.refresh_from_db()
        c2.refresh_from_db()
        assert c2.main_complaint_id == c1.id
        assert c1.reporter_count == 2

    def test_same_category_same_district_over_10m(self):
        c1 = Complaint.objects.create(
            id=uuid.uuid4(),
            complaint_number='CMP-TEST-3',
            citizen_id=self.citizen.id,
            category=self.category,
            description='Main',
            location='', location_lat=9.9312328, location_lng=76.2673041,
            district='Ernakulam',
            status=ComplaintStatus.SUBMITTED,
            reporter_count=1,
            submitted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        c2 = Complaint.objects.create(
            id=uuid.uuid4(),
            complaint_number='CMP-TEST-4',
            citizen_id=self.citizen.id,
            category=self.category,
            description='Dup',
            location='', location_lat=9.9315000, location_lng=76.2673041,
            district='Ernakulam',
            status=ComplaintStatus.SUBMITTED,
            submitted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        from apps.complaints.duplicates import detect_and_link_duplicate
        is_dup = detect_and_link_duplicate(c2)
        assert is_dup is False
        
        c2.refresh_from_db()
        assert c2.main_complaint_id is None
        
    @patch('core.authentication.supabase.SupabaseAuthentication.authenticate')
    def test_tracking_api_resolves_to_main_complaint(self, mock_auth):
        mock_auth.return_value = (self.citizen, None)
        
        # Setup c1 and duplicate c2 in database directly for tracking test
        c1 = Complaint.objects.create(
            id=uuid.uuid4(),
            complaint_number='CMP-TEST-1',
            citizen_id=self.citizen.id,
            category=self.category,
            description='Main',
            location='', location_lat=9.0, location_lng=76.0,
            status=ComplaintStatus.IN_PROGRESS,
            reporter_count=2,
            submitted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        c2 = Complaint.objects.create(
            id=uuid.uuid4(),
            complaint_number='CMP-TEST-2',
            citizen_id=self.citizen.id,
            category=self.category,
            description='Dup',
            location='', location_lat=9.0, location_lng=76.0,
            status=ComplaintStatus.SUBMITTED,
            main_complaint=c1,
            submitted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        res = self.client.get(f'/api/v1/complaints/track/{c2.id}/')
        assert res.status_code == 200
        assert res.data['complaint_number'] == 'CMP-TEST-2'
        assert res.data['is_duplicate'] is True
        assert res.data['main_complaint_number'] == 'CMP-TEST-1'
        assert res.data['status'] == ComplaintStatus.IN_PROGRESS  # from c1
