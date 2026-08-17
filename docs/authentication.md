# Authentication & Authorization

## Authentication Flow

```
User logs in via React + Supabase JS
    ↓
Supabase Auth issues JWT (Access Token)
    ↓
React includes token: Authorization: Bearer <token>
    ↓
Django DRF: SupabaseAuthentication.authenticate()
    ↓
Verify JWT signature using SUPABASE_JWT_SECRET (HS256)
    ↓
Extract user UUID from 'sub' claim
    ↓
Load public.profiles WHERE id = <uuid>
    + select_related: role, department, supervisor
    ↓
Check account_status == 'active'  (inactive → 401)
    ↓
request.user = Profile instance
    ↓
DRF permission_classes run against the loaded Profile
```

## Role Hierarchy

```
system_admin          ← full system access, no dept restriction
department_admin      ← full dept access within their department
supervisor            ← team-level access within their department
ground_level_employee ← assigned-complaint access only (Phase 3+)
citizen               ← own complaints only
```

## Permission Classes (core/permissions/roles.py)

| Class | Description |
|---|---|
| `IsAuthenticatedViaSupabase` | Valid JWT + active profile required |
| `IsCitizen` | citizen role |
| `IsGroundLevelEmployee` | ground_level_employee role |
| `IsSupervisor` | supervisor role |
| `IsDepartmentAdmin` | department_admin role |
| `IsSystemAdmin` | system_admin role |
| `IsStaffMember` | any non-citizen role |
| `IsDepartmentStaff` | employee/supervisor/dept-admin |
| `IsSupervisorOrAbove` | supervisor, dept-admin, system-admin |
| `IsDepartmentAdminOrSystemAdmin` | dept-admin or system-admin |
| `IsSameDepartment` | object-level: same dept as caller |
| `IsOwnProfile` | object-level: own profile or system-admin |

## Rules

- **Role values come exclusively from the database** — never from the request body.
- **Department values come exclusively from the database** — never from the request body.
- Inactive accounts are rejected at the authentication layer before any permission check runs.
- Ground-Level Employees access complaints only when `complaint.assigned_employee_id == user.id` (enforced in Phase 3).

