# Phase 9.1: Frontend Authentication & Infrastructure

This document outlines the foundational frontend authentication architecture built to interact with Supabase and the Django API.

## Frontend Auth Architecture
The frontend manages authentication state globally using a React Context provider (`AuthProvider.jsx`).
It relies entirely on `@supabase/supabase-js` to handle session management, JWT refresh cycles, and storage. The frontend does not implement custom JWT storage logic; it delegates token storage and rotation to the Supabase client.

## Supabase Client
A singleton Supabase client is initialized in `src/lib/supabase.js` using `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`. This client is the sole mechanism used for invoking Supabase Auth endpoints (like `signInWithPassword` and `signOut`).

## Session Lifecycle
1. **Restoration**: On initial load, the `AuthProvider` invokes `supabase.auth.getSession()` to restore an existing session synchronously.
2. **Listener**: It attaches `supabase.auth.onAuthStateChange` to react to login/logout/refresh events.
3. **Fetching Profile**: Upon receiving a valid session, the provider calls the Django backend to retrieve the user's role and profile.
4. **Logout**: Calling `signOut()` clears the Supabase session, resets the React Context state, and forces unauthenticated routes to redirect to `/login`.

## Django API Authentication & Bearer Token Flow
Django requires a valid Supabase ES256 JWT to authenticate requests.
1. `src/lib/api.js` exposes a centralized `fetch`-based HTTP client.
2. Before any API call, the client retrieves the current access token via `await supabase.auth.getSession()`.
3. It appends the `Authorization: Bearer <token>` header dynamically to all requests.

## Profile & Role Retrieval
Once Supabase authenticates the user, the `AuthProvider` reaches out to:
- `GET /api/v1/users/me/`
- `GET /api/v1/users/me/role/`

These endpoints return the authoritative Django profile and role, ensuring that the frontend never relies solely on JWT claims or manual metadata for authorization logic.

## ProtectedRoute
`ProtectedRoute.jsx` intercepts rendering for any authenticated view (wrapped inside `AppLayout` in `router.jsx`). 
- If `loading` is true, it displays a minimal loading screen (avoiding premature rendering).
- If no session exists, it immediately redirects the user to `/login`.
- Role-based authorization will be layered over this foundation in Phase 9.2.

## Environment Variables
Located in `frontend/.env`:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE_URL`

## Security Restrictions
- No `SUPABASE_SERVICE_ROLE_KEY` or `DATABASE_URL` is exposed.
- Authentication decisions respect the Django backend responses. `401 Unauthorized` HTTP responses are caught gracefully by the API client.
- Frontend role checks remain UX-only; Django continues to enforce true authorization.

## Testing Performed
- Validated via `npm run lint` and `npm run build` (success).
- Verified local `.env.example` existence.
- Verified missing secret variables in frontend logic.
