import jwt
from jwt import PyJWKClient

# This is the exact kid from the JWKS response we got
headers = {
    "alg": "ES256",
    "kid": "55c7cdf5-9fbd-46d7-a644-bcedc4af452a"
}

# Create a dummy token using another key, we just want to test if PyJWKClient can FETCH the signing key without throwing Exception
import os
import binascii
dummy_secret = binascii.hexlify(os.urandom(32)).decode()
# Let's just create the JWT string manually.
# Note: we encoded with HS256 but added headers manually to trick it. Actually jwt.encode might override the alg.
# Let's just create the JWT string manually.
import base64
import json
def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

header_b64 = b64url(json.dumps(headers).encode('utf-8'))
payload_b64 = b64url(json.dumps({"sub": "test"}).encode('utf-8'))
dummy_token = f"{header_b64}.{payload_b64}.dummy_signature"

jwks_url = "https://eucpbycjwfbaxzutwpoe.supabase.co/auth/v1/.well-known/jwks.json"

try:
    jwk_client = PyJWKClient(jwks_url, cache_keys=True, cache_jwk_set=True, lifespan=3600)
    print("Fetching key from JWKS...")
    key = jwk_client.get_signing_key_from_jwt(dummy_token)
    print("SUCCESS, Key found:", key)
except Exception as e:
    import traceback
    traceback.print_exc()
    print("EXCEPTION CAUGHT:", type(e))
