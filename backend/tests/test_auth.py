"""
tests/test_auth.py

Tests for the Supabase JWT authentication backend.
Updated for Phase 2: SupabaseAuthentication now loads a real Profile from DB,
so the valid-JWT test mocks the DB lookup.
"""

import uuid
import jwt
import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import AuthenticationFailed
from core.authentication.supabase import SupabaseAuthentication


@pytest.fixture
def api_factory():
    return APIRequestFactory()


def test_missing_auth_header(api_factory):
    """No Authorization header → authenticator returns None (pass-through)."""
    request = api_factory.get('/')
    auth = SupabaseAuthentication()
    assert auth.authenticate(request) is None


def test_invalid_auth_header_format(api_factory):
    """Authorization header without 'Bearer ' prefix → returns None."""
    request = api_factory.get('/', HTTP_AUTHORIZATION='Token xyz')
    auth = SupabaseAuthentication()
    assert auth.authenticate(request) is None


def test_invalid_jwt(api_factory, settings):
    """Completely invalid token string → raises AuthenticationFailed."""
    settings.SUPABASE_JWT_SECRET = 'secret'
    request = api_factory.get('/', HTTP_AUTHORIZATION='Bearer invalid_token')
    auth = SupabaseAuthentication()
    with pytest.raises(AuthenticationFailed, match='Invalid token'):
        auth.authenticate(request)


def test_expired_jwt(api_factory, settings):
    """Expired JWT → raises AuthenticationFailed with expiry message."""
    import time
    settings.SUPABASE_JWT_SECRET = 'super-secret'
    # iat in the far past, exp already elapsed
    token = jwt.encode(
        {'sub': str(uuid.uuid4()), 'aud': 'authenticated', 'exp': 1000000},
        'super-secret',
        algorithm='HS256',
    )
    request = api_factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
    auth = SupabaseAuthentication()
    with pytest.raises(AuthenticationFailed, match='expired'):
        auth.authenticate(request)


def test_valid_jwt_loads_profile(api_factory, settings):
    """
    Valid JWT with a proper UUID sub → authentication succeeds.
    The DB Profile lookup is mocked so no database is required.
    """
    settings.SUPABASE_JWT_SECRET = 'super-secret'
    user_uuid = uuid.uuid4()
    token = jwt.encode(
        {'sub': str(user_uuid), 'aud': 'authenticated'},
        'super-secret',
        algorithm='HS256',
    )
    request = api_factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')

    mock_profile = MagicMock()
    mock_profile.id = user_uuid
    mock_profile.account_status = 'active'
    mock_profile.is_authenticated = True
    mock_profile.profile = mock_profile

    auth = SupabaseAuthentication()
    with patch.object(auth, '_load_profile', return_value=mock_profile) as mock_load:
        user, auth_token = auth.authenticate(request)
        mock_load.assert_called_once_with(str(user_uuid))
        assert user.id == user_uuid
        assert auth_token == token


def test_missing_jwt_secret(api_factory, settings):
    """No SUPABASE_JWT_SECRET configured → raises AuthenticationFailed."""
    settings.SUPABASE_JWT_SECRET = None
    token = jwt.encode({'sub': str(uuid.uuid4()), 'aud': 'authenticated'}, 'any', algorithm='HS256')
    request = api_factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
    auth = SupabaseAuthentication()
    with pytest.raises(AuthenticationFailed, match='SUPABASE_JWT_SECRET'):
        auth.authenticate(request)
