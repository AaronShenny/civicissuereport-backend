"""
tests/test_phase8_ai_severity.py

Phase 8: AI Severity Assessment — Comprehensive Unit/Application Tests.

TESTING LIMITATIONS (IMPORTANT):
    These tests use mocks for all external dependencies.
    They do NOT validate:
        - Real Gemini API responses or availability.
        - Real Supabase PostgreSQL RLS policies.
        - Real Supabase Storage object access.
        - Real network connectivity.

    All DB interactions use Django's in-memory SQLite test database.
    All Gemini API calls are mocked via unittest.mock.

Test categories:
    1.  Schema validation — valid LOW/MEDIUM/HIGH/CRITICAL results.
    2.  Schema validation — invalid enum, score, confidence, malformed JSON.
    3.  Provider — API timeout and API failure handling.
    4.  Provider — text-only, image-only, text+image inputs.
    5.  Service — classification record creation (INSERT, never UPDATE).
    6.  Service — severity synchronization to complaints table.
    7.  Service — classification history preservation (never overwrite).
    8.  Service — low-confidence review task creation.
    9.  Security — client cannot spoof severity fields.
    10. Security — API key not exposed in responses.
"""

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from unittest import TestCase
from django.test import override_settings


# ===========================================================================
# 1. SeverityResult Schema Validation Tests
# ===========================================================================

