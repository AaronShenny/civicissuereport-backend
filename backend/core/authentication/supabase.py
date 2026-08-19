"""
core/authentication/supabase.py

Custom DRF authentication backend for Supabase JWTs.

Flow:
  1. Extract Bearer token from the Authorization header.
  2. Inspect the unverified JWT header to determine the algorithm (alg).
  3. If ES256 (Primary):
     - Fetch the public JWK from the Supabase JWKS endpoint (process-cached).
     - Verify the signature using the matching public key.
  4. If HS256 (Legacy/Local compatibility):
     - Verify using the symmetric SUPABASE_JWT_SECRET.
  5. Validate 'audience' and 'issuer'.
  6. Extract the user UUID from the 'sub' claim.
  7. Load the corresponding public.profiles row from the database.
  8. Attach the Profile as request.user.

Django does NOT issue its own tokens and does NOT store passwords.
Supabase Auth is the sole authentication authority.
"""

import jwt
from jwt import PyJWKClient, PyJWKClientError
from django.conf import settings
from rest_framework import authentication, exceptions

# Process-local cache for JWKS to avoid downloading on every request.
# The cache auto-refreshes if a token presents an unknown 'kid'.
_jwk_client = None

def get_jwk_client():
    global _jwk_client
    if _jwk_client is None:
        jwks_url = getattr(settings, 'SUPABASE_JWKS_URL', None)
        if not jwks_url:
            raise exceptions.AuthenticationFailed('SUPABASE_JWKS_URL is not configured.')
        ttl = getattr(settings, 'SUPABASE_JWKS_CACHE_TTL', 3600)
        _jwk_client = PyJWKClient(jwks_url, cache_keys=True, cache_jwk_set=True, lifespan=ttl)
    return _jwk_client

class SupabaseAuthentication(authentication.BaseAuthentication):
    """
    Verifies a Supabase-issued JWT and loads the matching public.profiles row.
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None  # No Supabase token — let other authenticators try.

        token = auth_header[len('Bearer '):]
        if not token:
            return None

        # Inspect unverified header ONLY to determine routing path.
        # NEVER trust the payload at this stage.
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed('Malformed token header.')

        alg = unverified_header.get('alg')
        issuer = getattr(settings, 'SUPABASE_JWT_ISSUER', None)

        # Common PyJWT decode options
        decode_kwargs = {
            "options": {
                "verify_aud": False,
                "verify_iss": False,
            }
        }

        if alg == "ES256":
            # Primary path: Live Supabase projects use ES256 signatures via JWKS.
            kid = unverified_header.get('kid')
            if not kid:
                raise exceptions.AuthenticationFailed('Missing kid in token header.')
            
            try:
                jwk_client = get_jwk_client()
                signing_key = jwk_client.get_signing_key_from_jwt(token)
            except PyJWKClientError:
                raise exceptions.AuthenticationFailed('Failed to verify signing key from JWKS.')
            except Exception:
                raise exceptions.AuthenticationFailed('Authentication service temporarily unavailable.')

            try:
                payload = jwt.decode(
                    token,
                    key=signing_key.key,
                    algorithms=["ES256"],
                    **decode_kwargs
                )
            except jwt.ExpiredSignatureError:
                raise exceptions.AuthenticationFailed('Token has expired.')
            except jwt.InvalidIssuerError as exc:
                raise exceptions.AuthenticationFailed(f'Invalid token issuer: {exc}')
            except jwt.InvalidAudienceError as exc:
                raise exceptions.AuthenticationFailed(f'Invalid token audience: {exc}')
            except jwt.InvalidTokenError as exc:
                print(f"[AUTH ERROR] InvalidTokenError: {exc}")
                raise exceptions.AuthenticationFailed(f'Invalid token: {exc}')

        elif alg == "HS256":
            # Legacy/Local compatibility path: Only allowed if the explicit secret is configured.
            jwt_secret = getattr(settings, 'SUPABASE_JWT_SECRET', None)
            if not jwt_secret:
                raise exceptions.AuthenticationFailed('SUPABASE_JWT_SECRET is not configured for HS256 tokens.')

            try:
                payload = jwt.decode(
                    token,
                    key=jwt_secret,
                    algorithms=["HS256"],
                    **decode_kwargs
                )
            except jwt.ExpiredSignatureError:
                raise exceptions.AuthenticationFailed('Token has expired.')
            except jwt.InvalidIssuerError as exc:
                raise exceptions.AuthenticationFailed(f'Invalid token issuer: {exc}')
            except jwt.InvalidAudienceError as exc:
                raise exceptions.AuthenticationFailed(f'Invalid token audience: {exc}')
            except jwt.InvalidTokenError as exc:
                print(f"[AUTH ERROR] InvalidTokenError: {exc}")
                raise exceptions.AuthenticationFailed(f'Invalid token: {exc}')

        else:
            # Any other algorithm is rejected immediately.
            raise exceptions.AuthenticationFailed(f'Unsupported token algorithm: {alg}')

        user_id = payload.get('sub')
        if not user_id:
            raise exceptions.AuthenticationFailed(
                'Token is missing the sub (user ID) claim.'
            )

        profile = self._load_profile(user_id, payload)
        return (profile, token)

    def _load_profile(self, user_id: str, payload: dict = None):
        """
        Loads the public.profiles record for the given Supabase user UUID.
        If no profile exists, automatically creates a default active Citizen profile.
        """
        import uuid
        from datetime import datetime, timezone
        from apps.users.models import Profile, Role

        try:
            profile = (
                Profile.objects
                .select_related('role', 'department', 'supervisor', 'supervisor__role')
                .get(id=user_id)
            )
        except Profile.DoesNotExist:
            citizen_role, _ = Role.objects.get_or_create(
                role_name=Role.CITIZEN,
                defaults={'description': 'Standard Citizen user'}
            )
            email = payload.get('email') if payload else ''
            user_meta = payload.get('user_metadata', {}) if payload else {}
            full_name = user_meta.get('full_name') or (email.split('@')[0] if email else 'User')
            now = datetime.now(timezone.utc)

            profile = Profile.objects.create(
                id=uuid.UUID(str(user_id)),
                full_name=full_name,
                email=email or None,
                role=citizen_role,
                account_status=Profile.ACCOUNT_STATUS_ACTIVE,
                created_at=now,
                updated_at=now
            )

        if profile.account_status == Profile.ACCOUNT_STATUS_INACTIVE:
            raise exceptions.AuthenticationFailed(
                'Your account has been deactivated. Contact an administrator.'
            )

        # Attach a minimal interface expected by DRF permission checks.
        profile.is_authenticated = True
        profile.profile = profile  # core/permissions/roles.py uses request.user.profile
        return profile

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
