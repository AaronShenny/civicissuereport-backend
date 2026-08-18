"""
apps/complaints/ai/providers/gemini.py

GeminiSeverityProvider — Gemini multimodal AI provider for severity assessment.

Model: gemini-3.6-flash  (GA/stable as of July 21, 2026)

API Compatibility Notes (gemini-3.6-flash):
    1. System instructions are passed via the top-level 'systemInstruction' field.
    2. User prompt and inline images are passed in 'contents' under role 'user'.
    3. Inline images use camelCase 'inlineData' with 'mimeType' and 'data'.
    4. Structured JSON output is enabled via generationConfig.responseMimeType = 'application/json'.
    5. Sampling parameters (temperature, top_P, top_K) are unsupported by the Gemini 3.x Flash series and are omitted.
    6. Authentication uses the 'x-goog-api-key' HTTP header.
    7. Request timeout is set to 60.0s to accommodate reasoning/thinking tokens.

Security:
    - The GEMINI_API_KEY is read from Django settings (environment variable only).
    - It is passed in the x-goog-api-key HTTP header — NEVER as a URL query
      parameter, never in the request body, and never logged.
    - The provider does NOT write to the database directly.

Supported input:
    - description only (image_data=[])
    - image only (description='')
    - description + image

Image handling:
    - Only images are passed to Gemini (file_type='photo' attachments).
    - Video and document attachments are NOT passed (not supported for inline).
    - Image bytes are base64-encoded and sent as inlineData.
    - Images are NOT stored in PostgreSQL.
"""

from __future__ import annotations

import base64
import json
import logging

import httpx
from django.conf import settings

from apps.complaints.ai.interfaces import SeverityProvider, SeverityProviderError
from apps.complaints.ai.schemas import SeverityResult, parse_and_validate_ai_response

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# The model identifier. Override via AI_GEMINI_MODEL in environment/settings.
# Default: gemini-3.6-flash — GA/stable model released July 21, 2026.
_DEFAULT_MODEL = 'gemini-3.6-flash'

# API endpoint base.
_GEMINI_API_BASE = 'https://generativelanguage.googleapis.com/v1beta/models'

# Request timeout in seconds (accommodates reasoning/thinking tokens).
_REQUEST_TIMEOUT = 60.0

# ---------------------------------------------------------------------------
# System prompt for severity assessment
# ---------------------------------------------------------------------------

SEVERITY_SYSTEM_PROMPT = """\
You are a civic infrastructure assessment AI. Your role is to evaluate the \
severity of a public complaint based on the provided description and any \
attached images.

Assess severity using these criteria:
- Public safety risk (immediate danger to people)
- Physical extent of the damage or problem
- Level of obstruction or disruption to public access
- Urgency (how quickly action is required)
- Potential for harm if left unaddressed
- Visible damage severity
- Impact on traffic or public movement

Severity Rubric (application-defined guidelines — not authoritative business rules):
  LOW     (severity_score 0-25):  Minor inconvenience. No immediate danger. \
Cosmetic or very small-scale issue.
  MEDIUM  (severity_score 26-50): Moderate disruption. Causes inconvenience \
but not life-threatening.
  HIGH    (severity_score 51-75): Major disruption or significant safety risk. \
Requires prompt action.
  CRITICAL (severity_score 76-100): Immediate life-threatening hazard or \
severe structural failure. Requires emergency response.

Instructions:
- Base your assessment ONLY on evidence present in the description and images.
- Do NOT invent or assume facts not present in the provided input.
- If evidence is insufficient or ambiguous, assign a LOWER confidence score.
- You must output ONLY a single valid JSON object. No markdown, no explanation \
text outside the JSON.

Required JSON schema (output exactly this structure, nothing else):
{"severity_level": "low|medium|high|critical", "severity_score": <float 0-100>, \
"confidence": <float 0-100>, "reason": "<brief evidence-based explanation>"}
"""


# ---------------------------------------------------------------------------
# GeminiSeverityProvider
# ---------------------------------------------------------------------------

