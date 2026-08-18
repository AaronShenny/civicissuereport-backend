# Phase 9: Frontend Architecture & Integration Plan

This document provides the definitive architectural blueprint for transforming the transitional frontend into the Civic Issue Reporting System. It maps the validated backend REST APIs, authentication flows, roles, and status lifecycles to their frontend equivalents.

---

## 1. Current Frontend Architecture Audit

- **Framework**: React 19, Vite, react-router-dom v7.
- **Styling**: Vanilla CSS, relying heavily on a tokenized design system (`index.css`, `App.css`).
- **State**: Currently entirely mocked using hardcoded files (e.g. `MOCK_ASSETS`) and localized `useState`.
- **Domain**: Currently implements a legacy "Asset Management" system (AssetFlow).
- **Authentication**: Non-existent (mock timeouts).
- **Conclusion**: The design tokens and component structure are valuable, but the domain logic, routing, and data layer must be completely replaced.

---

## 2. Backend API Audit (Verified)

The backend is fully implemented and relies on Supabase for auth and PostgreSQL for data, wrapped in a Django REST API.
Endpoints require a Supabase JWT (Bearer Token) and use RBAC to determine accessibility.

**Key Endpoints Discovered:**
- **Users**:
  - `GET /api/v1/users/me/`
  - `GET /api/v1/users/me/role/`
  - `GET /api/v1/users/me/department/`
  - `GET /api/v1/users/department-members/`
- **Complaints (Citizen)**:
  - `POST /api/v1/complaints/`
  - `GET /api/v1/complaints/`
  - `GET /api/v1/complaints/<uuid>/`
  - `POST /api/v1/complaints/<uuid>/confirm/`
  - `POST /api/v1/complaints/<uuid>/reject/`
- **Complaints (Supervisor)**:
  - `GET /api/v1/supervisor/complaints/unassigned/`
  - `GET /api/v1/supervisor/complaints/`
  - `POST /api/v1/supervisor/complaints/<uuid>/assign/`
  - `POST /api/v1/supervisor/complaints/<uuid>/reassign/`
- **Complaints (Employee)**:
  - `GET /api/v1/employee/complaints/`
  - `POST /api/v1/employee/complaints/<uuid>/verify/`
  - `GET /api/v1/employee/complaints/<uuid>/verification/`
  - `POST /api/v1/employee/complaints/<uuid>/progress/`
  - `POST /api/v1/employee/complaints/<uuid>/resolve/`
  - `GET /api/v1/employee/complaints/<uuid>/resolutions/`

---

## 3. Authentication Architecture

**Architecture Flow**:
1. **Frontend** calls `supabase.auth.signInWithPassword()` or OTP.
2. **Supabase Auth** authenticates the user and returns a session containing an `access_token` (JWT, typically ES256).
3. **Frontend API Client** intercepts all requests to the Django backend and attaches the Supabase `access_token` as a `Bearer` token.
4. **Django Backend** verifies the JWT using Supabase's JWKS (JSON Web Key Set), authenticates the user via `core.authentication.supabase.SupabaseAuthentication`, loads the matching PostgreSQL `Profile`, and returns the API response.

*Note: Do NOT create a separate JWT system or store passwords in Django.*

---

## 4. Supabase Auth Integration Design

- Use `@supabase/supabase-js`.
- Initialize using `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
- Let the Supabase client automatically handle session restoration and token refreshes.
- Wrap the app in an `<AuthProvider>` that listens to `supabase.auth.onAuthStateChange`.

---

## 5. Django API Integration Design

- Use the frontend's native API client (see section 21) to call Django `VITE_API_BASE_URL`.
- Attach the token using `await supabase.auth.getSession()`.
- Explicitly handle `401 Unauthorized` by redirecting to `/login`.

---

## 6. Role Architecture

The `role` is backend-owned and must be retrieved dynamically.
- Call `GET /api/v1/users/me/role/` upon successful login.
- Store the role in the global auth context.
- Roles mapping (as defined in `Complaint_Management_Elaborated_User_Stories.md`):
  1. Citizen
  2. Ground-Level Employee
  3. Supervisor
  4. Department Admin
  5. System Admin

---

## 7. Route Architecture

```text
/                       -> Landing (Public)
/login                  -> Login (Public)
/track                  -> Track Complaint (Public/Mock or simplified Citizen view)

