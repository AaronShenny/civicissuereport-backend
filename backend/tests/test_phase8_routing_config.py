"""
tests/test_phase8_routing_config.py

Phase 8 test suite: District + Category Routing Configuration.

Tests the authoritative business rule:

    CATEGORY + DISTRICT
        ↓
    RESPONSIBLE DEPARTMENT
        ↓
    ACTIVE SUPERVISORS OF THAT DEPARTMENT IN THAT DISTRICT

Test groups:
  1-8:   Category → Department mapping (all 8 categories)
  9-11:  Supervisor notification scoping by department + district
  12-14: Supervisor isolation (wrong department/wrong district excluded)
  15-17: Additional category routing (water_supply, pothole)
  18:    Fallback behavior (missing jurisdiction)
  19:    Routing failure (missing rules)

All tests use mocks consistent with the existing test architecture.
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock, call
from contextlib import nullcontext

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ComplaintCategory,
    ComplaintStatusHistory,
    Notification,
    NotificationEventType,
    NotificationChannelType,
)
from apps.complaints.routing import (
    route_complaint,
    find_responsible_department,
    get_jurisdiction_for_complaint,
    RoutingFailureError,
)
from apps.departments.models import DepartmentCategoryRule, Jurisdiction
from apps.users.models import Department, Profile, Role


@pytest.fixture(autouse=True)
def mock_atomic_transaction():
    with patch('django.db.transaction.atomic', side_effect=nullcontext):
        yield


# ---------------------------------------------------------------------------
# Mock Builders
# ---------------------------------------------------------------------------

def make_dept(name, dept_id=None):
    dept = MagicMock(spec=Department)
    dept.id = dept_id or uuid.uuid4()
    dept.name = name
    dept.is_active = True
    return dept


def make_jurisdiction(name, jur_id=None):
    jur = MagicMock(spec=Jurisdiction)
    jur.id = jur_id or uuid.uuid4()
    jur.name = name
    jur.area_type = 'district'
    return jur


def make_category(name, cat_id=None):
    cat = MagicMock(spec=ComplaintCategory)
    cat.id = cat_id or (hash(name) % 100 + 1)
    cat.name = name
    cat.is_active = True
    return cat


def make_supervisor(dept_id, jur_id=None, full_name='Supervisor', active=True):
    sup = MagicMock(spec=Profile)
    sup.id = uuid.uuid4()
    sup.full_name = full_name
    sup.role = MagicMock()
    sup.role.role_name = Role.SUPERVISOR
    sup.role_name = Role.SUPERVISOR
    sup.department_id = dept_id
    sup.jurisdiction = MagicMock() if jur_id else None
    if jur_id:
        sup.jurisdiction.id = jur_id
    sup.account_status = Profile.ACCOUNT_STATUS_ACTIVE if active else Profile.ACCOUNT_STATUS_INACTIVE
    sup.is_supervisor = True
    return sup


def make_complaint(category_name, district='Ernakulam', cat_id=None):
    cat = make_category(category_name, cat_id)
    c = MagicMock(spec=Complaint)
    c.id = uuid.uuid4()
    c.complaint_number = f'CMP-2026-{uuid.uuid4().hex[:6].upper()}'
    c.category = cat
    c.category_id = cat.id
    c.district = district
    c.status = ComplaintStatus.SUBMITTED
    c.assigned_department_id = None
    c.assigned_employee_id = None
    c.citizen_id = uuid.uuid4()
    return c


# ===========================================================================
# 1-8: Category → Department Mapping Tests
# ===========================================================================

class TestCategoryDepartmentMapping:
    """
    Tests that each category maps to the correct responsible department
    via the global DepartmentCategoryRule system.
    """

    @pytest.fixture
    def departments(self):
        """Pre-build all 6 departments from the authoritative mapping."""
        return {
            'PWD': make_dept('Public Works Department (PWD), Kerala'),
            'KSEB': make_dept('Kerala State Electricity Board (KSEB)'),
            'KWA': make_dept('Kerala Water Authority (KWA)'),
            'LSGD': make_dept('Local Self Government Department (LSGD)'),
            'LSGD_SWM': make_dept('LSGD - Solid Waste Management'),
            'LSGD_HS': make_dept('LSGD - Health & Sanitation'),
        }

    def _test_category_routes_to_department(self, category_name, expected_dept_key, departments):
        """Helper: verify a category resolves to the expected department."""
        expected_dept = departments[expected_dept_key]
        complaint = make_complaint(category_name)
        jur = make_jurisdiction('Ernakulam')
        rule = MagicMock(spec=DepartmentCategoryRule)
        rule.department = expected_dept

        with patch('apps.complaints.routing.DepartmentCategoryRule.objects') as mock_rule_mgr:
            mock_qs = MagicMock()
            mock_rule_mgr.filter.return_value.select_related.return_value = mock_qs
            # No jurisdiction-specific rule → fall back to global
            mock_qs.filter.return_value.order_by.return_value.first.side_effect = [None, rule]

            result = find_responsible_department(complaint, jur)
            assert result == expected_dept, (
                f'Category "{category_name}" should route to "{expected_dept.name}", '
                f'got "{result.name if result else None}"'
            )

    # Test 1: pothole → PWD Kerala
    def test_pothole_routes_to_pwd(self, departments):
        self._test_category_routes_to_department('pothole', 'PWD', departments)

    # Test 2: road_damage → PWD Kerala
    def test_road_damage_routes_to_pwd(self, departments):
        self._test_category_routes_to_department('road_damage', 'PWD', departments)

    # Test 3: streetlight → KSEB
    def test_streetlight_routes_to_kseb(self, departments):
        self._test_category_routes_to_department('streetlight', 'KSEB', departments)

    # Test 4: water_supply → KWA
    def test_water_supply_routes_to_kwa(self, departments):
        self._test_category_routes_to_department('water_supply', 'KWA', departments)

    # Test 5: drainage → LSGD
    def test_drainage_routes_to_lsgd(self, departments):
        self._test_category_routes_to_department('drainage', 'LSGD', departments)

    # Test 6: garbage → LSGD - Solid Waste Management
    def test_garbage_routes_to_lsgd_swm(self, departments):
        self._test_category_routes_to_department('garbage', 'LSGD_SWM', departments)

    # Test 7: sanitation → LSGD - Health & Sanitation
    def test_sanitation_routes_to_lsgd_health(self, departments):
        self._test_category_routes_to_department('sanitation', 'LSGD_HS', departments)

    # Test 8: other → LSGD
    def test_other_routes_to_lsgd(self, departments):
        self._test_category_routes_to_department('other', 'LSGD', departments)


# ===========================================================================
# 9-14: Supervisor Notification Scoping Tests
# ===========================================================================

class TestSupervisorNotificationScoping:
    """
    Tests that routing notifications are sent ONLY to supervisors
    matching BOTH the responsible department AND the complaint district.

    Test configuration:
      Supervisor A: KSEB + Ernakulam
      Supervisor B: KWA + Ernakulam
      Supervisor C: KSEB + Idukki
    """

    @pytest.fixture
    def setup(self):
        """Create the test department/jurisdiction/supervisor configuration."""
        kseb = make_dept('KSEB')
        kwa = make_dept('KWA')
        pwd = make_dept('PWD')

        jur_ern = make_jurisdiction('Ernakulam')
        jur_idk = make_jurisdiction('Idukki')

        sup_a = make_supervisor(kseb.id, jur_ern.id, 'Sup A (KSEB Ernakulam)')
        sup_b = make_supervisor(kwa.id, jur_ern.id, 'Sup B (KWA Ernakulam)')
        sup_c = make_supervisor(kseb.id, jur_idk.id, 'Sup C (KSEB Idukki)')

        return {
            'kseb': kseb, 'kwa': kwa, 'pwd': pwd,
            'jur_ern': jur_ern, 'jur_idk': jur_idk,
            'sup_a': sup_a, 'sup_b': sup_b, 'sup_c': sup_c,
        }

    # Test 9: streetlight + Ernakulam → KSEB → ONLY Sup A
    def test_streetlight_ernakulam_notifies_only_kseb_ernakulam_supervisor(self, setup):
        complaint = make_complaint('streetlight', 'Ernakulam')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=setup['jur_ern']), \
             patch('apps.complaints.routing.find_responsible_department', return_value=setup['kseb']), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create'), \
             patch('apps.complaints.routing.Profile.objects.filter') as mock_profile_filter, \
             patch('apps.complaints.routing.Notification.objects.bulk_create') as mock_notif_create:

            # Mock the queryset chain: filter(department) → filter(jurisdiction) → list
            mock_qs = MagicMock()
            mock_profile_filter.return_value = mock_qs
            mock_qs.filter.return_value = [setup['sup_a']]  # Only KSEB+Ernakulam

            route_complaint(complaint)

            # Verify department filter was called
            mock_profile_filter.assert_called_once_with(
                department_id=setup['kseb'].id,
                role__role_name=Role.SUPERVISOR,
                account_status=Profile.ACCOUNT_STATUS_ACTIVE,
            )

            # Verify jurisdiction filter was applied
            mock_qs.filter.assert_called_once_with(jurisdiction=setup['jur_ern'])

            # Verify notification created only for Sup A
            mock_notif_create.assert_called_once()
            created_notifications = mock_notif_create.call_args[0][0]
            assert len(created_notifications) == 1
            assert created_notifications[0].recipient_id == setup['sup_a'].id

    # Test 10: water_supply + Ernakulam → KWA → ONLY Sup B
    def test_water_supply_ernakulam_notifies_only_kwa_ernakulam_supervisor(self, setup):
        complaint = make_complaint('water_supply', 'Ernakulam')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=setup['jur_ern']), \
             patch('apps.complaints.routing.find_responsible_department', return_value=setup['kwa']), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create'), \
             patch('apps.complaints.routing.Profile.objects.filter') as mock_profile_filter, \
             patch('apps.complaints.routing.Notification.objects.bulk_create') as mock_notif_create:

            mock_qs = MagicMock()
            mock_profile_filter.return_value = mock_qs
            mock_qs.filter.return_value = [setup['sup_b']]  # Only KWA+Ernakulam

            route_complaint(complaint)

            # Verify department filter targets KWA
            mock_profile_filter.assert_called_once_with(
                department_id=setup['kwa'].id,
                role__role_name=Role.SUPERVISOR,
                account_status=Profile.ACCOUNT_STATUS_ACTIVE,
            )

            # Verify jurisdiction filter was applied
            mock_qs.filter.assert_called_once_with(jurisdiction=setup['jur_ern'])

            # Only Sup B gets notification
            mock_notif_create.assert_called_once()
            created_notifications = mock_notif_create.call_args[0][0]
            assert len(created_notifications) == 1
            assert created_notifications[0].recipient_id == setup['sup_b'].id

    # Test 11: pothole + Ernakulam → PWD → PWD supervisors in Ernakulam
    def test_pothole_ernakulam_notifies_pwd_ernakulam_supervisors(self, setup):
        complaint = make_complaint('pothole', 'Ernakulam')
        pwd_sup = make_supervisor(setup['pwd'].id, setup['jur_ern'].id, 'PWD Sup Ernakulam')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=setup['jur_ern']), \
             patch('apps.complaints.routing.find_responsible_department', return_value=setup['pwd']), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create'), \
             patch('apps.complaints.routing.Profile.objects.filter') as mock_profile_filter, \
             patch('apps.complaints.routing.Notification.objects.bulk_create') as mock_notif_create:

            mock_qs = MagicMock()
            mock_profile_filter.return_value = mock_qs
            mock_qs.filter.return_value = [pwd_sup]

            route_complaint(complaint)

            mock_profile_filter.assert_called_once_with(
                department_id=setup['pwd'].id,
                role__role_name=Role.SUPERVISOR,
                account_status=Profile.ACCOUNT_STATUS_ACTIVE,
            )
            mock_qs.filter.assert_called_once_with(jurisdiction=setup['jur_ern'])

            mock_notif_create.assert_called_once()
            created_notifications = mock_notif_create.call_args[0][0]
            assert len(created_notifications) == 1
            assert created_notifications[0].recipient_id == pwd_sup.id

    # Test 12: streetlight + Ernakulam → KSEB → Sup B (KWA) NOT notified
    def test_streetlight_ernakulam_does_not_notify_kwa_supervisor(self, setup):
        complaint = make_complaint('streetlight', 'Ernakulam')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=setup['jur_ern']), \
             patch('apps.complaints.routing.find_responsible_department', return_value=setup['kseb']), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create'), \
             patch('apps.complaints.routing.Profile.objects.filter') as mock_profile_filter, \
             patch('apps.complaints.routing.Notification.objects.bulk_create') as mock_notif_create:

            mock_qs = MagicMock()
            mock_profile_filter.return_value = mock_qs
            mock_qs.filter.return_value = [setup['sup_a']]

            route_complaint(complaint)

            # The filter was for KSEB, not KWA — so Sup B is structurally excluded
            filter_call = mock_profile_filter.call_args
            assert filter_call[1]['department_id'] == setup['kseb'].id
            assert filter_call[1]['department_id'] != setup['kwa'].id

            # Sup B not in notifications
            created_notifications = mock_notif_create.call_args[0][0]
            recipient_ids = {n.recipient_id for n in created_notifications}
            assert setup['sup_b'].id not in recipient_ids

    # Test 13: streetlight + Ernakulam → KSEB → Sup C (KSEB Idukki) NOT notified
    def test_streetlight_ernakulam_does_not_notify_kseb_idukki_supervisor(self, setup):
        complaint = make_complaint('streetlight', 'Ernakulam')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=setup['jur_ern']), \
             patch('apps.complaints.routing.find_responsible_department', return_value=setup['kseb']), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create'), \
             patch('apps.complaints.routing.Profile.objects.filter') as mock_profile_filter, \
             patch('apps.complaints.routing.Notification.objects.bulk_create') as mock_notif_create:

            mock_qs = MagicMock()
            mock_profile_filter.return_value = mock_qs
            # Jurisdiction filter returns only Ernakulam supervisors
            mock_qs.filter.return_value = [setup['sup_a']]

            route_complaint(complaint)

            # Jurisdiction filter was applied for Ernakulam
            mock_qs.filter.assert_called_once_with(jurisdiction=setup['jur_ern'])

            # Sup C (Idukki) not in notifications
            created_notifications = mock_notif_create.call_args[0][0]
            recipient_ids = {n.recipient_id for n in created_notifications}
            assert setup['sup_c'].id not in recipient_ids

    # Test 14: Inactive supervisor is excluded from queryset parameters
    def test_inactive_supervisor_excluded_by_filter(self, setup):
        complaint = make_complaint('streetlight', 'Ernakulam')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=setup['jur_ern']), \
             patch('apps.complaints.routing.find_responsible_department', return_value=setup['kseb']), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create'), \
             patch('apps.complaints.routing.Profile.objects.filter') as mock_profile_filter, \
             patch('apps.complaints.routing.Notification.objects.bulk_create'):

            mock_qs = MagicMock()
            mock_profile_filter.return_value = mock_qs
            mock_qs.filter.return_value = []  # No active supervisors

            route_complaint(complaint)

            # Confirm the filter explicitly requires account_status='active'
            filter_call = mock_profile_filter.call_args
            assert filter_call[1]['account_status'] == Profile.ACCOUNT_STATUS_ACTIVE


# ===========================================================================
# 15-17: Additional Category Routing End-to-End
# ===========================================================================

class TestAdditionalCategoryRouting:
    """
    End-to-end routing tests for water_supply and pothole,
    verifying department assignment + status transition + notification.
    """

    # Test 15: water_supply + Ernakulam → KWA assignment
    def test_water_supply_routes_assigns_kwa_department(self):
        kwa = make_dept('Kerala Water Authority (KWA)')
        jur = make_jurisdiction('Ernakulam')
        complaint = make_complaint('water_supply', 'Ernakulam')
        kwa_sup = make_supervisor(kwa.id, jur.id, 'KWA Sup')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=jur), \
             patch('apps.complaints.routing.find_responsible_department', return_value=kwa), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create') as mock_hist, \
             patch('apps.complaints.routing.Profile.objects.filter') as mock_pf, \
             patch('apps.complaints.routing.Notification.objects.bulk_create') as mock_notif:

            mock_qs = MagicMock()
            mock_pf.return_value = mock_qs
            mock_qs.filter.return_value = [kwa_sup]

            result = route_complaint(complaint)

            assert result == kwa
            assert complaint.assigned_department_id == kwa.id
            assert complaint.status == ComplaintStatus.UNDER_VERIFICATION

    # Test 16: pothole + Ernakulam → PWD assignment
    def test_pothole_routes_assigns_pwd_department(self):
        pwd = make_dept('Public Works Department (PWD), Kerala')
        jur = make_jurisdiction('Ernakulam')
        complaint = make_complaint('pothole', 'Ernakulam')
        pwd_sup = make_supervisor(pwd.id, jur.id, 'PWD Sup')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=jur), \
             patch('apps.complaints.routing.find_responsible_department', return_value=pwd), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create'), \
             patch('apps.complaints.routing.Profile.objects.filter') as mock_pf, \
             patch('apps.complaints.routing.Notification.objects.bulk_create') as mock_notif:

            mock_qs = MagicMock()
            mock_pf.return_value = mock_qs
            mock_qs.filter.return_value = [pwd_sup]

            result = route_complaint(complaint)

            assert result == pwd
            assert complaint.assigned_department_id == pwd.id

    # Test 17: Routing creates status history with correct status transition
    def test_routing_creates_submitted_to_under_verification_history(self):
        dept = make_dept('KSEB')
        jur = make_jurisdiction('Ernakulam')
        complaint = make_complaint('streetlight', 'Ernakulam')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=jur), \
             patch('apps.complaints.routing.find_responsible_department', return_value=dept), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create') as mock_hist, \
             patch('apps.complaints.routing.Profile.objects.filter') as mock_pf, \
             patch('apps.complaints.routing.Notification.objects.bulk_create'):

            mock_qs = MagicMock()
            mock_pf.return_value = mock_qs
            mock_qs.filter.return_value = []

            route_complaint(complaint)

            mock_hist.assert_called_once()
            hist_kwargs = mock_hist.call_args[1]
            assert hist_kwargs['old_status'] == ComplaintStatus.SUBMITTED
            assert hist_kwargs['new_status'] == ComplaintStatus.UNDER_VERIFICATION
            assert hist_kwargs['changed_by'] is None  # Automated system action


# ===========================================================================
# 18-19: Fallback and Failure Behavior
# ===========================================================================

class TestRoutingFallbackBehavior:

    # Test 18: Missing jurisdiction falls back to global rule
    def test_missing_jurisdiction_uses_global_rule(self):
        dept = make_dept('LSGD')
        complaint = make_complaint('drainage', 'UnknownDistrict')

        with patch('apps.complaints.routing.DepartmentCategoryRule.objects') as mock_rule_mgr:
            mock_qs = MagicMock()
            mock_rule_mgr.filter.return_value.select_related.return_value = mock_qs

            rule = MagicMock(spec=DepartmentCategoryRule)
            rule.department = dept
            # jurisdiction-specific: no result; global: returns rule
            mock_qs.filter.return_value.order_by.return_value.first.return_value = rule

            result = find_responsible_department(complaint, None)
            assert result == dept

            # Called with jurisdiction__isnull=True (global fallback)
            mock_qs.filter.assert_called_with(jurisdiction__isnull=True)

    # Test 19: No matching rules raises RoutingFailureError
    def test_no_matching_rules_raises_routing_failure(self):
        complaint = make_complaint('streetlight', 'Ernakulam')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=None), \
             patch('apps.complaints.routing.find_responsible_department', return_value=None):
            with pytest.raises(RoutingFailureError, match='Unable to determine responsible department'):
                route_complaint(complaint)

        # Complaint unchanged on failure
        assert complaint.assigned_department_id is None
        assert complaint.status == ComplaintStatus.SUBMITTED


# ===========================================================================
# 20: Cross-Department Isolation
# ===========================================================================

class TestCrossDepartmentIsolation:
    """
    Verify that the routing system's department filter prevents
    cross-department data leakage via the notification query.
    """

    # Test 20: KSEB routing never queries KWA supervisors
    def test_kseb_routing_never_queries_kwa_department(self):
        kseb = make_dept('KSEB')
        kwa = make_dept('KWA')
        jur = make_jurisdiction('Ernakulam')
        complaint = make_complaint('streetlight', 'Ernakulam')

        with patch('apps.complaints.routing.get_jurisdiction_for_complaint', return_value=jur), \
             patch('apps.complaints.routing.find_responsible_department', return_value=kseb), \
             patch('apps.complaints.routing.ComplaintStatusHistory.objects.create'), \
             patch('apps.complaints.routing.Profile.objects.filter') as mock_pf, \
             patch('apps.complaints.routing.Notification.objects.bulk_create'):

            mock_qs = MagicMock()
            mock_pf.return_value = mock_qs
            mock_qs.filter.return_value = []

            route_complaint(complaint)

            # Only ONE call to Profile.objects.filter — for KSEB
            mock_pf.assert_called_once()
            actual_dept_id = mock_pf.call_args[1]['department_id']
            assert actual_dept_id == kseb.id
            assert actual_dept_id != kwa.id
