"""
apps/complaints/ai/interfaces.py

Abstract base class (ABC) for severity classification providers.

The SeverityClassifier interface decouples the complaint workflow from
any specific AI provider. The current implementation uses Gemini
(GeminiSeverityProvider), but any model can be swapped in by implementing
this interface — for example, a local/self-hosted model in a future phase.

Usage:
    provider = GeminiSeverityProvider()
    classifier = SeverityClassifier  # not instantiated; providers subclass it
    result = provider.assess(text="...", image_data=[...])
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from apps.complaints.ai.schemas import SeverityResult


class SeverityProvider(ABC):
    """
    Provider abstraction for complaint severity assessment.

    Concrete implementations are responsible for:
    - Accepting complaint text and optional image data.
    - Calling the underlying AI model.
    - Returning a validated SeverityResult.
    - Raising SeverityProviderError on irrecoverable failures.

    Providers must NOT:
    - Write directly to the database.
    - Modify complaint status or assignment.
    - Expose API keys to callers.
    """

    @abstractmethod
    def assess(
        self,
        description: str,
        image_data: list[dict],
    ) -> SeverityResult:
        """
        Assess the severity of a complaint.

        Args:
            description: Raw complaint description text. May be empty string
                         if no description is available (image-only assessment).
            image_data:  List of dicts with keys:
                           - 'mime_type': str  (e.g. 'image/jpeg')
                           - 'data': bytes      (raw file bytes)
                         May be empty list (text-only assessment).

        Returns:
            A validated SeverityResult instance.

        Raises:
            SeverityProviderError: On API failure, timeout, or invalid response.
        """
        raise NotImplementedError


class SeverityProviderError(Exception):
    """
    Raised by SeverityProvider implementations when the AI assessment
    cannot be completed or when the model returns an invalid response.

    The complaint workflow catches this and logs the failure without
    corrupting the complaint record.
    """
    pass