(Authenticated & Protected Routes)
/dashboard              -> Unified Dashboard (Redirects/renders based on role)
/complaints             -> My Complaints (Citizen)
/complaints/new         -> Submit Complaint (Citizen)
/complaints/:id         -> Complaint Details (Shared, content adapts to role)
/queue                  -> Unassigned Queue (Supervisor)
/assigned               -> Assigned Complaints (Employee)
/department             -> Department Overview (Supervisor / Dept Admin)
/users                  -> User Management (System Admin)
/settings               -> Profile/Settings (All)
```

---

## 8. Citizen Frontend Design

**Functionality**: Submit complaints, track statuses, confirm/reject resolutions.
**Views**:
- **Submit**: Form capturing Category, Description, State, District, Google Maps URL, Media.
- **List**: `GET /api/v1/complaints/`
- **Detail**: Timelines, verify status, and action buttons to hit `/confirm/` or `/reject/`.

---

## 9. Employee Frontend Design

**Functionality**: Inspect sites, provide progress updates, submit final resolutions.
**Views**:
- **Assigned List**: `GET /api/v1/employee/complaints/`
- **Verification UI**: Form to hit `POST .../verify/` with valid status `verified` or `invalid`.
- **Resolution UI**: Form to hit `POST .../progress/` and `POST .../resolve/` with mandatory attachments.

---

## 10. Supervisor Frontend Design

**Functionality**: View department complaints, assign/reassign employees.
**Views**:
- **Queue**: `GET /api/v1/supervisor/complaints/unassigned/`
- **Department Complaints**: `GET /api/v1/supervisor/complaints/`
- **Assignment UI**: Modal/dropdown to hit `POST .../assign/` and `POST .../reassign/` using employee IDs from `GET /api/v1/users/department-members/`.

*Important: A district can have multiple supervisors. Supervisors see complaints routed to their department.*

---

## 11. Department Admin Frontend Design

**Functionality**: Oversee the entire department.
**Views**:
- **Department Members**: `GET /api/v1/users/department-members/`
- **Department Analytics**: Aggregated views (derived from department complaints).

---

## 12. System Admin Frontend Design

**Functionality**: Global oversight.
**Views**:
- **User Management**: Viewing profiles via `GET /api/v1/users/<uuid>/`.

---

## 13. Complaint Submission Flow

1. Citizen clicks "New Complaint".
2. Selects Category (from `GET /api/v1/categories/`).
3. Enters Description, State, District, and Google Maps URL. (Frontend DOES NOT ask for Lat/Lng).
4. Uploads photos.
5. Hits `POST /api/v1/complaints/`.
6. Backend extracts coordinates, routes, and returns `201 Created`.

---

## 14. Complaint Tracking Flow

- Track from the Dashboard or via specific ID.
- Hits `GET /api/v1/complaints/<uuid>/`.
- Displays `status_history`, `assignments`, and `resolutions` arrays visually as a timeline.

---

## 15. Complaint Lifecycle UI Mapping

- **SUBMITTED**: Waiting for automated routing.
- **UNDER_VERIFICATION**: In Supervisor queue.
- **ASSIGNED**: Employee must verify.
- **VERIFIED**: Progress updates expected.
- **IN_PROGRESS**: Work happening.
- **RESOLVED**: Employee submitted fix, waiting for Citizen confirmation.
- **CLOSED**: Terminal state.

---

## 16. Routing UI Implications

- Routing is backend-owned (`DepartmentCategoryRule`).
- Frontend never calculates routing.
- If a complaint fails routing (`RoutingFailureError`), the frontend displays the 422 error gracefully.

---

## 17. Phase 8 AI UI Implications

- Gemini AI properties (severity, confidence, model info) are managed entirely by the backend.
- The UI should strictly only display AI fields if they are included in the backend serializers (they currently aren't explicitly exposed to citizens, but may be to admins/supervisors).

---

## 18 & 19. API Endpoint & Request/Response Mapping

| User Story | Method | Endpoint | Payload | Response | Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Citizen submit | POST | `/api/v1/complaints/` | `category_id, description, state, district, google_maps_url, attachments` | `201 Created` | Citizen |
| Supv. assigns | POST | `.../assign/` | `employee_id, assignment_reason` | `200 OK` + Complaint | Supervisor |
| Emp. verifies | POST | `.../verify/` | `verification_result, verification_remarks, attachments` | `200 OK` | Employee |
| Emp. resolves | POST | `.../resolve/` | `resolution_details, attachments` | `200 OK` | Employee |

---

## 20. State Management Recommendation

**Recommendation**: **React Context (Auth) + TanStack Query (Data Fetching)**.
- **Why**: TanStack Query is perfect for server-state management (caching, invalidation, loading/error states) which is exactly what we need since all source of truth lives in Django.
- No need for Redux or Zustand for complex client state, as most state is just API responses.

---

## 21. API Client Recommendation

**Recommendation**: **Axios**.
- **Why**: Excellent support for request interceptors (to inject the Supabase token asynchronously before every request) and response interceptors (to handle global 401 redirects).

---

## 22. Component Architecture

- `RoleProtectedRoute`: Wraps routes to ensure only permitted roles can access them.
- `ComplaintCard`: Summary display for lists/queues.
- `ComplaintTimeline`: Visualizes `status_history` and `resolutions`.
- `StatusBadge`: Dynamic color-coded badge mapping to actual backend statuses.

---

## 23. Design-System Integration

- Keep `index.css` and its CSS variable token system.
- Preserve UI patterns for Cards, Buttons, and Data Tables.
- Re-theme the AssetFlow layout (e.g. sidebar navigation) into CivicConnect.

---

## 24. AssetFlow → CivicConnect Migration Mapping

| Old File | Action | New Civic Equivalent |
| :--- | :--- | :--- |
| `Landing.jsx` | KEEP / MODIFY | Connect "Track" to auth, clean up mock roles. |
| `Login.jsx` | REPLACE | Connect to Supabase Auth. |
| `Dashboard.jsx` | REPLACE | Civic Dashboard (Role-adaptive). |
| `Assets.jsx` / `AssetDetail.jsx` | REMOVE LATER | `Complaints.jsx` / `ComplaintDetail.jsx` |
| `Assignments.jsx` | REMOVE LATER | `Queue.jsx` (Supervisor unassigned view). |
| `Maintenance.jsx` | REMOVE LATER | `AssignedWork.jsx` (Employee view). |

---

## 25. Error Handling Strategy

- **401 Unauthorized**: Redirect to `/login`.
- **403 Forbidden**: Render a generic "Access Denied" empty state.
- **400 / 422**: Form validation errors mapping to UI fields (e.g. invalid Google Maps URL).
- **500**: Global toast notification "An unexpected error occurred".

---

## 26. Security Model

- **Environment Variables**: 
  - `VITE_SUPABASE_URL` (Public)
  - `VITE_SUPABASE_ANON_KEY` (Public)
  - `VITE_API_BASE_URL` (Public)
- **MUST NOT BE EXPOSED**: `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, `GEMINI_API_KEY`, `SUPABASE_JWT_SECRET`.
- **Authorization**: The frontend checks roles purely for UX (hiding tabs). Actual authorization enforcement MUST rely on the Django backend returning 403s.

