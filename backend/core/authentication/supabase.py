"""
core/authentication/supabase.py

Custom DRF authentication backend for Supabase JWTs.

Flow:
  1. Extract Bearer token from the Authorization header.
  2. Verify the JWT signature using SUPABASE_JWT_SECRET.
  3. Extract the user UUID from the 'sub' claim.
  4. Load the corresponding public.profiles row from the database.
  5. Attach the Profile as request.user so that downstream permissions
     can read role, department, and supervisor without additional DB hits.

Django does NOT issue its own tokens and does NOT store passwords.
Supabase Auth is the sole authentication authority.
"""

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions


class SupabaseAuthentication(authentication.BaseAuthentication):
    """
    Verifies a Supabase-issued JWT and loads the matching public.profiles row.

    On success, request.user is a Profile instance (not a Django auth User).
    On failure, raises AuthenticationFailed.
    If no Authorization header is present, returns None (unauthenticated —
    DRF then applies the DEFAULT_PERMISSION_CLASSES check).
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None  # No Supabase token — let other authenticators try.

        token = auth_header[len('Bearer '):]
        if not token:
            return None

        jwt_secret = getattr(settings, 'SUPABASE_JWT_SECRET', None)
        if not jwt_secret:
            raise exceptions.AuthenticationFailed(
                'SUPABASE_JWT_SECRET is not configured on this server.'
            )

        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=['HS256'],
                audience='authenticated',
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired.')
        except jwt.InvalidAudienceError:
            raise exceptions.AuthenticationFailed('Invalid token audience.')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token.')

        user_id = payload.get('sub')
        if not user_id:
            raise exceptions.AuthenticationFailed(
                'Token is missing the sub (user ID) claim.'
            )

        profile = self._load_profile(user_id)
        return (profile, token)

    def _load_profile(self, user_id: str):
        """
        Loads the public.profiles record for the given Supabase user UUID.

        Raises AuthenticationFailed when:
        - No profile exists (user registered in Supabase but profile trigger
          has not fired yet, or profile was manually deleted).
        - The profile's account_status is not 'active'.
        """
        # Import here to avoid circular import at module load time.
        from apps.users.models import Profile

        try:
            profile = (
                Profile.objects
                .select_related('role', 'department', 'supervisor', 'supervisor__role')
                .get(id=user_id)
            )
        except Profile.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                'No profile found for this user. '
                'Ensure the Supabase profile trigger has fired.'
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
