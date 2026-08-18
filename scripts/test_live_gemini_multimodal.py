"""
scripts/test_live_gemini_multimodal.py

Manual live integration test for Phase 8: Real Image + Text (Multimodal).
Calls the real Gemini API using the production GeminiSeverityProvider.

Usage:
    python scripts/test_live_gemini_multimodal.py "path/to/image.jpg"

Safety & Constraints:
- Loads GEMINI_API_KEY from environment / .env.
- Does NOT mock httpx or Gemini.
- Does NOT write to Supabase or database.
- Never prints GEMINI_API_KEY.
- Exits with code 0 on success, code 1 on failure.
"""

import os
import sys
import mimetypes
from pathlib import Path

# Set up project root and backend path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / 'backend'

sys.path.insert(0, str(BACKEND_DIR))

# Initialize Django environment to load settings and environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

try:
    from dotenv import load_dotenv
    # Load .env from project root and backend directory if present
    load_dotenv(REPO_ROOT / '.env')
    load_dotenv(BACKEND_DIR / '.env')
except ImportError:
    pass

import django
django.setup()

from django.conf import settings
from apps.complaints.ai.providers.gemini import GeminiSeverityProvider
from apps.complaints.ai.interfaces import SeverityProviderError
from apps.complaints.ai.schemas import VALID_SEVERITY_LEVELS

SUPPORTED_IMAGE_MIMES = {
    'image/jpeg', 'image/png', 'image/webp', 'image/gif',
}


def run_live_multimodal_test(image_path_str: str) -> int:
    print("=" * 60)
    print("LIVE MULTIMODAL TEST: Phase 8 AI Severity Assessment (Image + Text)")
    print("=" * 60)

    # 1. Check GEMINI_API_KEY
    api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is not set in environment or .env file.")
        print("Please configure GEMINI_API_KEY in .env before running this test.")
        return 1

    # 2. Check AI_GEMINI_MODEL
    model_name = getattr(settings, 'AI_GEMINI_MODEL', None) or os.environ.get('AI_GEMINI_MODEL', 'gemini-3.6-flash')
    print(f"Configured Model : {model_name}")

    # 3. Verify model is gemini-3.6-flash
    EXPECTED_MODEL = 'gemini-3.6-flash'
    if model_name != EXPECTED_MODEL:
        print(f"[ERROR] Expected model '{EXPECTED_MODEL}', but got '{model_name}'.")
        return 1

    # 4. Validate and load image file
    image_path = Path(image_path_str).resolve()
    if not image_path.exists() or not image_path.is_file():
        print(f"[ERROR] Image file does not exist: {image_path}")
        return 1

    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type or mime_type not in SUPPORTED_IMAGE_MIMES:
        # Fallback heuristic based on extension
        ext = image_path.suffix.lower()
        ext_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif',
        }
        mime_type = ext_map.get(ext)

    if not mime_type or mime_type not in SUPPORTED_IMAGE_MIMES:
        print(f"[ERROR] Unsupported or unrecognized image MIME type: {mime_type}")
        print(f"Supported MIME types: {sorted(SUPPORTED_IMAGE_MIMES)}")
        return 1

    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
    except Exception as exc:
        print(f"[ERROR] Failed to read image file: {exc}")
        return 1

    if not image_bytes:
        print("[ERROR] Image file is empty (0 bytes).")
        return 1

    file_size_kb = len(image_bytes) / 1024.0
    print(f"Image File       : {image_path.name} ({file_size_kb:.1f} KB)")
    print(f"Image MIME Type  : {mime_type}")

    # 5. Civic complaint text
    complaint_description = (
        "There is a large pothole approximately 1 meter wide in the middle of a busy road. "
        "Vehicles are swerving into the opposite lane to avoid it. "
        "The pothole becomes difficult to see at night and several vehicles have already nearly lost control."
    )

    print("\nComplaint Description:")
    print(f'"{complaint_description}"\n')

    # 6. Initialize production provider
    try:
        provider = GeminiSeverityProvider()
    except Exception as exc:
        print(f"[ERROR] Failed to initialize GeminiSeverityProvider: {exc}")
        return 1

    image_data = [{'mime_type': mime_type, 'data': image_bytes}]

    # 7. Call live Gemini API with multimodal input (text + image)
    print("Sending live multimodal assessment request to Gemini API...")
    try:
        result = provider.assess(
            description=complaint_description,
            image_data=image_data,
        )
    except SeverityProviderError as exc:
        print(f"[ERROR] Gemini provider failed during multimodal assessment: {exc}")
        return 1
    except Exception as exc:
        print(f"[ERROR] Unexpected exception during multimodal assessment: {exc}")
        return 1

    # 8. Print and validate results
    print("\n" + "-" * 60)
    print("MULTIMODAL ASSESSMENT RESULT")
    print("-" * 60)
    print("HTTP / API Call : SUCCESS (HTTP 200)")
    print(f"Model Used      : {model_name}")
    print(f"Image MIME Type : {mime_type}")
    print(f"Severity Level  : {result.severity_level}")
    print(f"Severity Score  : {result.severity_score}")
    print(f"Confidence      : {result.confidence}%")
    print(f"Reason          : {result.reason}")
    print("-" * 60)

    errors = []

    if result.severity_level not in VALID_SEVERITY_LEVELS:
        errors.append(
            f"Invalid severity_level '{result.severity_level}'. Must be one of: {sorted(VALID_SEVERITY_LEVELS)}"
        )

    if not (0.0 <= result.severity_score <= 100.0):
        errors.append(f"severity_score {result.severity_score} is out of range [0, 100].")

    if not (0.0 <= result.confidence <= 100.0):
        errors.append(f"confidence {result.confidence} is out of range [0, 100].")

    if not result.reason or not result.reason.strip():
        errors.append("reason must be a non-empty string.")

    if errors:
        print("\n[VALIDATION FAILED]")
        for err in errors:
            print(f" - {err}")
        return 1

    print("\n[SUCCESS] Live multimodal Gemini severity assessment completed and validated successfully!")
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("Usage: python scripts/test_live_gemini_multimodal.py <path_to_image>")
        print("Example: python scripts/test_live_gemini_multimodal.py C:\\path\\to\\pothole.jpg")
        sys.exit(1)

    exit_code = run_live_multimodal_test(sys.argv[1])
    sys.exit(exit_code)