class TestParseAndValidateAIResponse(TestCase):
    """Tests for parse_and_validate_ai_response() in ai/schemas.py."""

    def _parse(self, raw: str):
        from apps.complaints.ai.schemas import parse_and_validate_ai_response
        return parse_and_validate_ai_response(raw)

    def _valid_payload(self, **overrides) -> str:
        base = {
            'severity_level': 'low',
            'severity_score': 15.0,
            'confidence': 85.0,
            'reason': 'Minor pothole on the road shoulder.',
        }
        base.update(overrides)
        return json.dumps(base)

    # --- Valid severity levels ---

    def test_valid_low(self):
        result = self._parse(self._valid_payload(severity_level='low', severity_score=15.0))
        self.assertEqual(result.severity_level, 'low')
        self.assertEqual(result.severity_score, 15.0)
        self.assertEqual(result.confidence, 85.0)
        self.assertIsNotNone(result.reason)

    def test_valid_medium(self):
        result = self._parse(self._valid_payload(severity_level='medium', severity_score=40.0))
        self.assertEqual(result.severity_level, 'medium')
        self.assertEqual(result.severity_score, 40.0)

    def test_valid_high(self):
        result = self._parse(self._valid_payload(severity_level='high', severity_score=65.0))
        self.assertEqual(result.severity_level, 'high')
        self.assertEqual(result.severity_score, 65.0)

    def test_valid_critical(self):
        result = self._parse(self._valid_payload(severity_level='critical', severity_score=90.0))
        self.assertEqual(result.severity_level, 'critical')
        self.assertEqual(result.severity_score, 90.0)

    def test_boundary_score_zero(self):
        result = self._parse(self._valid_payload(severity_level='low', severity_score=0.0))
        self.assertEqual(result.severity_score, 0.0)

    def test_boundary_score_hundred(self):
        result = self._parse(self._valid_payload(severity_level='critical', severity_score=100.0))
        self.assertEqual(result.severity_score, 100.0)

    def test_confidence_boundary_zero(self):
        result = self._parse(self._valid_payload(confidence=0.0))
        self.assertEqual(result.confidence, 0.0)

    def test_confidence_boundary_hundred(self):
        result = self._parse(self._valid_payload(confidence=100.0))
        self.assertEqual(result.confidence, 100.0)

    def test_case_insensitive_severity_level(self):
        """Model may return uppercase — schema normalizes to lowercase."""
        result = self._parse(self._valid_payload(severity_level='HIGH'))
        self.assertEqual(result.severity_level, 'high')

    # --- Invalid severity level ---

    def test_invalid_severity_level(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError) as ctx:
            self._parse(self._valid_payload(severity_level='extreme'))
        self.assertIn('extreme', str(ctx.exception))

    def test_invalid_severity_level_numeric(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError):
            self._parse(self._valid_payload(severity_level=3))

    def test_invalid_severity_level_empty(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError):
            self._parse(self._valid_payload(severity_level=''))

    # --- Invalid score ---

    def test_invalid_score_below_zero(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError) as ctx:
            self._parse(self._valid_payload(severity_score=-1.0))
        self.assertIn('severity_score', str(ctx.exception))

    def test_invalid_score_above_hundred(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError) as ctx:
            self._parse(self._valid_payload(severity_score=100.1))
        self.assertIn('severity_score', str(ctx.exception))

    def test_invalid_score_string(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError):
            self._parse(self._valid_payload(severity_score='high'))

    # --- Invalid confidence ---

    def test_invalid_confidence_below_zero(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError) as ctx:
            self._parse(self._valid_payload(confidence=-5.0))
        self.assertIn('confidence', str(ctx.exception))

    def test_invalid_confidence_above_hundred(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError) as ctx:
            self._parse(self._valid_payload(confidence=101.0))
        self.assertIn('confidence', str(ctx.exception))

    # --- Missing fields ---

    def test_missing_severity_level(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        payload = {'severity_score': 20.0, 'confidence': 80.0, 'reason': 'test'}
        with self.assertRaises(SeverityValidationError) as ctx:
            self._parse(json.dumps(payload))
        self.assertIn('severity_level', str(ctx.exception))

    def test_missing_severity_score(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        payload = {'severity_level': 'low', 'confidence': 80.0, 'reason': 'test'}
        with self.assertRaises(SeverityValidationError):
            self._parse(json.dumps(payload))

    def test_missing_confidence(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        payload = {'severity_level': 'low', 'severity_score': 20.0, 'reason': 'test'}
        with self.assertRaises(SeverityValidationError):
            self._parse(json.dumps(payload))

    def test_missing_reason(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        payload = {'severity_level': 'low', 'severity_score': 20.0, 'confidence': 80.0}
        with self.assertRaises(SeverityValidationError):
            self._parse(json.dumps(payload))

    # --- Malformed JSON ---

    def test_malformed_json_plain_text(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError) as ctx:
            self._parse('This is not JSON')
        self.assertIn('not valid JSON', str(ctx.exception))

    def test_malformed_json_truncated(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError):
            self._parse('{"severity_level": "low"')

    def test_malformed_json_array(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError):
            self._parse('[{"severity_level": "low"}]')

    def test_empty_string(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError):
            self._parse('')

    def test_whitespace_only(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError):
            self._parse('   ')

    def test_empty_reason(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError):
            self._parse(self._valid_payload(reason=''))

    def test_whitespace_reason(self):
        from apps.complaints.ai.schemas import SeverityValidationError
        with self.assertRaises(SeverityValidationError):
            self._parse(self._valid_payload(reason='   '))

    def test_strips_markdown_code_fences(self):
        """Schema validator strips markdown ```json fences some models emit."""
        payload = {
            'severity_level': 'medium',
            'severity_score': 40.0,
            'confidence': 75.0,
            'reason': 'Drainage blockage.',
        }
        raw = '```json\n' + json.dumps(payload) + '\n```'
        result = self._parse(raw)
        self.assertEqual(result.severity_level, 'medium')


# ===========================================================================
# 2. GeminiSeverityProvider Tests
# ===========================================================================

class TestGeminiSeverityProvider(TestCase):
    """Tests for GeminiSeverityProvider in ai/providers/gemini.py."""

    def _make_provider(self, api_key='test-key', model='gemini-3.6-flash'):
        from apps.complaints.ai.providers.gemini import GeminiSeverityProvider
        with override_settings(GEMINI_API_KEY=api_key, AI_GEMINI_MODEL=model):
            provider = GeminiSeverityProvider()
        return provider

    def _gemini_response(self, payload: dict) -> MagicMock:
        """Build a mock httpx.Response that returns a Gemini-style JSON envelope."""
        text_content = json.dumps(payload)
        response_body = {
            'candidates': [
                {
                    'content': {
                        'parts': [{'text': text_content}]
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response_body
        return mock_resp

    def _valid_payload(self, level='low') -> dict:
        scores = {'low': 15.0, 'medium': 40.0, 'high': 65.0, 'critical': 90.0}
        return {
            'severity_level': level,
            'severity_score': scores.get(level, 20.0),
            'confidence': 88.0,
            'reason': f'Test reason for {level} severity.',
        }

    # --- Missing API key ---

    def test_missing_api_key_raises_provider_error(self):
        from apps.complaints.ai.interfaces import SeverityProviderError
        from apps.complaints.ai.providers.gemini import GeminiSeverityProvider
        with override_settings(GEMINI_API_KEY=None):
            provider = GeminiSeverityProvider()
        with self.assertRaises(SeverityProviderError) as ctx:
            provider.assess('A broken road.', [])
        self.assertIn('GEMINI_API_KEY', str(ctx.exception))

    # --- Text-only input ---

    @patch('apps.complaints.ai.providers.gemini.httpx.post')
    def test_text_only_input(self, mock_post):
        mock_post.return_value = self._gemini_response(self._valid_payload('low'))
        provider = self._make_provider()
        result = provider.assess('Small pothole on road shoulder.', [])
        self.assertEqual(result.severity_level, 'low')
        # Verify API was called (with description in payload)
        self.assertTrue(mock_post.called)

    # --- Image-only input ---

    @patch('apps.complaints.ai.providers.gemini.httpx.post')
    def test_image_only_input(self, mock_post):
        mock_post.return_value = self._gemini_response(self._valid_payload('high'))
        provider = self._make_provider()
        image_data = [{'mime_type': 'image/jpeg', 'data': b'\xff\xd8\xff'}]
        result = provider.assess('', image_data)
        self.assertEqual(result.severity_level, 'high')

    # --- Text + image input ---

    @patch('apps.complaints.ai.providers.gemini.httpx.post')
    def test_text_and_image_input(self, mock_post):
        mock_post.return_value = self._gemini_response(self._valid_payload('critical'))
        provider = self._make_provider()
        image_data = [
            {'mime_type': 'image/png', 'data': b'\x89PNG\r\n'},
        ]
        result = provider.assess('Large sinkhole blocking the road.', image_data)
        self.assertEqual(result.severity_level, 'critical')
        # Verify inlineData was included in the request body
        call_args = mock_post.call_args
        body = call_args.kwargs.get('json') or call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get('json', {})
        parts = body['contents'][0]['parts']
        inline_parts = [p for p in parts if 'inlineData' in p or 'inline_data' in p]
        self.assertEqual(len(inline_parts), 1)

    # --- Unsupported MIME type is skipped ---

    @patch('apps.complaints.ai.providers.gemini.httpx.post')
    def test_unsupported_mime_type_skipped(self, mock_post):
        mock_post.return_value = self._gemini_response(self._valid_payload('low'))
        provider = self._make_provider()
        # video/mp4 is not a supported inline image MIME
        image_data = [{'mime_type': 'video/mp4', 'data': b'\x00\x00\x00\x20'}]
        result = provider.assess('Road damage.', image_data)
        self.assertEqual(result.severity_level, 'low')
        # Verify NO inlineData in request
        call_args = mock_post.call_args
        body = call_args.kwargs.get('json', {})
        parts = body.get('contents', [{}])[0].get('parts', [])
        inline_parts = [p for p in parts if 'inlineData' in p or 'inline_data' in p]
        self.assertEqual(len(inline_parts), 0)

    # --- API timeout ---

    @patch('apps.complaints.ai.providers.gemini.httpx.post')
    def test_api_timeout(self, mock_post):
        import httpx as _httpx
        from apps.complaints.ai.interfaces import SeverityProviderError
        mock_post.side_effect = _httpx.TimeoutException('Timed out')
        provider = self._make_provider()
        with self.assertRaises(SeverityProviderError) as ctx:
            provider.assess('Flooding on main road.', [])
        self.assertIn('timed out', str(ctx.exception).lower())

    # --- API network failure ---

    @patch('apps.complaints.ai.providers.gemini.httpx.post')
    def test_api_network_failure(self, mock_post):
        import httpx as _httpx
        from apps.complaints.ai.interfaces import SeverityProviderError
        mock_post.side_effect = _httpx.ConnectError('Connection refused')
        provider = self._make_provider()
        with self.assertRaises(SeverityProviderError) as ctx:
            provider.assess('Broken streetlight.', [])
        self.assertIn('network error', str(ctx.exception).lower())

    # --- HTTP non-200 response ---

    @patch('apps.complaints.ai.providers.gemini.httpx.post')
    def test_api_http_error(self, mock_post):
        from apps.complaints.ai.interfaces import SeverityProviderError
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = 'Rate limit exceeded'
        mock_post.return_value = mock_resp
        provider = self._make_provider()
        with self.assertRaises(SeverityProviderError) as ctx:
            provider.assess('Garbage pile.', [])
        self.assertIn('429', str(ctx.exception))

    # --- Malformed Gemini response structure ---

    @patch('apps.complaints.ai.providers.gemini.httpx.post')
    def test_malformed_gemini_response_structure(self, mock_post):
        from apps.complaints.ai.interfaces import SeverityProviderError
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'error': 'unexpected format'}
        mock_post.return_value = mock_resp
        provider = self._make_provider()
        with self.assertRaises(SeverityProviderError):
            provider.assess('Water supply issue.', [])

    # --- Invalid severity in Gemini response ---

    @patch('apps.complaints.ai.providers.gemini.httpx.post')
    def test_invalid_severity_in_gemini_response(self, mock_post):
        from apps.complaints.ai.interfaces import SeverityProviderError
        mock_post.return_value = self._gemini_response({
            'severity_level': 'catastrophic',  # Invalid
            'severity_score': 95.0,
            'confidence': 90.0,
            'reason': 'Test.',
        })
        provider = self._make_provider()
        with self.assertRaises(SeverityProviderError) as ctx:
            provider.assess('Some complaint.', [])
        self.assertIn('validation', str(ctx.exception).lower())

    # --- API key is never logged or returned ---

    @patch('apps.complaints.ai.providers.gemini.httpx.post')
    def test_api_key_not_in_request_body(self, mock_post):
        """API key is passed as URL param, never in the request body."""
        mock_post.return_value = self._gemini_response(self._valid_payload('medium'))
        provider = self._make_provider(api_key='super-secret-key-12345')
        provider.assess('A complaint.', [])
        call_args = mock_post.call_args
        body = call_args.kwargs.get('json', {})
        body_str = json.dumps(body)
        self.assertNotIn('super-secret-key-12345', body_str)


# ===========================================================================
# 3. ComplaintSeverityService Tests
# ===========================================================================

class TestComplaintSeverityService(TestCase):
    """
    Tests for ComplaintSeverityService in ai/service.py.

    Uses a mock provider — no real Gemini API calls are made.
    DB operations use the test SQLite database (not real Supabase PostgreSQL).
    """

    def _make_result(self, level='medium', score=40.0, confidence=85.0,
                     reason='Moderate road damage.'):
        from apps.complaints.ai.schemas import SeverityResult
        return SeverityResult(
            severity_level=level,
            severity_score=score,
            confidence=confidence,
            reason=reason,
        )

    def _make_service(self, provider=None):
        from apps.complaints.ai.service import ComplaintSeverityService
        mock_provider = provider or MagicMock()
        return ComplaintSeverityService(provider=mock_provider)

    # --- Provider failure does not affect complaint ---

    @patch('apps.complaints.ai.service._fetch_image_data_for_complaint', return_value=[])
    @patch('apps.complaints.ai.service._insert_classification_record')
    def test_provider_failure_does_not_raise(self, mock_insert, mock_images):
        from apps.complaints.ai.interfaces import SeverityProviderError

        mock_provider = MagicMock()
        mock_provider.assess.side_effect = SeverityProviderError('Gemini down')

        service = self._make_service(mock_provider)

        with patch('apps.complaints.models.Complaint.objects') as mock_objects:
            mock_complaint = MagicMock()
            mock_complaint.description = 'Road damage near school.'
            mock_objects.only.return_value.get.return_value = mock_complaint

            # Should NOT raise
            service.assess_complaint(str(uuid.uuid4()))

        # Classification should NOT have been inserted
        mock_insert.assert_not_called()

    # --- Complaint not found does not raise ---

    def test_complaint_not_found_does_not_raise(self):
        from apps.complaints.models import Complaint
        service = self._make_service()
        # Use a non-existent UUID — should log and return gracefully
        non_existent_id = str(uuid.uuid4())
        # No exception expected
        with patch('apps.complaints.models.Complaint.objects') as mock_objects:
            mock_objects.only.return_value.get.side_effect = Complaint.DoesNotExist
            service.assess_complaint(non_existent_id)

    # --- Valid result causes classification record INSERT ---

    @patch('apps.complaints.ai.service._sync_complaint_severity')
    @patch('apps.complaints.ai.service._create_review_task_if_needed')
    @patch('apps.complaints.ai.service._insert_classification_record', return_value='fake-classification-id')
    @patch('apps.complaints.ai.service._fetch_image_data_for_complaint', return_value=[])
    def test_valid_result_inserts_classification(
        self, mock_images, mock_insert, mock_review, mock_sync
    ):
        mock_provider = MagicMock()
        mock_provider.assess.return_value = self._make_result('high', 65.0, 90.0)

        service = self._make_service(mock_provider)

        with patch('apps.complaints.models.Complaint.objects') as mock_objects:
            mock_complaint = MagicMock()
            mock_complaint.description = 'Large pothole.'
            mock_objects.only.return_value.get.return_value = mock_complaint

            service.assess_complaint(str(uuid.uuid4()))

        mock_insert.assert_called_once()

    # --- Valid result causes severity sync ---

    @patch('apps.complaints.ai.service._create_review_task_if_needed')
    @patch('apps.complaints.ai.service._sync_complaint_severity')
    @patch('apps.complaints.ai.service._insert_classification_record', return_value='fake-id')
    @patch('apps.complaints.ai.service._fetch_image_data_for_complaint', return_value=[])
    def test_valid_result_syncs_severity(
        self, mock_images, mock_insert, mock_sync, mock_review
    ):
        mock_provider = MagicMock()
        result = self._make_result('critical', 90.0, 95.0)
        mock_provider.assess.return_value = result

        service = self._make_service(mock_provider)

        with patch('apps.complaints.models.Complaint.objects') as mock_objects:
            mock_complaint = MagicMock()
            mock_complaint.description = 'Sinkhole on highway.'
            mock_objects.only.return_value.get.return_value = mock_complaint

            service.assess_complaint(str(uuid.uuid4()))

        mock_sync.assert_called_once()
        call_result = mock_sync.call_args.kwargs.get('result') or mock_sync.call_args[0][1]
        self.assertEqual(call_result.severity_level, 'critical')

    # --- Classification history is preserved (INSERT not UPDATE) ---

    @patch('apps.complaints.ai.service._create_review_task_if_needed')
    @patch('apps.complaints.ai.service._sync_complaint_severity')
    @patch('apps.complaints.ai.service._insert_classification_record')
    @patch('apps.complaints.ai.service._fetch_image_data_for_complaint', return_value=[])
    def test_classification_history_preserved_on_second_run(
        self, mock_images, mock_insert, mock_sync, mock_review
    ):
        """Two runs on the same complaint each call _insert_classification_record once."""
        mock_insert.side_effect = ['class-id-1', 'class-id-2']
        mock_provider = MagicMock()
        mock_provider.assess.side_effect = [
            self._make_result('medium', 40.0, 85.0),
            self._make_result('high', 65.0, 88.0),
        ]
        service = self._make_service(mock_provider)
        complaint_id = str(uuid.uuid4())

        with patch('apps.complaints.models.Complaint.objects') as mock_objects:
            mock_complaint = MagicMock()
            mock_complaint.description = 'Some road issue.'
            mock_objects.only.return_value.get.return_value = mock_complaint

            service.assess_complaint(complaint_id)
            service.assess_complaint(complaint_id)

        # Two INSERTs — history preserved
        self.assertEqual(mock_insert.call_count, 2)

    # --- Low confidence creates review task ---

    @patch('apps.complaints.ai.service._create_review_task_if_needed')
    @patch('apps.complaints.ai.service._sync_complaint_severity')
    @patch('apps.complaints.ai.service._insert_classification_record', return_value='cls-id')
    @patch('apps.complaints.ai.service._fetch_image_data_for_complaint', return_value=[])
    @override_settings(AI_CONFIDENCE_THRESHOLD=70.0)
    def test_low_confidence_creates_review_task(
        self, mock_images, mock_insert, mock_sync, mock_review
    ):
        low_confidence_result = self._make_result('medium', 40.0, confidence=50.0)
        mock_provider = MagicMock()
        mock_provider.assess.return_value = low_confidence_result

        service = self._make_service(mock_provider)

        with patch('apps.complaints.models.Complaint.objects') as mock_objects:
            mock_complaint = MagicMock()
            mock_complaint.description = 'Unclear damage.'
            mock_objects.only.return_value.get.return_value = mock_complaint

            service.assess_complaint(str(uuid.uuid4()))

        mock_review.assert_called_once()
        call_kwargs = mock_review.call_args.kwargs
        self.assertEqual(call_kwargs.get('confidence'), 50.0)
        self.assertEqual(call_kwargs.get('threshold'), 70.0)

    # --- High confidence does NOT create review task ---

    @patch('apps.complaints.ai.service._create_review_task_if_needed')
    @patch('apps.complaints.ai.service._sync_complaint_severity')
    @patch('apps.complaints.ai.service._insert_classification_record', return_value='cls-id')
    @patch('apps.complaints.ai.service._fetch_image_data_for_complaint', return_value=[])
    @override_settings(AI_CONFIDENCE_THRESHOLD=70.0)
    def test_high_confidence_does_not_create_review_task(
        self, mock_images, mock_insert, mock_sync, mock_review
    ):
        high_confidence_result = self._make_result('high', 65.0, confidence=92.0)
        mock_provider = MagicMock()
        mock_provider.assess.return_value = high_confidence_result

        service = self._make_service(mock_provider)

        with patch('apps.complaints.models.Complaint.objects') as mock_objects:
            mock_complaint = MagicMock()
            mock_complaint.description = 'Road damage.'
            mock_objects.only.return_value.get.return_value = mock_complaint

            service.assess_complaint(str(uuid.uuid4()))

        # _create_review_task_if_needed is called but should do nothing at 92% confidence
        mock_review.assert_called_once()
        call_kwargs = mock_review.call_args.kwargs
        # Confidence >= threshold means no task is created inside the function
        self.assertGreaterEqual(call_kwargs.get('confidence', 0), call_kwargs.get('threshold', 70.0))

    # --- Image fetch failure falls back to text-only ---

    @patch('apps.complaints.ai.service._create_review_task_if_needed')
    @patch('apps.complaints.ai.service._sync_complaint_severity')
    @patch('apps.complaints.ai.service._insert_classification_record', return_value='cls-id')
    @patch('apps.complaints.ai.service._fetch_image_data_for_complaint')
    def test_image_fetch_failure_falls_back_to_text_only(
        self, mock_images, mock_insert, mock_sync, mock_review
    ):
        """If image fetching fails, assessment proceeds with description only."""
        mock_images.side_effect = Exception('Storage unreachable')
        mock_provider = MagicMock()
        mock_provider.assess.return_value = self._make_result('low', 15.0, 80.0)

        service = self._make_service(mock_provider)

        with patch('apps.complaints.models.Complaint.objects') as mock_objects:
            mock_complaint = MagicMock()
            mock_complaint.description = 'Minor pothole.'
            mock_objects.only.return_value.get.return_value = mock_complaint

            # Should NOT raise — falls back to text-only
            service.assess_complaint(str(uuid.uuid4()))

        # Provider was called with empty image_data
        mock_provider.assess.assert_called_once()
        call_args = mock_provider.assess.call_args
        # Support both keyword and positional arguments
        if call_args.kwargs.get('image_data') is not None:
            call_image_data = call_args.kwargs['image_data']
        elif len(call_args.args) > 1:
            call_image_data = call_args.args[1]
        else:
            call_image_data = []
        self.assertEqual(call_image_data, [])


# ===========================================================================
# 4. Confidence Threshold Configuration Tests
# ===========================================================================

class TestConfidenceThreshold(TestCase):
    """Tests that the confidence threshold is configurable and not hardcoded."""

    def test_default_threshold_is_70(self):
        from apps.complaints.ai.service import _get_confidence_threshold
        with override_settings(AI_CONFIDENCE_THRESHOLD=70.0):
            self.assertEqual(_get_confidence_threshold(), 70.0)

    def test_custom_threshold_is_respected(self):
        from apps.complaints.ai.service import _get_confidence_threshold
        with override_settings(AI_CONFIDENCE_THRESHOLD=55.0):
            self.assertEqual(_get_confidence_threshold(), 55.0)

    def test_threshold_at_boundary_zero(self):
        from apps.complaints.ai.service import _get_confidence_threshold
        with override_settings(AI_CONFIDENCE_THRESHOLD=0.0):
            self.assertEqual(_get_confidence_threshold(), 0.0)

    def test_review_task_created_when_confidence_below_threshold(self):
        from apps.complaints.ai.service import _create_review_task_if_needed
        # Should attempt DB insert when below threshold
        with patch('apps.complaints.ai.service.connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            now = datetime.now(timezone.utc)
            _create_review_task_if_needed(
                complaint_id=str(uuid.uuid4()),
                classification_id=str(uuid.uuid4()),
                confidence=45.0,
                threshold=70.0,
                now=now,
            )
            # cursor.execute should have been called
            self.assertTrue(mock_cursor.execute.called)

    def test_review_task_not_created_when_confidence_at_threshold(self):
        from apps.complaints.ai.service import _create_review_task_if_needed
        with patch('apps.complaints.ai.service.connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            now = datetime.now(timezone.utc)
            _create_review_task_if_needed(
                complaint_id=str(uuid.uuid4()),
                classification_id=str(uuid.uuid4()),
                confidence=70.0,
                threshold=70.0,
                now=now,
            )
            # At exactly threshold — no task created
            self.assertFalse(mock_cursor.execute.called)


# ===========================================================================
# 5. Security Tests
# ===========================================================================

class TestAISeveritySecurityEnforcement(TestCase):
    """
    Tests that severity fields cannot be spoofed by clients.
    The ComplaintSubmitSerializer explicitly excludes severity fields.
    """

    def test_severity_level_not_in_submit_serializer_fields(self):
        """Client-submitted severity_level must be rejected at the serializer."""
        from apps.complaints.serializers import ComplaintSubmitSerializer
        field_names = list(ComplaintSubmitSerializer().fields.keys())
        self.assertNotIn('severity_level', field_names)
        self.assertNotIn('severity_score', field_names)
        self.assertNotIn('confidence', field_names)
        self.assertNotIn('model_name', field_names)
        self.assertNotIn('model_version', field_names)

    def test_severity_fields_read_only_in_detail_serializer(self):
        """severity_level and severity_score must be read-only in the detail view."""
        from apps.complaints.serializers import ComplaintDetailSerializer
        meta = ComplaintDetailSerializer.Meta
        # ComplaintDetailSerializer.Meta.read_only_fields covers all fields
        self.assertEqual(meta.read_only_fields, '__all__')

    def test_gemini_api_key_not_in_provider_request_body(self):
        """
        API key must be passed in the x-goog-api-key HTTP header, never in the
        JSON request body.

        gemini-3.6-flash authentication change from gemini-2.0-flash:
            Previously: key passed as ?key= URL query parameter.
            Now: key passed as x-goog-api-key header.
            Reason: Query parameters appear in server/proxy access logs; headers
                    are not logged by default.
        """
        from apps.complaints.ai.providers.gemini import GeminiSeverityProvider

        with patch('apps.complaints.ai.providers.gemini.httpx.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            secret_key = 'top-secret-gemini-key-xyz'
            mock_resp.json.return_value = {
                'candidates': [{
                    'content': {'parts': [{'text': json.dumps({
                        'severity_level': 'low',
                        'severity_score': 10.0,
                        'confidence': 90.0,
                        'reason': 'Minor issue.',
                    })}]}
                }]
            }
            mock_post.return_value = mock_resp

            with override_settings(GEMINI_API_KEY=secret_key, AI_GEMINI_MODEL='gemini-3.6-flash'):
                provider = GeminiSeverityProvider()
                provider.assess('Test complaint.', [])

            call_kwargs = mock_post.call_args.kwargs
            json_body = json.dumps(call_kwargs.get('json', {}))
            request_headers = call_kwargs.get('headers', {})

            # Key must NOT appear in the JSON body
            self.assertNotIn(secret_key, json_body)
            # Key must NOT appear as a URL query param
            params = call_kwargs.get('params', {})
            self.assertNotIn(secret_key, str(params))
            # Key MUST appear in the x-goog-api-key header
            self.assertEqual(request_headers.get('x-goog-api-key'), secret_key)

    def test_ai_does_not_change_complaint_status(self):
        """
        The service must never update complaint.status.
        _sync_complaint_severity only writes severity_level, severity_score, updated_at.
        """
        from apps.complaints.ai.service import _sync_complaint_severity
        from apps.complaints.ai.schemas import SeverityResult

        result = SeverityResult(
            severity_level='high',
            severity_score=65.0,
            confidence=85.0,
            reason='Major pothole.',
        )
        with patch('apps.complaints.ai.service.connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            now = datetime.now(timezone.utc)
            _sync_complaint_severity('fake-uuid', result, now)

            sql = mock_cursor.execute.call_args[0][0]
            # Must NOT contain status in the UPDATE
            self.assertNotIn('status', sql.lower())
            # Must update severity fields
            self.assertIn('severity_level', sql)
            self.assertIn('severity_score', sql)


# ===========================================================================
# 6. Background Thread Execution Test
# ===========================================================================

class TestBackgroundThreadExecution(TestCase):
    """Tests for run_severity_assessment_in_background."""

    @patch('apps.complaints.ai.service.ComplaintSeverityService.assess_complaint')
    @patch('apps.complaints.ai.providers.gemini.GeminiSeverityProvider')
    def test_background_function_starts_thread(self, MockProvider, mock_assess):
        """run_severity_assessment_in_background launches a thread."""
        from apps.complaints.ai.service import run_severity_assessment_in_background
        import threading

        complaint_id = str(uuid.uuid4())

        with patch('apps.complaints.ai.service.connection'):
            run_severity_assessment_in_background(complaint_id)

        import time
        time.sleep(0.05)  # Give thread a moment to start

        # Thread was started (we can't reliably count active threads in test,
        # so just assert no exception was raised)
        # This test primarily verifies the function runs without error
