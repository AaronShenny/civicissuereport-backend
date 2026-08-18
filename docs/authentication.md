# Supabase ES256 Authentication

This document explains the authentication flow in the Civic Issue Report Django backend.

## Overview

The application relies completely on Supabase Auth for identity management and does not issue its own tokens. The Django backend uses a custom DRF authentication class (`core.authentication.supabase.SupabaseAuthentication`) to cryptographically verify JSON Web Tokens (JWTs) provided by clients.

## ES256 & JWKS Verification (Primary)

Live Supabase projects issue JWTs signed with Elliptic Curve Cryptography (`ES256`).

To verify these tokens securely:
1. The backend extracts the `Bearer` token from the `Authorization` header.
2. The unverified JWT header is inspected to determine the signature algorithm (`alg`) and Key ID (`kid`).
3. If `alg == "ES256"`, the backend fetches the public JSON Web Key Set (JWKS) directly from the Supabase project endpoint (e.g., `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`).
4. The backend constructs the EC public key using the JWK matching the `kid`.
5. The JWT signature is verified using `ES256` alongside `audience` and `issuer` claims.

### Key Caching

To prevent network overhead and rate limits:
- The JWKS is cached in process memory by `PyJWKClient`.
- The cache has a TTL configured by `SUPABASE_JWKS_CACHE_TTL` (default 3600 seconds).
- The cache automatically invalidates/refreshes if a token presents an unknown `kid`, allowing seamless key rotation by Supabase without restarting the Django service.

## HS256 Verification (Legacy/Fallback)

If a token is signed with `HS256`, the backend falls back to validating the token using the symmetric `SUPABASE_JWT_SECRET`.
This is retained strictly for backward compatibility with older configurations or local mock testing that may not provide a JWKS endpoint.

**Note:** If the explicit `SUPABASE_JWT_SECRET` is not set in the environment, the backend will aggressively reject any HS256 tokens.

## Audience & Issuer Validation

- **Audience**: Hardcoded to `"authenticated"`.
- **Issuer**: Explicitly validated against `SUPABASE_JWT_ISSUER` (derived securely from `SUPABASE_URL`). This prevents cross-project tokens from being falsely accepted.

## Failure Behavior

The backend adheres to a "fail-closed" model. If any of the following occur, a `401 Unauthorized` error is returned immediately:
- The `Authorization` header is missing or malformed.
- The token algorithm is not explicitly allowed (`HS256` or `ES256`).
- The token is expired (`exp`).
- The JWT signature is invalid.
- The `kid` is missing or cannot be matched against the live JWKS.
- The audience or issuer does not match.

No internal cryptography exceptions or cache states are ever exposed to the client.

## Environment Variables

- `SUPABASE_URL`: Required. Base URL of the Supabase project.
- `SUPABASE_JWKS_URL`: Optional. Derived from `SUPABASE_URL`.
- `SUPABASE_JWT_ISSUER`: Optional. Derived from `SUPABASE_URL`.
- `SUPABASE_JWKS_CACHE_TTL`: Optional. Time in seconds to cache the JWKS payload. Default 3600.
- `SUPABASE_JWT_SECRET`: Required ONLY for HS256 support.
