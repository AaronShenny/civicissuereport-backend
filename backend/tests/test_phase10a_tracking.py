import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import uuid

@pytest.fixture
def api_client():
    return APIClient()

def make_mock_resolution():
    res = MagicMock()
    res.resolution_details = "Fixed the pothole"
    res.created_at = '2026-08-20T10:00:00Z'
    return res

def make_mock_history():
    hist = MagicMock()
    hist.new_status = 'submitted'
    hist.changed_at = '2026-08-19T10:00:00Z'
    return hist

def make_mock_complaint():
    c = MagicMock()
    c.id = uuid.uuid4()
    c.complaint_number = 'CMP-2026-999999'
    c.category.name = "Trackable Issue"
    c.status = 'resolved'
    c.submitted_at = '2026-08-19T09:00:00Z'
    c.updated_at = '2026-08-20T10:00:00Z'
    
    # Mock related fields for serializers
    hist = make_mock_history()
    c.status_history = [hist]
    
    # Resolving resolution logic in serializer
    res = make_mock_resolution()
    # For many=True/queryset, we need to mock .filter(...).order_by(...).first()
    res_qs = MagicMock()
    res_qs.order_by.return_value.first.return_value = res
    c.resolutions.filter.return_value = res_qs
    
    return c

class TestPublicTrackingAPI:
    @patch('apps.complaints.views.get_object_or_404')
    def test_unauthenticated_request_succeeds(self, mock_get_object, api_client):
        """1. Unauthenticated request succeeds for a valid public complaint."""
        mock_get_object.return_value = make_mock_complaint()
        url = reverse('complaint-public-track', kwargs={'complaint_number': 'CMP-2026-999999'})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    @patch('apps.complaints.views.get_object_or_404')
    def test_valid_complaint_returns_expected_fields(self, mock_get_object, api_client):
        """2. Valid complaint number returns the expected public fields."""
        c = make_mock_complaint()
        mock_get_object.return_value = c
        url = reverse('complaint-public-track', kwargs={'complaint_number': c.complaint_number})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        
        data = res.json()
        assert data['complaint_number'] == c.complaint_number
        assert data['category'] == "Trackable Issue"
        assert data['status'] == "resolved"
        assert 'submitted_at' in data
        assert 'updated_at' in data

    @patch('apps.complaints.views.get_object_or_404')
    def test_invalid_complaint_number_returns_404(self, mock_get_object, api_client):
        """3. Invalid complaint number returns 404."""
        from django.http import Http404
        mock_get_object.side_effect = Http404()
        url = reverse('complaint-public-track', kwargs={'complaint_number': 'INVALID-123'})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_404_NOT_FOUND

    @patch('apps.complaints.views.get_object_or_404')
    def test_response_does_not_contain_private_data(self, mock_get_object, api_client):
        """4. Response does NOT contain private/PII/internal data."""
        c = make_mock_complaint()
        mock_get_object.return_value = c
        url = reverse('complaint-public-track', kwargs={'complaint_number': c.complaint_number})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        
        data = res.json()
        # Verify absence of private fields (since we explicitly set only safe ones)
        assert 'citizen' not in data
        assert 'citizen_name' not in data
        assert 'description' not in data
        assert 'location' not in data
        assert 'latitude' not in data
        assert 'longitude' not in data
        
    @patch('apps.complaints.views.get_object_or_404')
    def test_public_status_history_is_safe(self, mock_get_object, api_client):
        """5. Public status history contains only safe status/timestamp information."""
        c = make_mock_complaint()
        c.status_history = [make_mock_history()]

        mock_get_object.return_value = c
        url = reverse('complaint-public-track', kwargs={'complaint_number': c.complaint_number})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        
        data = res.json()
        print("DEBUG DATA:", data)
        assert 'status_history' in data
        assert len(data['status_history']) > 0
        
        history_item = data['status_history'][0]
        assert 'status' in history_item
        assert 'changed_at' in history_item
        assert 'changed_by' not in history_item
        assert 'change_reason' not in history_item

    @patch('apps.complaints.views.get_object_or_404')
    def test_resolved_complaint_exposes_only_safe_resolution(self, mock_get_object, api_client):
        """6. Resolved complaint exposes only approved public resolution information."""
        c = make_mock_complaint()
        mock_get_object.return_value = c
        url = reverse('complaint-public-track', kwargs={'complaint_number': c.complaint_number})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        
        data = res.json()
        assert 'resolution' in data
        assert data['resolution'] is not None
        assert data['resolution']['details'] == "Fixed the pothole"
        assert 'resolved_at' in data['resolution']
        assert 'remarks' not in data['resolution']
        assert 'updated_by' not in data['resolution']

    def test_existing_private_endpoints_remain_protected(self, api_client):
        """7. Existing authenticated complaint-detail endpoint remains protected."""
        # UUID needed for the private URL routing
        private_url = reverse('complaint-detail', kwargs={'pk': str(uuid.uuid4())})
        res = api_client.get(private_url)
        # Should be 401 Unauthorized because we are unauthenticated
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
