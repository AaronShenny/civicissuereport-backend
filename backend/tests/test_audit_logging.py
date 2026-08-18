import pytest
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch, MagicMock

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

def mock_profile(role_name):
    profile = MagicMock()
    profile.id = "test-uuid"
    profile.role_name = role_name
    profile.is_system_admin = (role_name == "system_admin")
    profile.is_department_admin = (role_name == "department_admin")
    profile.is_supervisor = (role_name == "supervisor")
    profile.is_staff_member = True
    profile.is_authenticated = True
    profile.account_status = 'active'
    profile.profile = profile
    return profile

def test_audit_log_api_access_system_admin(api_client):
    user = mock_profile("system_admin")
    api_client.force_authenticate(user=user)
    
    with patch('apps.users.views.AuditLog.objects') as mock_objects:
        mock_qs = MagicMock()
        mock_objects.select_related.return_value.all.return_value = mock_qs
        url = reverse('admin-audit-logs')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

def test_audit_log_api_access_department_admin(api_client):
    user = mock_profile("department_admin")
    api_client.force_authenticate(user=user)
    url = reverse('admin-audit-logs')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_audit_logger_service():
    from apps.users.audit_logger import log_audit_event
    
    actor = MagicMock()
    actor.id = "actor-uuid"
    
    with patch('apps.users.audit_logger.AuditLog.objects.create') as mock_create:
        log_audit_event(
            actor=actor,
            action="test_action",
            entity_type="TestEntity",
            entity_id="123",
            old_value={"some_field": "old", "password": "hidden"},
            new_value={"some_field": "new", "password": "hidden_new"}
        )
        
        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        assert kwargs["actor"] == actor
        assert kwargs["action"] == "test_action"
        assert kwargs["old_value"] == {"some_field": "old"}
        assert kwargs["new_value"] == {"some_field": "new"}
        assert "password" not in kwargs["old_value"]
        assert "password" not in kwargs["new_value"]