---

## 27. Frontend Testing Strategy

- Use Vitest + React Testing Library.
- Test routing and protected routes with mock roles.
- Test form validation (Google Maps URL extraction requirement).
- Mock Axios for unit tests, but ensure E2E tests run against the REAL Django backend.

---

## 28. Environment Variables Required

Create a `.env` in the `frontend/` directory:
```
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 29. Dependency Changes

**To Install**:
- `@supabase/supabase-js` (Auth)
- `axios` (API Client)
- `@tanstack/react-query` (Server State Management)
- `lucide-react` (To replace duplicated SVGs)

---

## 30. Implementation Phases for Phase 9

1. **Setup & Dependencies**: Install Supabase, Axios, React Query. Setup `.env`.
2. **Auth Integration**: Implement `supabase.js` client, `<AuthProvider>`, and `Axios` interceptor. Connect `/login`.
3. **Role & Routing**: Implement `RoleProtectedRoute` and fetch `/me/role/`. Wire up the layout.
4. **Domain Refactor**: Remove AssetFlow hardcoded files. Build Complaint components.
5. **Role-Specific Views**: Build out Citizen, Employee, and Supervisor interfaces using real API data.

---

## 31. Risks and Unresolved Questions

- **Image Uploads**: Does the backend expect multipart/form-data or Base64? *(Audit confirms `MultiPartParser`, so `FormData` is required on the frontend).*
- **Pagination**: The backend `ListAPIView` generally paginates. The frontend must handle paginated JSON structures (`count`, `next`, `previous`, `results`).
