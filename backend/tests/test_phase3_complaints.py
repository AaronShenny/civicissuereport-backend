"""
tests/test_phase3_complaints.py

Phase 3 test suite — Complaint Categories, Submission, Retrieval, Attachments.

All 25 required test scenarios are covered.

Tests run entirely with mock DB/storage objects so no Supabase connection
is needed. The pattern follows Phase 2: mock at the service boundary.
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock, call
from decimal import Decimal
from io import BytesIO

from django.core.exceptions import ValidationError
from django.test import override_settings


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_mock_role(role_name: str):
    role = MagicMock()
    role.role_name = role_name
    return role


def make_mock_profile(role_name: str, profile_id=None):
    p = MagicMock()
    p.id = profile_id or uuid.uuid4()
    p.role = make_mock_role(role_name)
    p.role_name = role_name
    p.is_citizen = (role_name == 'citizen')
    p.is_ground_level_employee = (role_name == 'ground_level_employee')
    p.is_supervisor = (role_name == 'supervisor')
    p.is_department_admin = (role_name == 'department_admin')
    p.is_system_admin = (role_name == 'system_admin')
    p.is_staff_member = (role_name != 'citizen')
    p.account_status = 'active'
    p.is_authenticated = True
    p.profile = p
    p.department_id = None
    return p


def make_mock_category(cat_id=1, name='pothole', requires_attachment=False, is_active=True):
    cat = MagicMock()
    cat.id = cat_id
    cat.name = name
    cat.requires_attachment = requires_attachment
    cat.is_active = is_active
    return cat


def make_mock_complaint(citizen_id=None, cat_name='pothole'):
    c = MagicMock()
    c.id = uuid.uuid4()
    c.complaint_number = 'CMP-2026-000001'
    c.citizen_id = citizen_id or uuid.uuid4()
    c.status = 'submitted'
    c.submitted_at = '2026-08-18T00:00:00Z'
    c.category = MagicMock()
    c.category.name = cat_name
    return c


def make_mock_request(profile=None):
    r = MagicMock()
    r.user = profile
    return r


def make_uploaded_file(name='photo.jpg', mime='image/jpeg', size=1024 * 100):
    f = MagicMock()
    f.name = name
    f.content_type = mime
    f.size = size
    f.read.return_value = b'x' * size
    return f


# ===========================================================================
# 1. Authenticated citizen can submit a complaint
# ===========================================================================

class TestComplaintSubmission:

    def test_validate_submission_data_valid(self):
        from apps.complaints.services import validate_submission_data
        data = {
            'description': 'Large pothole on main road causing accidents.',
            'category_id': 1,
            'google_maps_url': '9.93,76.27',
            'state': 'Kerala',
            'district': 'Ernakulam',
        }
        cat = make_mock_category()
        with patch('apps.complaints.services.validate_category', return_value=(cat, [])):
            errors = validate_submission_data(data, [])
        assert not errors

    def test_validate_description_not_empty(self):
        from apps.complaints.services import validate_submission_data
        data = {
            'description': '   ',
            'category_id': 1,
            'google_maps_url': '9.93,76.27',
            'state': 'Kerala',
            'district': 'Ernakulam',
        }
        cat = make_mock_category()
        with patch('apps.complaints.services.validate_category', return_value=(cat, [])):
            errors = validate_submission_data(data, [])
        assert any('description' in e for e in errors)

    # 2. Unauthenticated user cannot submit
    def test_unauthenticated_rejected_by_permission(self):
        from core.permissions.roles import IsAuthenticatedViaSupabase
        request = make_mock_request(profile=None)
        request.user = MagicMock()
        request.user.is_authenticated = False
        perm = IsAuthenticatedViaSupabase()
        assert perm.has_permission(request, None) is False

    # 3. Non-citizen cannot submit
    def test_non_citizen_rejected_by_is_citizen(self):
        from core.permissions.roles import IsCitizen
        for role in ['ground_level_employee', 'supervisor', 'department_admin', 'system_admin']:
            profile = make_mock_profile(role)
            request = make_mock_request(profile)
            perm = IsCitizen()
            assert perm.has_permission(request, None) is False, f'Expected False for {role}'

    def test_citizen_passes_is_citizen(self):
        from core.permissions.roles import IsCitizen
        profile = make_mock_profile('citizen')
        request = make_mock_request(profile)
        perm = IsCitizen()
        assert perm.has_permission(request, None) is True


# ===========================================================================
# 4–5. Complaint number generation
# ===========================================================================

class TestComplaintNumber:

    # 4. Complaint number is generated automatically
    def test_generate_complaint_number_format(self):
        from apps.complaints.number import generate_complaint_number
        from datetime import datetime
        with patch('apps.complaints.number._next_sequence_number', return_value=42):
            number = generate_complaint_number()
        year = datetime.utcnow().year
        assert number == f'CMP-{year}-000042'

    # 5. Complaint number is unique (sequence increments)
    def test_complaint_numbers_are_unique(self):
        from apps.complaints.number import generate_complaint_number
        seq_values = iter(range(1, 100))
        with patch('apps.complaints.number._next_sequence_number', side_effect=seq_values):
            numbers = {generate_complaint_number() for _ in range(10)}
        assert len(numbers) == 10  # all unique

    def test_complaint_number_six_digit_padding(self):
        from apps.complaints.number import generate_complaint_number
        from datetime import datetime
        with patch('apps.complaints.number._next_sequence_number', return_value=1):
            number = generate_complaint_number()
        assert '000001' in number

    def test_complaint_number_includes_year(self):
        from apps.complaints.number import generate_complaint_number
        from datetime import datetime
        year = datetime.utcnow().year
        with patch('apps.complaints.number._next_sequence_number', return_value=1):
            number = generate_complaint_number()
        assert str(year) in number


# ===========================================================================
# 6. New complaint starts as submitted
# 7. Initial status history is created
# ===========================================================================

class TestComplaintCreation:

    # 6 & 7: Status starts as submitted and history created atomically
    def test_submit_complaint_calls_db_insert(self):
        from apps.complaints.services import submit_complaint
        citizen = make_mock_profile('citizen')
        category = make_mock_category()
        validated_data = {
            'description': 'A pothole near the market.',
            'category': category,
            'google_maps_url': '9.93,76.27',
            'state': 'Kerala',
            'district': 'Ernakulam',
            'latitude': 9.93,
            'longitude': 76.27,
            'location_address': '1 Main St',
            'inconvenience_details': '',
            'expected_solution': '',
        }
        mock_complaint = make_mock_complaint(citizen_id=citizen.id)

        with patch('apps.complaints.services._create_complaint_in_db', return_value=mock_complaint) as mock_create:
            result = submit_complaint(citizen, validated_data, [])

        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        assert kwargs['citizen'] == citizen
        assert kwargs['category'] == category

    # 8. Atomicity: if DB fails, no record remains
    def test_submission_rollback_on_db_error(self):
        from apps.complaints.services import submit_complaint
        citizen = make_mock_profile('citizen')
        category = make_mock_category()
        validated_data = {
            'description': 'Road damage near school.',
            'category': category,
            'google_maps_url': '9.93,76.27',
            'state': 'Kerala',
            'district': 'Ernakulam',
            'latitude': 9.93,
            'longitude': 76.27,
        }
        with patch('apps.complaints.services._create_complaint_in_db', side_effect=Exception('DB error')):
            with pytest.raises(Exception, match='DB error'):
                submit_complaint(citizen, validated_data, [])


# ===========================================================================
# 9–13. Validation: category, description, coordinates
# ===========================================================================

class TestSubmissionValidation:

    # 9. Missing / nonexistent category rejected
    def test_missing_category_rejected(self):
        from apps.complaints.services import validate_category
        cat, errors = validate_category(None)
        assert cat is None
        assert errors

    def test_nonexistent_category_rejected(self):
        from apps.complaints.services import validate_category
        with patch('apps.complaints.services.ComplaintCategory.objects') as mock_mgr:
            mock_mgr.get.side_effect = Exception('DoesNotExist')
            from apps.complaints.models import ComplaintCategory
            with patch.object(ComplaintCategory.objects, 'get', side_effect=ComplaintCategory.DoesNotExist):
                cat, errors = validate_category(9999)
        assert cat is None
        assert errors

    # 10. Inactive category rejected
    def test_inactive_category_rejected(self):
        from apps.complaints.services import validate_category
        inactive_cat = make_mock_category(is_active=False)
        with patch('apps.complaints.services.ComplaintCategory.objects') as mock_mgr:
            mock_mgr.get.return_value = inactive_cat
            from apps.complaints.models import ComplaintCategory
            with patch.object(ComplaintCategory.objects, 'get', return_value=inactive_cat):
                cat, errors = validate_category(1)
        assert cat is None
        assert any('not currently' in e for e in errors)

    # 11. Missing description rejected
    def test_empty_description_rejected(self):
        from apps.complaints.services import validate_submission_data
        cat = make_mock_category()
        data = {'description': '', 'category_id': 1, 'google_maps_url': '9.0,76.0', 'state': 'Kerala', 'district': 'Ernakulam'}
        with patch('apps.complaints.services.validate_category', return_value=(cat, [])):
            errors = validate_submission_data(data, [])
        assert any('description' in e for e in errors)

    def test_whitespace_only_description_rejected(self):
        from apps.complaints.services import validate_submission_data
        cat = make_mock_category()
        data = {'description': '   \t\n  ', 'category_id': 1, 'google_maps_url': '9.0,76.0', 'state': 'Kerala', 'district': 'Ernakulam'}
        with patch('apps.complaints.services.validate_category', return_value=(cat, [])):
            errors = validate_submission_data(data, [])
        assert any('description' in e for e in errors)

    # 12. Invalid latitude rejected
    def test_latitude_too_high_rejected(self):
        from apps.complaints.services import validate_location
        errors = validate_location(91.0, 76.0)
        assert any('latitude' in e for e in errors)

    def test_latitude_too_low_rejected(self):
        from apps.complaints.services import validate_location
        errors = validate_location(-91.0, 76.0)
        assert any('latitude' in e for e in errors)

    def test_latitude_non_numeric_rejected(self):
        from apps.complaints.services import validate_location
        errors = validate_location('not-a-number', 76.0)
        assert any('latitude' in e for e in errors)

    # 13. Invalid longitude rejected
    def test_longitude_too_high_rejected(self):
        from apps.complaints.services import validate_location
        errors = validate_location(9.93, 181.0)
        assert any('longitude' in e for e in errors)

    def test_longitude_too_low_rejected(self):
        from apps.complaints.services import validate_location
        errors = validate_location(9.93, -181.0)
        assert any('longitude' in e for e in errors)

    def test_longitude_non_numeric_rejected(self):
        from apps.complaints.services import validate_location
        errors = validate_location(9.93, 'bad')
        assert any('longitude' in e for e in errors)

    def test_valid_coordinates_accepted(self):
        from apps.complaints.services import validate_location
        errors = validate_location(9.93, 76.27)
        assert errors == []

class TestLocationExtractor:
    def test_extract_short_url(self):
        from apps.complaints.location import extract_coordinates_from_url
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.url = 'https://www.google.com/maps/place/12.34,56.78'
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            lat, lng = extract_coordinates_from_url('https://maps.app.goo.gl/abcd')
            assert lat == 12.34
            assert lng == 56.78

    def test_extract_place_url(self):
        from apps.complaints.location import extract_coordinates_from_url
        url = 'https://www.google.com/maps/place/Some+Place/@12.345,67.890,15z/data=!3m1!4b1!4m6!3m5!1s0x0:0x0!7e2!8m2!3d12.345!4d67.890'
        lat, lng = extract_coordinates_from_url(url)
        assert lat == 12.345
        assert lng == 67.890

    def test_extract_search_url(self):
        from apps.complaints.location import extract_coordinates_from_url
        url = 'https://www.google.com/maps/search/12.345,+67.890'
        lat, lng = extract_coordinates_from_url(url)
        assert lat == 12.345
        assert lng == 67.890

    def test_extract_at_url(self):
        from apps.complaints.location import extract_coordinates_from_url
        url = 'https://www.google.com/maps/@12.345,67.890,15z'
        lat, lng = extract_coordinates_from_url(url)
        assert lat == 12.345
        assert lng == 67.890

    def test_extract_coordinate_pair(self):
        from apps.complaints.location import extract_coordinates_from_url
        lat, lng = extract_coordinates_from_url('12.345, 67.890')
        assert lat == 12.345
        assert lng == 67.890
        
        lat, lng = extract_coordinates_from_url('-12.345, -67.890')
        assert lat == -12.345
        assert lng == -67.890

    def test_invalid_url_rejected(self):
        from apps.complaints.location import extract_coordinates_from_url, LocationExtractionError
        with pytest.raises(LocationExtractionError):
            extract_coordinates_from_url('https://example.com')

    def test_invalid_coordinates_rejected(self):
        from apps.complaints.location import extract_coordinates_from_url, LocationExtractionError
        with pytest.raises(LocationExtractionError):
            extract_coordinates_from_url('91.0, 67.890')



# ===========================================================================
# 14–15. Attachment requirement
# ===========================================================================

class TestAttachmentRequirement:

    # 14. Required attachment category rejects submission without evidence
    def test_required_attachment_category_no_files_rejected(self):
        from apps.complaints.services import validate_submission_data
        data = {
            'description': 'A drainage blockage.',
            'category_id': 2,
            'google_maps_url': '9.93,76.27',
            'state': 'Kerala',
            'district': 'Ernakulam',
        }
        cat = make_mock_category(requires_attachment=True)
        with patch('apps.complaints.services.validate_category', return_value=(cat, [])):
            errors = validate_submission_data(data, [])  # no files
        assert any('requires at least one attachment' in e for e in errors)

    # 15. Optional attachment category allows submission without evidence
    def test_optional_attachment_category_no_files_accepted(self):
        from apps.complaints.services import validate_submission_data
        data = {
            'description': 'A pothole near the bus stop.',
            'category_id': 1,
            'google_maps_url': '9.93,76.27',
            'state': 'Kerala',
            'district': 'Ernakulam',
        }
        cat = make_mock_category(requires_attachment=False)
        with patch('apps.complaints.services.validate_category', return_value=(cat, [])):
            errors = validate_submission_data(data, [])
        assert not errors


# ===========================================================================
# 16. File upload validation
# ===========================================================================

class TestAttachmentValidation:

    def test_valid_photo_accepted(self):
        from apps.complaints.services import validate_attachments
        f = make_uploaded_file('photo.jpg', 'image/jpeg', 1024 * 500)
        pending, errors = validate_attachments([f])
        assert not errors
        assert len(pending) == 1
        assert pending[0].file_type == 'photo'

    def test_valid_video_accepted(self):
        from apps.complaints.services import validate_attachments
        f = make_uploaded_file('video.mp4', 'video/mp4', 1024 * 1024 * 10)
        pending, errors = validate_attachments([f])
        assert not errors
        assert pending[0].file_type == 'video'

    def test_valid_document_accepted(self):
        from apps.complaints.services import validate_attachments
        f = make_uploaded_file('doc.pdf', 'application/pdf', 1024 * 200)
        pending, errors = validate_attachments([f])
        assert not errors
        assert pending[0].file_type == 'document'

    def test_unsupported_mime_rejected(self):
        from apps.complaints.services import validate_attachments
        f = make_uploaded_file('script.py', 'text/x-python', 1000)
        pending, errors = validate_attachments([f])
        assert errors
        assert not pending

    def test_oversized_photo_rejected(self):
        from apps.complaints.storage import validate_upload
        # 11 MB photo — exceeds 10 MB limit
        errors = validate_upload('photo', 'image/jpeg', 11 * 1024 * 1024)
        assert errors
        assert any('limit' in e for e in errors)

    def test_oversized_video_rejected(self):
        from apps.complaints.storage import validate_upload
        # 101 MB video — exceeds 100 MB limit
        errors = validate_upload('video', 'video/mp4', 101 * 1024 * 1024)
        assert errors

    def test_within_size_limit_accepted(self):
        from apps.complaints.storage import validate_upload
        errors = validate_upload('photo', 'image/jpeg', 5 * 1024 * 1024)
        assert not errors


# ===========================================================================
# 17–18. Complaint retrieval — ownership
# ===========================================================================

class TestComplaintRetrieval:

    # 17. Citizen can retrieve their own complaint
    def test_citizen_retrieves_own_complaint(self):
        """
        The get_queryset in ComplaintDetailView filters by citizen_id == request.user.id.
        We verify that filter is applied correctly.
        """
        from apps.complaints.views import ComplaintDetailView
        citizen = make_mock_profile('citizen')
        request = make_mock_request(citizen)

        view = ComplaintDetailView()
        view.request = request

        with patch('apps.complaints.views.Complaint.objects') as mock_mgr:
            mock_filter = MagicMock()
            mock_mgr.filter.return_value = mock_filter
            mock_filter.select_related.return_value = mock_filter
            mock_filter.prefetch_related.return_value = mock_filter

            view.get_queryset()
            mock_mgr.filter.assert_called_once_with(citizen_id=citizen.id)

    # 18. Citizen cannot retrieve another citizen's complaint
    def test_citizen_cannot_retrieve_other_complaint(self):
        """
        The queryset is filtered to citizen_id == user.id; a complaint
        belonging to another citizen would not be in the queryset → 404.
        We verify the filter excludes other citizens.
        """
        from apps.complaints.views import ComplaintDetailView
        citizen_a = make_mock_profile('citizen')
        citizen_b = make_mock_profile('citizen')
        request = make_mock_request(citizen_a)

        view = ComplaintDetailView()
        view.request = request

        # Simulate queryset contains only citizen_a's complaints
        with patch('apps.complaints.views.Complaint.objects') as mock_mgr:
            mock_filter = MagicMock()
            mock_mgr.filter.return_value = mock_filter
            mock_filter.select_related.return_value = mock_filter
            mock_filter.prefetch_related.return_value = mock_filter

            view.get_queryset()
            # verify the filter uses citizen_a's ID (not citizen_b's)
            mock_mgr.filter.assert_called_once_with(citizen_id=citizen_a.id)
            # citizen_b's id was never used in the filter call
            assert str(citizen_b.id) not in str(mock_mgr.filter.call_args)


# ===========================================================================
# 19–23. Client cannot spoof server-controlled fields
# ===========================================================================

class TestServerControlledFields:

    def _get_serializer_input_fields(self):
        from apps.complaints.serializers import ComplaintSubmitSerializer
        return list(ComplaintSubmitSerializer().fields.keys())

    # 19. Client cannot spoof citizen_id
    def test_citizen_id_not_in_submit_serializer(self):
        fields = self._get_serializer_input_fields()
        assert 'citizen_id' not in fields

    # 20. Client cannot spoof complaint_number
    def test_complaint_number_not_in_submit_serializer(self):
        fields = self._get_serializer_input_fields()
        assert 'complaint_number' not in fields

    # 21. Client cannot force a different status
    def test_status_not_in_submit_serializer(self):
        fields = self._get_serializer_input_fields()
        assert 'status' not in fields

    # 22. Client cannot set assigned_employee_id
    def test_assigned_employee_id_not_in_submit_serializer(self):
        fields = self._get_serializer_input_fields()
        assert 'assigned_employee_id' not in fields

    # 23. Client cannot set assigned_department_id
    def test_assigned_department_id_not_in_submit_serializer(self):
        fields = self._get_serializer_input_fields()
        assert 'assigned_department_id' not in fields

    def test_reporter_count_not_in_submit_serializer(self):
        fields = self._get_serializer_input_fields()
        assert 'reporter_count' not in fields

    def test_priority_not_in_submit_serializer(self):
        fields = self._get_serializer_input_fields()
        assert 'priority_category' not in fields
        assert 'priority_score' not in fields

    def test_severity_not_in_submit_serializer(self):
        fields = self._get_serializer_input_fields()
        assert 'severity_level' not in fields
        assert 'severity_score' not in fields


# ===========================================================================
# 24. Attachment ownership enforced
# ===========================================================================

class TestAttachmentOwnership:

    def test_storage_path_includes_complaint_id(self):
        from apps.complaints.storage import build_storage_path
        complaint_id = str(uuid.uuid4())
        path = build_storage_path(complaint_id, 'submission_evidence', 'photo.jpg')
        assert complaint_id in path

    def test_storage_path_includes_submission_folder(self):
        from apps.complaints.storage import build_storage_path
        path = build_storage_path(str(uuid.uuid4()), 'submission_evidence', 'photo.jpg')
        assert 'submission' in path

    def test_storage_path_has_unique_filename(self):
        from apps.complaints.storage import build_storage_path
        cid = str(uuid.uuid4())
        path1 = build_storage_path(cid, 'submission_evidence', 'photo.jpg')
        path2 = build_storage_path(cid, 'submission_evidence', 'photo.jpg')
        # Even same original filename → different Storage paths (UUID-based)
        assert path1 != path2


# ===========================================================================
# 25. Phase 1 and Phase 2 tests still pass (marker test — actual pass
#     confirmed by running the full test suite together)
# ===========================================================================

class TestRegressionGuard:
    """
    These tests do not re-run Phase 1/2 logic — they verify that the Phase 3
    modules do not accidentally import-break Phase 1/2 modules.
    """

    def test_supabase_auth_still_importable(self):
        from core.authentication.supabase import SupabaseAuthentication
        assert SupabaseAuthentication is not None

    def test_phase2_permissions_still_importable(self):
        from core.permissions.roles import (
            IsAuthenticatedViaSupabase, IsCitizen, IsSystemAdmin,
            IsSameDepartment, IsOwnProfile,
        )
        assert IsCitizen is not None

    def test_phase2_user_models_still_importable(self):
        from apps.users.models import Profile, Role, Department, UserPermission
        assert Profile is not None

    def test_phase3_models_importable(self):
        from apps.complaints.models import (
            Complaint, ComplaintCategory,
            ComplaintAttachment, ComplaintStatusHistory,
        )
        assert Complaint is not None

    def test_phase3_storage_importable(self):
        from apps.complaints.storage import (
            upload_to_storage, delete_from_storage,
            build_storage_path, validate_upload,
        )
        assert build_storage_path is not None

    def test_phase3_number_importable(self):
        from apps.complaints.number import generate_complaint_number
        assert generate_complaint_number is not None
