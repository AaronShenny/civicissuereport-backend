"""
tests/test_auth.py

Tests for the Supabase JWT authentication backend supporting both ES256 (JWKS) and HS256.
"""

import uuid
import jwt
import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import AuthenticationFailed
from core.authentication.supabase import SupabaseAuthentication
from cryptography.hazmat.primitives.asymmetric import ec
from jwt import PyJWKClientError

@pytest.fixture
def api_factory():
    return APIRequestFactory()

@pytest.fixture(scope="module")
def ec_keys():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key

def test_missing_auth_header(api_factory):
    request = api_factory.get('/')
    auth = SupabaseAuthentication()
    assert auth.authenticate(request) is None

def test_invalid_auth_header_format(api_factory):
    request = api_factory.get('/', HTTP_AUTHORIZATION='Token xyz')
    auth = SupabaseAuthentication()
    assert auth.authenticate(request) is None

def test_invalid_jwt_format(api_factory):
    request = api_factory.get('/', HTTP_AUTHORIZATION='Bearer invalid_token_format')
    auth = SupabaseAuthentication()
    with pytest.raises(AuthenticationFailed, match='Malformed token header'):
        auth.authenticate(request)

def test_unsupported_algorithm(api_factory, settings):
    # Encode with RS256 which is not supported
    import cryptography.hazmat.primitives.asymmetric.rsa as rsa
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode({'sub': '123', 'aud': 'authenticated'}, private_key, algorithm='RS256')
    request = api_factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
    auth = SupabaseAuthentication()
    with pytest.raises(AuthenticationFailed, match='Unsupported token algorithm: RS256'):
        auth.authenticate(request)

def test_es256_missing_kid(api_factory, ec_keys):
    private_key, _ = ec_keys
    token = jwt.encode({'sub': '123', 'aud': 'authenticated'}, private_key, algorithm='ES256')
    request = api_factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
    auth = SupabaseAuthentication()
    with pytest.raises(AuthenticationFailed, match='Missing kid in token header'):
        auth.authenticate(request)

@patch('core.authentication.supabase.get_jwk_client')
def test_es256_valid(mock_get_client, api_factory, settings, ec_keys):
    settings.SUPABASE_JWT_ISSUER = 'test-issuer'
    private_key, public_key = ec_keys
    user_uuid = uuid.uuid4()
    token = jwt.encode({'sub': str(user_uuid), 'aud': 'authenticated', 'iss': 'test-issuer'}, private_key, algorithm='ES256', headers={'kid': 'test-kid'})
    
    mock_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
    mock_get_client.return_value = mock_client

    request = api_factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
    auth = SupabaseAuthentication()
    
    mock_profile = MagicMock()
    mock_profile.id = user_uuid
    mock_profile.account_status = 'active'
    mock_profile.is_authenticated = True
    mock_profile.profile = mock_profile

    with patch.object(auth, '_load_profile', return_value=mock_profile):
        user, auth_token = auth.authenticate(request)
        assert user.id == user_uuid
        assert auth_token == token

@patch('core.authentication.supabase.get_jwk_client')
def test_es256_invalid_signature(mock_get_client, api_factory, settings, ec_keys):
    settings.SUPABASE_JWT_ISSUER = 'test-issuer'
    private_key, _ = ec_keys
    # Use a different key for verification
    wrong_private_key = ec.generate_private_key(ec.SECP256R1())
    wrong_public_key = wrong_private_key.public_key()
    
    token = jwt.encode({'sub': '123', 'aud': 'authenticated', 'iss': 'test-issuer'}, private_key, algorithm='ES256', headers={'kid': 'test-kid'})
    
    mock_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = wrong_public_key
    mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
    mock_get_client.return_value = mock_client

    request = api_factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
    auth = SupabaseAuthentication()
    with pytest.raises(AuthenticationFailed, match='Invalid token'):
        auth.authenticate(request)

@patch('core.authentication.supabase.get_jwk_client')
def test_es256_jwks_failure(mock_get_client, api_factory, ec_keys):
    private_key, _ = ec_keys
    token = jwt.encode({'sub': '123', 'aud': 'authenticated'}, private_key, algorithm='ES256', headers={'kid': 'test-kid'})
    
    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.side_effect = PyJWKClientError("Network error")
    mock_get_client.return_value = mock_client

    request = api_factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
    auth = SupabaseAuthentication()
    with pytest.raises(AuthenticationFailed, match='Failed to verify signing key from JWKS'):
        auth.authenticate(request)

def test_hs256_valid(api_factory, settings):
    settings.SUPABASE_JWT_SECRET = 'super-secret'
    settings.SUPABASE_JWT_ISSUER = 'test-issuer'
    user_uuid = uuid.uuid4()
    token = jwt.encode({'sub': str(user_uuid), 'aud': 'authenticated', 'iss': 'test-issuer'}, 'super-secret', algorithm='HS256')
    request = api_factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
    
    mock_profile = MagicMock()
    mock_profile.id = user_uuid
    mock_profile.account_status = 'active'
    mock_profile.is_authenticated = True
    mock_profile.profile = mock_profile

    auth = SupabaseAuthentication()
    with patch.object(auth, '_load_profile', return_value=mock_profile):
        user, auth_token = auth.authenticate(request)
        assert user.id == user_uuid
        assert auth_token == token

def test_hs256_missing_secret(api_factory, settings):
    settings.SUPABASE_JWT_SECRET = None
    token = jwt.encode({'sub': '123', 'aud': 'authenticated'}, 'any', algorithm='HS256')
    request = api_factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
    auth = SupabaseAuthentication()
    with pytest.raises(AuthenticationFailed, match='SUPABASE_JWT_SECRET is not configured'):
        auth.authenticate(request)
