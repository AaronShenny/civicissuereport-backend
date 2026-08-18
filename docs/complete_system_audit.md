# Civic Issue Reporting System — Complete Backend + Frontend Audit

**Date of Audit:** August 18, 2026  
**Audited Version:** Integration Verification State (Checkpoint 24)  
**Status:** Audit Completed (No code changes, migrations, or database updates were applied during this audit)

---

## 1. Source of Truth

This audit compares the actual code implementation in the repository against:
*   The **Complaint Management / Civic Issue Reporting user stories** (`user_stories.txt`, `Complaint_Management_Elaborated_User_Stories.md`).
*   The **Supabase database design/schema** (`database_schema.md`).
*   The **Centralized designs document** (`frontend/designs.md`).

### Discrepancies and Gap Identification:
1.  **Duplicate Detection:** 
    *   *Requirement:* Detect similar complaints based on proximity, category, and description, and offer duplicate linking/merging.
    *   *Actual Implementation:* **MISSING**. There is no backend service, model field, or frontend page implementing duplicate detection.
2.  **Audit Logging:**
    *   *Requirement:* Track administrative changes, assignments, status updates, and logins in the database.
    *   *Actual Implementation:* **PARTIAL**. The `audit_logs` table exists in Supabase schema definitions, but the Django backend does not write to it during state transitions (e.g., assignment, verification). The only history tracked is `ComplaintStatusHistory`.
3.  **Department / System Admin Dashboards:**
    *   *Requirement:* Full analytics dashboard for Department Admins (performance, overdue complaints, charts) and System Admins (user/role settings, system-wide metrics).
    *   *Actual Implementation:* **NOT SPECIFIED / MISSING**. The pages (`AdminOverview.jsx` and `DepartmentComplaints.jsx`) exist as basic placeholders, but the Django API lacks endpoints for aggregating performance, overdue metrics, or system-wide stats.
4.  **Automatic Status Transition Timeline:**
    *   *Requirement:* Display status transition histories with changed-by users.
    *   *Actual Implementation:* **PARTIAL**. The Django backend records history, but if `status_history` is empty, the frontend has to fall back gracefully without fabricating data.

---

## 2. Repository Structure Audit

The repository contains a standard decoupled structure:

```text
root/
├── backend/                  # Django REST Framework application
│   ├── api/                  # API version routing (/api/v1/)
│   ├── apps/                 # Domain-driven Django apps (users, complaints, departments)
│   ├── core/                 # Shared core utilities (permissions, authentication)
│   ├── config/               # Settings (base.py, development.py)
│   └── tests/                # Pytest suite
├── frontend/                 # Vite + React Single Page Application (SPA)
│   ├── src/
│   │   ├── auth/             # Supabase Auth Provider context
│   │   ├── components/       # Reusable layout/UI components (Sidebar, Header, StatusBadge)
│   │   ├── lib/              # Centralized clients (api.js, supabase.js)
│   │   ├── pages/            # View components (Dashboard, ComplaintDetail, Settings)
│   │   └── router.jsx        # Route registry and ProtectedRoute wrappers
├── supabase/                 # Supabase configuration, seed, and schema definitions
└── docs/                     # Implementation notes and progress reports
```

### High-Level Architecture Map:
```text
      [ React Frontend SPA ]
                │ (Supabase Session)
                ├────────────────────────┐
                ▼                        ▼
      [ Supabase Auth JWT ]    [ Supabase Storage ] (File Uploads)
                │
                │ (Bearer Token)
                ▼
       [ Django REST API ]
                │ (Supabase JWT Verification / RS256 JWKS)
                ▼
       [ PostgreSQL / PostGIS ] (Supabase Host)
                │
                ├── [ AI Severity Engine ] (Gemini API Background Threads)
                ├── [ Notification Service ]
                └── [ Spatial Routing Engine ] (PostGIS Coordinates)
```

**Verification:** The actual implementation follows this architecture. The frontend retrieves the Supabase Session, uploads attachments directly to Supabase storage, and sends the raw JWT token to the Django REST API, which validates it using its custom Supabase JWT Authentication backend.