class GeminiSeverityProvider(SeverityProvider):
    """
    Gemini multimodal severity assessment provider.

    Uses the Google Generative Language REST API directly via httpx
    (no additional SDK dependency required).

    The provider is stateless — a new instance may be created per request
    or reused as a singleton.
    """

    def __init__(self):
        self._api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self._model = getattr(settings, 'AI_GEMINI_MODEL', _DEFAULT_MODEL)

    def _get_api_key(self) -> str:
        if not self._api_key:
            raise SeverityProviderError(
                'GEMINI_API_KEY is not configured. '
                'Set the GEMINI_API_KEY environment variable.'
            )
        return self._api_key

    def _build_url(self) -> str:
        return f'{_GEMINI_API_BASE}/{self._model}:generateContent'

    def _build_request_body(
        self,
        description: str,
        image_data: list[dict],
    ) -> dict:
        """
        Constructs the Gemini API request body.

        Supports:
            - Text only (image_data=[])
            - Image only (description='')
            - Text + image (both provided)

        Only 'photo' MIME types are passed; other file types are silently skipped.
        """
        user_parts = []

        # Complaint description
        if description and description.strip():
            user_parts.append({'text': f'Complaint description: {description.strip()}'})
        else:
            user_parts.append({'text': 'No description provided. Assess based on attached images only.'})

        # Images — base64-encoded inline data
        SUPPORTED_IMAGE_MIMES = {
            'image/jpeg', 'image/png', 'image/webp', 'image/gif',
        }
        for img in image_data:
            mime = img.get('mime_type', '')
            raw_bytes = img.get('data', b'')
            if mime not in SUPPORTED_IMAGE_MIMES:
                logger.debug(
                    'Skipping unsupported MIME type for Gemini inline image: %s', mime
                )
                continue
            if not raw_bytes:
                continue
            encoded = base64.b64encode(raw_bytes).decode('utf-8')
            user_parts.append({
                'inlineData': {
                    'mimeType': mime,
                    'data': encoded,
                }
            })

        return {
            'systemInstruction': {
                'parts': [{'text': SEVERITY_SYSTEM_PROMPT}]
            },
            'contents': [
                {
                    'role': 'user',
                    'parts': user_parts,
                }
            ],
            'generationConfig': {
                'responseMimeType': 'application/json',
            },
        }

    def assess(
        self,
        description: str,
        image_data: list[dict],
    ) -> SeverityResult:
        """
        Call the Gemini API and return a validated SeverityResult.

        Raises:
            SeverityProviderError: On API key missing, network failure, timeout,
                                   HTTP error, or invalid/unvalidatable response.
        """
        api_key = self._get_api_key()
        url = self._build_url()
        body = self._build_request_body(description, image_data)

        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': api_key,
        }

        try:
            response = httpx.post(
                url,
                json=body,
                headers=headers,
                timeout=_REQUEST_TIMEOUT,
            )
        except httpx.TimeoutException as exc:
            raise SeverityProviderError(
                f'Gemini API request timed out after {_REQUEST_TIMEOUT}s: {exc}'
            )
        except httpx.RequestError as exc:
            raise SeverityProviderError(
                f'Gemini API network error: {exc}'
            )

        if response.status_code != 200:
            raise SeverityProviderError(
                f'Gemini API returned HTTP {response.status_code}. '
                f'Body: {response.text[:300]}'
            )

        try:
            resp_json = response.json()
        except Exception as exc:
            raise SeverityProviderError(
                f'Could not parse Gemini API response as JSON: {exc}'
            )

        # Extract the text content from the Gemini response structure
        try:
            raw_text = (
                resp_json['candidates'][0]['content']['parts'][0]['text']
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise SeverityProviderError(
                f'Unexpected Gemini response structure: {exc}. '
                f'Response: {json.dumps(resp_json)[:300]}'
            )

        # Validate and return structured result
        from apps.complaints.ai.schemas import SeverityValidationError
        try:
            return parse_and_validate_ai_response(raw_text)
        except SeverityValidationError as exc:
            raise SeverityProviderError(
                f'Gemini response failed validation: {exc}'
            )
