# Phase 9.2 Frontend Implementation Documentation

## Overview
Phase 9.2 completes the transition from the legacy AssetFlow mockup to the Civic Issue Reporting System domain. The frontend now integrates with the real Django and Supabase backend APIs, and the application routes adapt to the authenticated user's role.

## Routes & Role Mapping

The primary routing architecture revolves around a unified `/dashboard` that fetches varying statistics based on the user's role. Role-specific routes are restricted by UI visibility, though backend enforcement prevents unauthorized API access.

| Role | Available Routes |
|------|-----------------|
| **Citizen** | `/dashboard`, `/complaints/new`, `/complaints`, `/complaints/:id` |
| **Ground-Level Employee** | `/dashboard`, `/employee/complaints` (includes action panels for verification, progress, and resolution) |
| **Supervisor** | `/dashboard`, `/supervisor/unassigned`, `/supervisor/complaints` |
| **Department Admin** | `/dashboard`, `/department/complaints` (Placeholder) |
| **System Admin** | `/dashboard`, `/admin/overview` (Placeholder) |

## API Contracts & Integration

All interactions use the `api.js` fetch wrapper, which automatically injects the Supabase JWT. Submissions with file attachments utilize `FormData` to leverage the browser's automatic `multipart/form-data` boundary generation.

### Citizen Endpoints
- **Create Complaint**: `POST /api/v1/complaints/` (Requires `category_id`, `description`, `state`, `district`, `google_maps_url`, and optional `attachments`).
- **List Complaints**: `GET /api/v1/complaints/`
- **Retrieve Detail**: `GET /api/v1/complaints/<uuid>/`
- **Resolution Feedback**: `POST /api/v1/complaints/<uuid>/confirm/` or `.../reject/`

### Employee Endpoints
- **List Assigned Queue**: `GET /api/v1/employee/complaints/`
- **Verify Issue**: `POST /api/v1/employee/complaints/<uuid>/verify/`
- **Update Progress**: `POST /api/v1/employee/complaints/<uuid>/progress/`
- **Resolve Issue**: `POST /api/v1/employee/complaints/<uuid>/resolve/`

### Supervisor Endpoints
- **List Unassigned**: `GET /api/v1/supervisor/complaints/unassigned/`
- **List Department Queue**: `GET /api/v1/supervisor/complaints/`
- **Assign Employee**: `POST /api/v1/supervisor/complaints/<uuid>/assign/`
- **Fetch Employees**: `GET /api/v1/users/department-members/`

## Data Flow & Authentication
Authentication relies on the frozen Phase 9.1 architecture (`Supabase Auth` -> `api.js`). Responses with HTTP `4xx` and `5xx` throw errors containing the detail string from the Django backend. React components uniformly trap these in `try-catch` blocks and render them in a standard Error Empty State component.

## Error Handling
Every API-driven component follows a standard state triad: `data`, `loading`, `error`. 
If `error` is present, the component renders a visually consistent "Error" empty state with a "Retry" button (calling `window.location.reload()` or the specific load function). 
For form actions, the `alert()` method natively propagates backend errors (e.g., 400 Bad Request if verification remarks are missing).

## Backend Gaps Identified
- **Employee Detail View**: `GET /api/v1/employee/complaints/` returns a summarized list. There is no employee-specific detail endpoint to view full descriptions or media. Action forms are currently rendered inline with the list.
- **Department Admin Dashboard**: No specific aggregation endpoints exist for Department Admins.
- **System Admin Dashboard**: No specific aggregation or management endpoints exist for System Admins.

## AssetFlow Migration Status
The new Civic routes are live and running parallel to the legacy AssetFlow routes. The AssetFlow files (`Assets.jsx`, `AssetDetail.jsx`, `AssetForm.jsx`, `Categories.jsx`, `Assignments.jsx`, `Maintenance.jsx`, `Reports.jsx`, `Settings.jsx`, `Users.jsx`) have not been deleted pending explicit instruction to remove them.