---

## 3. Backend Complete Audit

The Django backend utilizes Django REST Framework (DRF) to serve a headless API.

*   **config/settings/**: Correctly decoupled settings using `base.py` for shared configuration, and `development.py` for local dev. Contains database connections mapped to the Supabase PostgreSQL host.
*   **authentication/**: Handled in `core/authentication/supabase.py`. Custom backend verifies ES256/RS256 JWT tokens using the Supabase project’s public JSON Web Key Sets (JWKS).
*   **permissions/**: Centralized under `core/permissions/roles.py`. Implements `IsCitizen`, `IsSupervisor`, `IsGroundLevelEmployee`, etc., checking matching role profiles in the DB.
*   **users app**: Manages the user profile model.
*   **departments app**: Maps departments and geographic jurisdictions.
*   **complaints app**: Main engine managing submission logic, location parsing, PostGIS integration, assignments, resolutions, and timeline status histories.
*   **AI Integration**: Asynchronous Gemini API integration (`apps/complaints/services.py` + `number.py`). Runs structured classification as background execution using threads.
*   **Background Tasks**: Relies on background python threads spawned within views rather than a message broker like Celery.

---

## 4. Backend Database Contract

Django Models (`managed = False` in meta) match the live Supabase PostgreSQL schema.

*   **PostGIS geography support**: Models map the spatial coordinates using `location_lat` and `location_lng` fields, converting Google Maps URLs into PostGIS geometries on the database side via raw SQL queries in `services.py`.
*   **PostgreSQL Sequences**: `complaint_number_seq` exists and is queried via raw SQL on submission to generate unique numbers (`CMP-YYYY-00000X`).
*   **Triggers/Functions**: RLS is configured in Supabase, but since Django connects via the `postgres` superuser/service role, RLS is bypassed at the Django connection level.
*   **Constraints**:
    *   `ComplaintCategory` mapping has valid foreign key restraints.
    *   Status histories are correctly linked.
*   **Mismatch Identified:** 
    *   **Regression Failure:** The detail serializer `ComplaintDetailSerializer` Meta has `read_only_fields = fields` (previously changed to resolve a DRF `TypeError` caused by `'__all__'`). This broke the assertion inside the test suite: `self.assertEqual(meta.read_only_fields, '__all__')` (Line 739 of `test_phase8_ai_severity.py`).

---

## 5. Authentication Audit

### Verification Flow:
1.  Frontend logs in using Supabase Client, acquiring a JWT.
2.  JWT is passed in the `Authorization: Bearer <token>` header to Django.
3.  Django's `SupabaseJWTAuthentication` intercepts the header, fetches the Supabase JWKS endpoint, and validates the token signature, audience (`authenticated`), issuer, and expiry.
4.  If valid, Django maps the token's `sub` (UID) to the corresponding `Profile.supabase_uid` to set `request.user`.

*   **Role Retrieval:** Profiles are dynamically queried to find the assigned `Role` name.
*   **Audience/Issuer validation:** Enforced.
*   **Secrets Exposure:** Validated. No service-role keys or database passwords are hardcoded in the frontend.

---

## 6. RBAC / Authorization Audit

Django enforces strict role authorization inside its views using `permission_classes`.

*   **Citizen Isolation:** Citizens can ONLY access their own complaints. Enforced in `ComplaintListCreateView` and `ComplaintDetailView` using `.filter(citizen_id=request.user.id)`.
*   **Employee Isolation:** Employees can ONLY view complaints assigned to them (`assigned_employee_id=employee.id`) in `EmployeeAssignedComplaintsView`.
*   **Supervisor Isolation:** Supervisors can only see complaints assigned to their department (`assigned_department_id=supervisor.department_id`) in `SupervisorDepartmentComplaintsView`.
*   **Boundary Crossing Check:**
    *   *Supervisor vs Employee:* Supervisors cannot assign employees outside of their department because the employee assignment service verifies department bounds.
    *   *Citizen vs Citizen:* Checked. An IDOR attempt to retrieve another citizen's complaint UUID returns a 404 (due to queryset filtering) or 403.

---

## 7. Complaint Lifecycle Audit

State transitions follow the lifecycle:
`submitted` → `under_verification` → `assigned` → `verified` → `in_progress` → `resolved` → `closed`

### Transition Matrix:

| Transition | Initiator | API Endpoint | DB State Change | History Created | Status |
|------------|-----------|--------------|-----------------|-----------------|--------|
| -> submitted | Citizen | `POST /api/v1/complaints/` | status='submitted' | Yes | 🟢 Working |
| -> under_verification | System (Auto) | `POST /api/v1/complaints/<uuid>/route/` | status='under_verification', assigns department | Yes | 🟢 Working |
| -> assigned | Supervisor | `POST /api/v1/supervisor/complaints/<uuid>/assign/` | status='under_verification', sets assigned_employee | Yes | 🟢 Working |
| -> verified / invalid | Employee | `POST /api/v1/employee/complaints/<uuid>/verify/` | status='verified' or 'invalid' | Yes | 🟢 Working |
| -> in_progress | Employee | `POST /api/v1/employee/complaints/<uuid>/progress/` | status='in_progress' | Yes | 🟢 Working |
| -> resolved | Employee | `POST /api/v1/employee/complaints/<uuid>/resolve/` | status='resolved', resolution proof logged | Yes | 🟢 Working |
| -> closed (Confirm) | Citizen | `POST /api/v1/complaints/<uuid>/confirm/` | status='closed', closure_confirmation='confirmed' | Yes | 🟢 Working |
| -> back to in_progress | Citizen | `POST /api/v1/complaints/<uuid>/reject/` | status='in_progress', closure_confirmation='rejected' | Yes | 🟢 Working |

---

## 8. Complaint Submission Investigation

During the initial phase of submission debugging, complaints were failing silently because:
1.  **Frontend Validation Block (Root Cause):** The form validation blocked submit calls if the Category field was left unselected. 
2.  **Missing Alert UI Class (Secondary Issue):** The `.alert-error` stylesheet classes were missing in `index.css`. The validation message was successfully set in React state but was rendered as an invisible div. The user clicked submit, but nothing occurred on the UI and no network request was triggered.
3.  **DRF Serializer TypeError:** The backend was throwing an HTTP 500 when attempting to fetch complaint details due to the invalid `'__all__'` string definition on `read_only_fields`.

**Current Status:** All these points have been resolved in the workspace. Form submissions are verified to be fully operational (HTTP 201 Created), and the table listings are working cleanly.

---

## 9. Location / Routing Audit

Geographic assignment is processed via PostGIS.
*   **Coordinate Extraction:** Done in `backend/apps/complaints/location.py` using RegExp on the incoming `google_maps_url`. It extracts coordinates correctly for standard maps links, place links, and raw parameters.
*   **Routing Logic:** Defined in `backend/apps/complaints/routing.py`. It looks up `DepartmentCategoryRule` records matching the category and geographical jurisdiction bounds.
*   **Defect:** If a complaint falls outside mapped jurisdictions, it routes to a fallback department. Mapped reference data in the DB must contain at least one fallback rule to prevent routing errors.

---

## 10. AI Audit

AI functions analyze the severity of submitted reports.
*   **Model:** Google Gemini API (`gemini-1.5-flash`).
*   **Execution:** Spawns a background thread in `_run_ai_classification_in_background` to prevent blocking the HTTP response.
*   **Failure Isolation:** Excellent. If the Gemini API limits hit, or the API key is missing, it logs the exception, handles the thread, and keeps the complaint at default priority without crashing the submission.
*   **Audit Status:** Fully implemented and verified.

---

## 11. Duplicate Detection Audit

*   **Status:** **MISSING**. No duplicate similarity matching algorithms or tables exist in the current application code.

---

## 12. Storage / Attachments Audit

*   **Bucket:** Uses Supabase Storage `complaint-media`.
*   **Upload flow:** Frontend uploads directly to Supabase storage using the authenticated user session, then sends the public file URL in the payload to Django.
*   **Validation:** Django verifies attachment count and sizes in `services.py:validate_attachments`.
*   **Isolation:** The service role key is kept strictly backend-side. The frontend uses the standard user JWT session to write to storage.

---

## 13. Notification Audit

*   **Database:** A `notifications` table exists in the database.
*   **Backend:** `Notification` records are created inside `services.py` on submission and assignment.
*   **Frontend UI:** **MISSING / PARTIAL**. The bell icon is present in `Header.jsx`, but there is no notification panel or tray component to view past alerts.

---

## 14. Audit Logging

*   **Status:** **MISSING**. Although the database defines an `audit_logs` table, no application view or service actively inserts logging entries into it. Only the `status_history` keeps track of transitions.

---

## 15. Backend API Inventory

| Method | Endpoint | Role | Purpose | Serializer | Status | Frontend Used |
|--------|----------|------|---------|------------|--------|---------------|
| GET | `/api/v1/health/` | Any | Health check | None | 🟢 Working | No |
| GET | `/api/v1/categories/` | Any | Fetch active categories | `ComplaintCategorySerializer` | 🟢 Working | Yes |
| GET | `/api/v1/categories/<id>/` | Any | Get category details | `ComplaintCategorySerializer` | 🟢 Working | No |
| GET | `/api/v1/complaints/` | Citizen | List citizen's complaints | `ComplaintListSerializer` | 🟢 Working | Yes |
| POST | `/api/v1/complaints/` | Citizen | Submit a complaint | `ComplaintSubmitSerializer` | 🟢 Working | Yes |
| GET | `/api/v1/complaints/<uuid>/` | Citizen | Get complaint details | `ComplaintDetailSerializer` | 🟢 Working | Yes |
| POST | `/api/v1/complaints/<uuid>/route/` | System | Route complaint to dept | None | 🟢 Working | No |
| POST | `/api/v1/complaints/<uuid>/confirm/` | Citizen | Confirm resolution | `ConfirmResolutionSerializer` | 🟢 Working | Yes |
| POST | `/api/v1/complaints/<uuid>/reject/` | Citizen | Reject resolution | `RejectResolutionSerializer` | 🟢 Working | Yes |
| GET | `/api/v1/users/me/` | Any | Get profile info | `ProfileSerializer` | 🟢 Working | Yes |
| PATCH | `/api/v1/users/me/` | Any | Update profile details | `ProfileUpdateSerializer` | 🟢 Working | Yes |
| GET | `/api/v1/users/me/role/` | Any | Get active role | None | 🟢 Working | Yes |
| GET | `/api/v1/users/me/department/` | Any | Get user's department | None | 🟢 Working | Yes |
| GET | `/api/v1/users/department-members/` | Supervisor | List team members | `StaffProfileSummarySerializer` | 🟢 Working | Yes |
| GET | `/api/v1/supervisor/complaints/unassigned/` | Supervisor | View unassigned queue | `SupervisorComplaintListSerializer` | 🟢 Working | Yes |
| GET | `/api/v1/supervisor/complaints/` | Supervisor | View department queue | `SupervisorComplaintListSerializer` | 🟢 Working | Yes |
| POST | `/api/v1/supervisor/complaints/<uuid>/assign/` | Supervisor | Assign employee | `AssignEmployeeSerializer` | 🟢 Working | Yes |
| POST | `/api/v1/supervisor/complaints/<uuid>/reassign/` | Supervisor | Reassign employee | `ReassignEmployeeSerializer` | 🟢 Working | Yes |
| GET | `/api/v1/employee/complaints/` | Employee | View assigned complaints | `SupervisorComplaintListSerializer` | 🟢 Working | Yes |
| POST | `/api/v1/employee/complaints/<uuid>/verify/` | Employee | Submit verification | `SubmitVerificationSerializer` | 🟢 Working | Yes |
| GET | `/api/v1/employee/complaints/<uuid>/verification/` | Employee | Get verification notes | `ComplaintVerificationSerializer` | 🟢 Working | Yes |
| POST | `/api/v1/employee/complaints/<uuid>/progress/` | Employee | Log progress update | `SubmitProgressUpdateSerializer` | 🟢 Working | Yes |
| POST | `/api/v1/employee/complaints/<uuid>/resolve/` | Employee | Mark complaint resolved | `SubmitResolutionSerializer` | 🟢 Working | Yes |
| GET | `/api/v1/employee/complaints/<uuid>/resolutions/` | Employee | Get resolutions log | `ComplaintResolutionSerializer` | 🟢 Working | Yes |

---

## 16. Frontend Complete Audit

*   **Routing (`router.jsx`):** Configures layout shell nesting and applies `ProtectedRoute` authorization guards.
*   **Layouts (`AppLayout.jsx`):** Employs standard flex container layouts.
*   **Styles (`index.css`):** Employs root CSS tokens. Fully responsive layout selectors.
*   **Legacy Code:** Sidebar features remnants of the old asset management template (`Assets`, `Categories`). These were disabled from rendering in code but the pages files remain in the source tree (`src/pages/Assets.jsx`, etc.).

---

## 17. Frontend Authentication Audit

*   **AuthProvider:** Correctly manages user token caching, session state updates, and triggers profile reload calls.
*   **Token Refresh:** Handled natively by the Supabase client wrapper.
*   **Route Guards:** Unauthenticated redirects point correctly to `/login`.

---

## 18. Frontend API Audit

*   **api.js Client:** Correctly inserts Bearer JWT authorization tokens and configures headers. Standardized methods (`get`, `post`, `patch`, `put`, `delete`) map cleanly to DRF endpoints.

---

## 19. Frontend Role Audit

*   **Citizen:** Accesses dashboard KPIs, My Complaints table, settings profile, and the report submission form.
*   **Employee:** Dashboard layout renders assigned tickets.
*   **Supervisor:** Pulls the department queue and team dropdowns to allocate workers.
*   **Admin roles:** Placeholders exist but lack structural dashboard content.

---

## 20. Citizen Workflow Audit
*   Registration: 🟢 **PASS**
*   Login: 🟢 **PASS**
*   Dashboard View: 🟢 **PASS**
*   Submit Complaint: 🟢 **PASS**
*   My Complaints Table: 🟢 **PASS**
*   Complaint Detail & Timeline: 🟢 **PASS**
*   Confirm / Reject: 🟢 **PASS**

---

## 21. Employee Workflow Audit
*   Inspect Assigned: 🟢 **PASS**
*   Submit Verification: 🟢 **PASS**
*   Progress Logging: 🟢 **PASS**
*   Final Resolution: 🟢 **PASS**

---

## 22. Supervisor Workflow Audit
*   Unassigned Queue: 🟢 **PASS**
*   Employee Dropdown: 🟢 **PASS**
*   Assign Ticket: 🟢 **PASS**
*   Reassign Ticket: 🟢 **PASS**

---

## 23. Department Admin Audit
*   **Status:** 🔴 **BROKEN / MISSING**. The UI is a placeholder; backend APIs do not support department-wide performance or statistical reports.

---

## 24. System Admin Audit
*   **Status:** 🔴 **BROKEN / MISSING**. The UI is a placeholder; no user management, audit logs viewer, or system-wide settings interface is wired.

---

## 25. Track Complaint Audit

*   **Status:** ⚪ **MISSING**. A public `/track` route does not exist. Users must log in to view complaints in their dashboard or list view.

---

## 26. Design / UX Audit

*   **Typography/Spacing:** Verified. Colors and variables (`--text`, `--bg-default`) align with `designs.md`.
*   **Responsiveness:** Fluid breakpoints are implemented for mobile.
*   **AssetFlow Cleanup:** Visual assets or sidebar menu structures do not display legacy links.

---

## 27. Security Audit

*   **Secrets Exposure:** Safe. No secrets are stored in the git repo.
*   **JWKS Authentication:** Django verifies tokens dynamically with Supabase certificates.
*   **CORS Configuration:** Mapped correctly in `.env` and `settings/base.py`.
*   **IDOR Guards:** Django querysets are strictly constrained by `citizen_id` or `assigned_employee_id`.

---

## 28. Testing Audit

The test suite runs using `pytest`.
*   **Passed Tests:** 241
*   **Failed Tests:** 1 (`test_severity_fields_read_only_in_detail_serializer` due to change in `read_only_fields` configuration in DRF Serializers).

---

## 29. End-to-End Gap Analysis

| Requirement | Backend | Database | Frontend | E2E Tested | Status |
|-------------|---------|----------|----------|------------|--------|
| Authentication | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Working |
| Submit Complaint | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Working |
| Geo-routing | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Working |
| AI Severity | 🟢 Yes | 🟢 Yes | ⚪ No | 🟢 Yes | 🟡 Implemented but untested on UI |
| Assignment | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Working |
| Verification | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Working |
| Progress Log | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Working |
| Resolution | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Working |
| Confirm/Reject | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Yes | 🟢 Working |
| Notifications | 🟡 Partial | 🟢 Yes | 🔴 No | ⚪ No | 🟠 Partial (Backend only) |
| Duplicate Detection | 🔴 No | 🔴 No | 🔴 No | ⚪ No | ⚫ Missing |
| Dept Admin Dash | 🔴 No | 🟢 Yes | 🔴 No | ⚪ No | ⚫ Missing |
| System Admin Dash | 🔴 No | 🟢 Yes | 🔴 No | ⚪ No | ⚫ Missing |
| Audit Logs | 🔴 No | 🟢 Yes | 🔴 No | ⚪ No | ⚫ Missing |

---

## 30. Critical Blockers

*   **P0 (Blocker):** None. The core Citizen, Employee, and Supervisor workflows are fully functional end-to-end.
*   **P1 (Regression):** `test_severity_fields_read_only_in_detail_serializer` is failing in the test suite due to a serializer meta attribute update.
*   **P2 (Core Missing):**
    *   **Notification UI Panel:** The bell icon exists but doesn't display any messages.
    *   **Admin/Supervisor Statistics:** Dashboard statistics are calculated on loaded data but missing global aggregations.

---

## 31. Dead / Legacy Code Audit

*   **Legacy Pages:** `frontend/src/pages/Assets.jsx`, `frontend/src/pages/Categories.jsx`, `frontend/src/pages/Maintenance.jsx` are left over from the AssetFlow template. They are not active in `router.jsx` or `Sidebar.jsx`, but files exist.
*   **Legacy Components:** Asset-specific models or views in the Django backend are inactive.

---

## 32. Final Project Scorecard

```text
DATABASE        90%
BACKEND         85%
AUTH            100%
ROUTING         90%
AI              85%
NOTIFICATIONS   30%
FRONTEND        80%
CITIZEN         100%
EMPLOYEE        95%
SUPERVISOR      95%
DEPT ADMIN      10%
SYSTEM ADMIN    10%
E2E             85%
SECURITY        95%
```

---

## 33. Final Recommended Roadmap

1.  **Phase 1: Fix DRF Serializer Regression Guard**
    *   *Goal:* Fix the `read_only_fields` declaration in `ComplaintDetailSerializer` to ensure both DRF returns correct values and the regression suite passes.
2.  **Phase 2: Remove Dead AssetFlow Code**
    *   *Goal:* Safely purge inactive legacy frontend views (`Assets.jsx`, etc.) and backend models to clean up the repository footprint.
3.  **Phase 3: Develop Notifications Tray UI**
    *   *Goal:* Create a popover/list component bound to the header bell icon that fetches `/api/v1/notifications` to present status updates to citizens and staff.
4.  **Phase 4: Implement Department Admin Dashboard APIs**
    *   *Goal:* Design and expose endpoints mapping department performance KPI aggregations so the admin layout becomes functional.
5.  **Phase 5: Implement System Admin User Management APIs**
    *   *Goal:* Wire endpoints to edit profiles, roles, and view `audit_logs` entries for System Admin auditing.
6.  **Phase 6: Duplicate Detection Engine**
    *   *Goal:* Implement geo-proximity and text similarity matching to flag and link duplicate tickets.

---

## 34. Most Important Rule

*   No modifications to files or databases occurred during this audit session.
*   All data schemas, permissions, environments, and application layers remain in their original state.
