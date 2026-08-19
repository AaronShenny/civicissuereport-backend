import pytest
import uuid
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from apps.complaints.priority import get_base_priority, calculate_final_priority
from apps.complaints.models import PriorityCategory

@pytest.mark.django_db
def test_base_priorities():
    from datetime import datetime, timezone
    from apps.complaints.models import ComplaintCategory
    now = datetime.now(timezone.utc)
    # Seed data
    categories = [
        ('drainage', PriorityCategory.HIGH),
        ('garbage', PriorityCategory.HIGH),
        ('other', PriorityCategory.MEDIUM),
        ('pothole', PriorityCategory.HIGH),
        ('road_damage', PriorityCategory.HIGH),
        ('sanitation', PriorityCategory.HIGH),
        ('streetlight', PriorityCategory.MEDIUM),
        ('water_supply', PriorityCategory.HIGH),
        ('Road Damage ', PriorityCategory.HIGH),
    ]
    for name, bp in categories:
        ComplaintCategory.objects.create(name=name, base_priority=bp, created_at=now, updated_at=now)

    assert get_base_priority('drainage') == PriorityCategory.HIGH
    assert get_base_priority('garbage') == PriorityCategory.HIGH
    assert get_base_priority('other') == PriorityCategory.MEDIUM
    assert get_base_priority('pothole') == PriorityCategory.HIGH
    assert get_base_priority('road_damage') == PriorityCategory.HIGH
    assert get_base_priority('sanitation') == PriorityCategory.HIGH
    assert get_base_priority('streetlight') == PriorityCategory.MEDIUM
    assert get_base_priority('water_supply') == PriorityCategory.HIGH
    # test case insensitivity
    assert get_base_priority(' Road Damage ') == PriorityCategory.HIGH
    # Unknown default to MEDIUM
    assert get_base_priority('unknown') == PriorityCategory.MEDIUM

def test_calculate_final_priority_critical_promotes():
    assert calculate_final_priority(PriorityCategory.LOW, 'critical') == PriorityCategory.MEDIUM
    assert calculate_final_priority(PriorityCategory.MEDIUM, 'critical') == PriorityCategory.HIGH
    assert calculate_final_priority(PriorityCategory.HIGH, 'critical') == PriorityCategory.HIGH

def test_calculate_final_priority_low_demotes():
    assert calculate_final_priority(PriorityCategory.HIGH, 'low') == PriorityCategory.MEDIUM
    assert calculate_final_priority(PriorityCategory.MEDIUM, 'low') == PriorityCategory.LOW
    assert calculate_final_priority(PriorityCategory.LOW, 'low') == PriorityCategory.LOW

def test_calculate_final_priority_medium_high_retains():
    assert calculate_final_priority(PriorityCategory.HIGH, 'medium') == PriorityCategory.HIGH
    assert calculate_final_priority(PriorityCategory.MEDIUM, 'medium') == PriorityCategory.MEDIUM
    assert calculate_final_priority(PriorityCategory.LOW, 'high') == PriorityCategory.LOW
    
def test_calculate_final_priority_ai_failure():
    assert calculate_final_priority(PriorityCategory.HIGH, None) == PriorityCategory.HIGH
    assert calculate_final_priority(PriorityCategory.MEDIUM, None) == PriorityCategory.MEDIUM


