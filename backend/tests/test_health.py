import pytest
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_health_check_endpoint():
    client = APIClient()
    url = reverse('health_check')
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    # db might not be configured locally in CI without postgres, but the structure is tested.
