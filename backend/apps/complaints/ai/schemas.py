"""
apps/complaints/ai/schemas.py

Data classes and validation for AI severity assessment results.

Design:
    The AI model returns a raw JSON string. This module provides:
    - SeverityResult: typed, validated dataclass representing a clean result.
    - parse_and_validate_ai_response: strict validator that rejects any
      response that does not conform to the expected schema.

Validation rules (enforced server-side, never trusting AI blindly):
    - severity_level must be one of: low, medium, high, critical
      (matching the PostgreSQL severity_level_type enum in database_schema.md).
    - severity_score must be a numeric value in [0, 100].
    - confidence must be a numeric value in [0, 100].
    - reason must be a non-empty string.

Any deviation from these rules raises SeverityValidationError — the AI
response is rejected and the complaint is left unchanged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

# The four valid severity levels as defined by the schema enum severity_level_type.
VALID_SEVERITY_LEVELS = {'low', 'medium', 'high', 'critical'}


class SeverityValidationError(Exception):
    """
    Raised when the AI response fails schema or value validation.
    The complaint workflow catches this and logs the failure.
    """
    pass


@dataclass(frozen=True)
class SeverityResult:
    """
    A fully validated severity assessment result from an AI provider.

    All fields have been checked for type, range, and enum validity
    before this object is constructed.

    Fields:
        severity_level: One of 'low', 'medium', 'high', 'critical'.
        severity_score: Float in [0, 100].
        confidence:     Float in [0, 100].  Indicates model certainty.
        reason:         Non-empty string. Brief evidence-based explanation.
    """
    severity_level: str
    severity_score: float
    confidence: float
    reason: str


def parse_and_validate_ai_response(raw_response: str) -> SeverityResult:
    """
    Parse and strictly validate the raw JSON string returned by an AI provider.

    Raises SeverityValidationError for any of the following:
        - Malformed JSON (not parseable)
        - Missing required fields (severity_level, severity_score, confidence, reason)
        - severity_level not in {low, medium, high, critical}
        - severity_score outside [0, 100]
        - confidence outside [0, 100]
        - reason is empty or whitespace-only

    Returns:
        SeverityResult — a validated, immutable result object.
    """
    if not raw_response or not raw_response.strip():
        raise SeverityValidationError('AI returned an empty response.')

    # Strip potential markdown code fences that models sometimes add
    stripped = raw_response.strip()
    if stripped.startswith('```'):
        lines = stripped.splitlines()
        # Remove first and last fence lines
        stripped = '\n'.join(
            line for line in lines
            if not line.strip().startswith('```')
        )

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise SeverityValidationError(
            f'AI response is not valid JSON: {exc}. '
            f'Raw response (first 200 chars): {raw_response[:200]!r}'
        )

    if not isinstance(data, dict):
        raise SeverityValidationError(
            f'AI response must be a JSON object, got {type(data).__name__}.'
        )

    # --- Required field presence ---
    required_fields = {'severity_level', 'severity_score', 'confidence', 'reason'}
    missing = required_fields - data.keys()
    if missing:
        raise SeverityValidationError(
            f'AI response missing required fields: {sorted(missing)}.'
        )

    # --- severity_level validation ---
    severity_level = data['severity_level']
    if not isinstance(severity_level, str):
        raise SeverityValidationError(
            f'severity_level must be a string, got {type(severity_level).__name__}.'
        )
    severity_level = severity_level.strip().lower()
    if severity_level not in VALID_SEVERITY_LEVELS:
        raise SeverityValidationError(
            f'Invalid severity_level "{severity_level}". '
            f'Must be one of: {sorted(VALID_SEVERITY_LEVELS)}.'
        )

    # --- severity_score validation ---
    try:
        severity_score = float(data['severity_score'])
    except (TypeError, ValueError):
        raise SeverityValidationError(
            f'severity_score must be numeric, got {data["severity_score"]!r}.'
        )
    if not (0.0 <= severity_score <= 100.0):
        raise SeverityValidationError(
            f'severity_score must be in [0, 100], got {severity_score}.'
        )

    # --- confidence validation ---
    try:
        confidence = float(data['confidence'])
    except (TypeError, ValueError):
        raise SeverityValidationError(
            f'confidence must be numeric, got {data["confidence"]!r}.'
        )
    if not (0.0 <= confidence <= 100.0):
        raise SeverityValidationError(
            f'confidence must be in [0, 100], got {confidence}.'
        )

    # --- reason validation ---
    reason = data.get('reason', '')
    if not isinstance(reason, str) or not reason.strip():
        raise SeverityValidationError(
            'reason must be a non-empty string.'
        )

    return SeverityResult(
        severity_level=severity_level,
        severity_score=round(severity_score, 2),
        confidence=round(confidence, 2),
        reason=reason.strip(),
    )
