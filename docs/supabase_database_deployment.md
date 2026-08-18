# Supabase Database Deployment — Final Pre-Deployment Audit

> **Status: AWAITING EXPLICIT APPROVAL — Supabase has NOT been modified.**
> Migration file: `supabase/migrations/20260818115322_initial_schema.sql`

---

## 1. Original Authoritative Schema vs Newly Confirmed Requirements

| Item | Original `database_schema.md` | Newly Confirmed Requirement | SQL Action |
|------|-------------------------------|----------------------------|------------|
| `profiles.jurisdiction_id` | Not defined | Required for supervisor district routing | **ADDED** |
| `complaints.state` | Not defined | Citizen-supplied; no reverse geocoding | **ADDED** |
| `complaints.google_maps_url` | Not defined | Source URL for coordinate extraction | **ADDED** |
| `department_category_rules.jurisdiction_id` | Not defined | District-specific category→department override | **ADDED** |
| `complaint_number_seq` | Implied | Django-owned CMP-YYYY-NNNNNN generation | **ADDED** |

---

## 2. Routing Model

```
Citizen supplies: State + District + Google Maps URL + Category
                      ↓
Backend extracts: latitude, longitude from Google Maps URL
Backend stores:   location (PostGIS Point), location_lat, location_lng,
                  state (text), district (text)
                      ↓
Routing query:
  SELECT department_id
  FROM   department_category_rules
  WHERE  category_id = :category
    AND  (jurisdiction_id = :district_jurisdiction_id
          OR jurisdiction_id IS NULL)   -- NULL = global fallback
  ORDER BY
    jurisdiction_id NULLS LAST,        -- specific rule takes precedence
    priority_rank ASC
  LIMIT 1
                      ↓
Supervisor notification query:
  SELECT p.*
  FROM   profiles p
  JOIN   jurisdictions j ON j.id = p.jurisdiction_id
  WHERE  p.department_id   = :routed_department_id
    AND  j.name            = :complaint_district
    AND  p.role_id         = (SELECT id FROM roles WHERE role_name = 'supervisor')
    AND  p.account_status  = 'active'
```

**Result**: Many supervisors per district per department are correctly returned. No 1-to-1 constraint exists.

---

## 3. District / Supervisor Relationship

```
jurisdictions (area_type='district')
    id = <uuid for Ernakulam>
    name = 'Ernakulam'

profiles (supervisor A)
    department_id   = <Public Works uuid>
    jurisdiction_id = <Ernakulam uuid>
    role_id         = supervisor
    account_status  = active

profiles (supervisor B)
    department_id   = <Public Works uuid>
    jurisdiction_id = <Ernakulam uuid>
    role_id         = supervisor
    account_status  = active

profiles (supervisor C)
    department_id   = <Health Dept uuid>
    jurisdiction_id = <Ernakulam uuid>
    role_id         = supervisor
    account_status  = active
```

A single query correctly returns supervisors A and B for `Public Works + Ernakulam`, and C for `Health + Ernakulam`. No one-to-one bottleneck.

---

## 4. Category + District Routing Relationship

`department_category_rules` now has three columns:

| `category_id` | `jurisdiction_id` | `department_id` | Meaning |
|---|---|---|---|
| pothole | Ernakulam uuid | Public Works uuid | Pothole in Ernakulam → Public Works |
| pothole | Idukki uuid | Roads Dept uuid | Pothole in Idukki → Roads Dept |
| pothole | NULL | Default Works uuid | Pothole anywhere else → Default |

Lookup logic: prefer the jurisdiction-specific rule; fall back to NULL (global) if none exists. `UNIQUE(department_id, category_id, jurisdiction_id)` enforces no duplicate rules.

---

## 5. Location Model

```sql
-- In complaints table:
google_maps_url  text            -- citizen-supplied input URL
location         geography(Point,4326)  -- PostGIS point (extracted)
location_lat     numeric(9,6)    -- decimal latitude (extracted)
location_lng     numeric(9,6)    -- decimal longitude (extracted)
location_address text            -- optional human-readable address
state            text            -- citizen-supplied (no reverse geocoding)
district         text            -- citizen-supplied (no reverse geocoding)
```

**No reverse geocoding is implemented. `state` and `district` are taken directly from citizen input.**

---

## 6. Django Model Discrepancies (DO NOT MODIFY YET — awaiting approval)

| Model | File | Missing Field | Required SQL Column | Action Needed |
|-------|------|--------------|---------------------|---------------|
| `Profile` | `apps/users/models.py` | `jurisdiction_id` | `profiles.jurisdiction_id uuid FK` | Add ForeignKey to `Jurisdiction` |
| `Complaint` | `apps/complaints/models.py` | `state` | `complaints.state text` | Add `TextField(null=True, blank=True)` |
| `Complaint` | `apps/complaints/models.py` | `google_maps_url` | `complaints.google_maps_url text` | Add `TextField(null=True, blank=True)` |
| `DepartmentCategoryRule` | `apps/departments/models.py` | `jurisdiction_id` | `department_category_rules.jurisdiction_id uuid FK` | Add ForeignKey to `Jurisdiction` |
| `DepartmentCategoryRule` | `apps/departments/models.py` | `unique_together` mismatch | `UNIQUE(department_id, category_id, jurisdiction_id)` | Update `unique_together` or `UniqueConstraint` |

---

## 7. Trigger Ownership Table

| Trigger / Function | Owner | Rationale |
|---|---|---|
| `set_updated_at` on `profiles` | **DATABASE** | Safe guard for direct DB edits. No conflict with Django (Django uses `auto_now=False`). |
| `set_updated_at` on `complaints` | **DATABASE** | Same as above. |
| `handle_new_auth_user` (auth.users → profiles) | **DATABASE** | Required on Supabase Auth signup; Django never creates users directly. |
| `complaint_number` generation (CMP-YYYY-NNNNNN) | **DJANGO** | `apps/complaints/number.py`; uses `complaint_number_seq` sequence. DB trigger omitted to prevent conflict. |
| `complaint_status_history` inserts | **DJANGO** | Explicitly called in `assignment.py`, `verification.py`, `resolution.py`, `closure.py`. A DB trigger would create duplicate rows. **DB trigger intentionally omitted.** |
| `verification_status` update | **DJANGO** | `verification.py` sets `complaint.status = VERIFIED / INVALID`. DB trigger omitted. |
| `resolution_status` update | **DJANGO** | `resolution.py` / `closure.py` sets `complaint.status = RESOLVED / CLOSED`. DB trigger omitted. |
| `notifications` creation | **DJANGO** | Notification service in Django. DB trigger omitted. |

---

## 8. RLS Policy Table (Complete — All 24 Tables)

| Table | RLS Enabled | Notes |
|-------|-------------|-------|
| `roles` | ✅ | Public SELECT |
| `departments` | ✅ | Public SELECT |
| `jurisdictions` | ✅ | Public SELECT |
| `profiles` | ✅ | Own row; staff reads dept peers; sysadmin full. **No recursive policy — uses SECURITY DEFINER helpers.** |
| `user_permissions` | ✅ | Own row; sysadmin full |
| `login_audit_log` | ✅ | Own + sysadmin reads |
| `audit_logs` | ✅ | Sysadmin read; backend writes via service_role |
| `complaint_categories` | ✅ | Public SELECT |
| `department_category_rules` | ✅ | Any authenticated user reads |
| `complaints` | ✅ | Citizen: own. Employee: assigned. Supervisor: dept+district. Dept Admin: dept. Sysadmin: all. |
| `complaint_attachments` | ✅ | Mirrors complaint access per role. INSERT restricted by purpose type per role. **Fixed: no open SELECT.** |
| `complaint_classifications` | ✅ | Citizen: own complaint. Staff: all in scope. |
| `classification_review_tasks` | ✅ | Assigned user; dept admin; sysadmin |
| `priority_scoring_rules` | ✅ | Supervisor/admin read only |
| `location_reference_points` | ✅ | Any authenticated user |
| `complaint_priority_assessments` | ✅ | Mirrors complaint access |
| `complaint_duplicates` | ✅ | Supervisor/admin only |
| `complaint_assignments` | ✅ | Employee own; supervisor dept; dept admin; sysadmin |
| `complaint_verifications` | ✅ | Verifier; supervisor/admin; citizen own complaint |
| `complaint_resolutions` | ✅ | Citizen own; staff read |
| `complaint_status_history` | ✅ | Citizen own; staff read |
| `notifications` | ✅ | Own recipient only; own UPDATE (mark-as-read) |
| `notification_preferences` | ✅ | Own row SELECT/INSERT/UPDATE |
| `report_exports` | ✅ | Own; dept admin; sysadmin |

---

## 9. Defects Fixed vs Previous SQL

| # | Defect | Fix Applied |
|---|--------|-------------|
| 1 | Recursive `profiles` policy (`SELECT 1 FROM profiles WHERE id = auth.uid()`) | Replaced with `SECURITY DEFINER` helper functions (`auth_user_role()`, `auth_user_department_id()`, etc.) |
| 2 | Attachment SELECT policy was completely open (no user filter) | Replaced with 5 role-specific policies each joining back to `complaints` |
| 3 | 14 tables had RLS enabled via `ALTER TABLE` missing | All 24 tables now explicitly listed |
| 4 | `storage.objects` RLS not enabled | `ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY` added |
| 5 | Storage had only 2 policies (citizen upload + citizen read) | 6 storage policies covering all roles and purposes |
| 6 | `handle_new_user()` used hard-coded `role_id = 1` | Now resolves `citizen` role_id by name via subquery |
| 7 | Supervisor policy used hard-coded `role_id IN (3, 4)` | All role checks now use `auth_user_role() = 'supervisor'` (text) |
| 8 | `complaint_verifications` and `complaint_resolutions` had RLS enabled but zero policies | 3 policies each added |
| 9 | `department_admin` had zero policies | Explicit dept-scoped SELECT policies on complaints, attachments, assignments, report_exports |
| 10 | `system_admin` had zero policies | Full SELECT + UPDATE policies on profiles, complaints; read on all tables |
| 11 | `notifications` had no RLS or policies | RLS enabled; own-recipient SELECT + UPDATE (mark-as-read) |
| 12 | `complaint_status_history` had no RLS or policies | RLS enabled; citizen-own and staff-read policies |
| 13 | `complaint_assignments` had no RLS or policies | RLS enabled; employee/supervisor/dept-admin/sysadmin policies |
| 14 | `department_category_rules` had no RLS or policies | RLS enabled; authenticated read |
| 15 | Storage used fragile `owner::text` comparison | Replaced with `(storage.foldername(name))[2]` path-based complaint_id lookup |
| 16 | `DepartmentCategoryRule` unique constraint was 2-field in SQL comment | `UNIQUE(department_id, category_id, jurisdiction_id)` in SQL |

---

## 10. Storage Policies Summary

| Policy | Operation | Actor | Path Check |
|--------|-----------|-------|------------|
| `storage: citizen upload submission` | INSERT | citizen | folder[3] = 'submission'; complaint owned by citizen |
| `storage: employee upload evidence` | INSERT | ground_level_employee | folder[3] IN ('verification','resolution'); complaint assigned |
| `storage: citizen read own` | SELECT | citizen | complaint owned by citizen |
| `storage: employee read assigned` | SELECT | ground_level_employee | complaint assigned to employee |
| `storage: supervisor read dept` | SELECT | supervisor, department_admin | complaint in actor's department |
| `storage: system_admin full read` | SELECT | system_admin | bucket-level |

**Bucket**: `complaint-media` — **private** (no public access). Signed URLs required for frontend rendering.

---

## 11. Seed / Reference Data

| Table | Rows Seeded | Data |
|-------|------------|------|
| `roles` | 5 | citizen, ground_level_employee, supervisor, department_admin, system_admin |
| `complaint_categories` | 8 | pothole, drainage, garbage, streetlight, road_damage, water_supply, sanitation, other |

**NOT seeded**: citizens, employees, supervisors, departments, jurisdictions, complaints, notifications. All operational data is created through the application.

---

## 12. Lifecycle Verification

```
SUBMITTED
    ↓ (routing service)
UNDER_VERIFICATION
    ↓ (supervisor assigns ground-level employee)
ASSIGNED
    ↓ (employee verifies — result: verified or invalid)
┌─ VERIFIED ────────────────────────────────────────────┐
│       ↓ (employee updates in-progress)                │
│   IN_PROGRESS                                         │
│       ↓ (employee marks resolved)                     │
│   RESOLVED ──── citizen rejects ──→ IN_PROGRESS       │
│       ↓ citizen confirms / auto-closure               │
│   CLOSED                                              │
└───────────────────────────────────────────────────────┘
└─ INVALID  ────────────────────────────────────────────┐
        ↓ (system/supervisor closes)                    │
    CLOSED                                              │
└───────────────────────────────────────────────────────┘
```

The `complaint_status_type` ENUM contains all 8 values: `submitted`, `under_verification`, `assigned`, `verified`, `invalid`, `in_progress`, `resolved`, `closed`.

---

## 13. AI Schema Verification

`complaint_classifications` table — AI (Phase 8) ONLY writes to:
- `complaint_id`, `detected_category_id`, `confidence_score`, `severity_level`, `severity_score`, `model_name`, `model_version`, `is_manual_override`, `classified_by`, `classified_at`

AI **NEVER** writes to:
- `complaints.status`
- `complaints.assigned_department_id`
- `complaints.assigned_employee_id`

This constraint is enforced at the Django application layer and confirmed in `backend/apps/complaints/ai/`.

---

## 14. SQL Migration Path

**File**: [`supabase/migrations/20260818115322_initial_schema.sql`](file:///c:/Users/Lenovo/Documents/civic/civicissuereport-backend/supabase/migrations/20260818115322_initial_schema.sql)

**Execution order within file**:
1. Extensions
2. ENUMs
3. Tables (dependency-ordered: roles → departments → jurisdictions → profiles → …)
4. Sequences
5. Security-definer helper functions
6. Triggers
7. `ALTER TABLE … ENABLE ROW LEVEL SECURITY` (all 24 tables)
8. RLS Policies
9. Indexes
10. Storage bucket + storage object policies
11. Reference seed data (roles, complaint_categories)

---

## 15. Django Files Requiring Modification (NOT YET MODIFIED)

| File | Change Required |
|------|----------------|
| [`backend/apps/users/models.py`](file:///c:/Users/Lenovo/Documents/civic/civicissuereport-backend/backend/apps/users/models.py) | Add `jurisdiction = ForeignKey(Jurisdiction, ...)` to `Profile` |
| [`backend/apps/complaints/models.py`](file:///c:/Users/Lenovo/Documents/civic/civicissuereport-backend/backend/apps/complaints/models.py) | Add `state = TextField(null=True)` and `google_maps_url = TextField(null=True)` to `Complaint` |
| [`backend/apps/departments/models.py`](file:///c:/Users/Lenovo/Documents/civic/civicissuereport-backend/backend/apps/departments/models.py) | Add `jurisdiction = ForeignKey(Jurisdiction, null=True)` to `DepartmentCategoryRule`; update `unique_together` |

---

## 16. Confirmation: Supabase NOT Modified

- ✅ No `supabase db push` executed
- ✅ No `supabase migration up` executed
- ✅ No Django `migrate` executed
- ✅ No SQL run against live Supabase project
- ✅ No users, departments, complaints, or fake data created
- ✅ Migration file is a static local file only

**WAITING FOR EXPLICIT APPROVAL TO PROCEED WITH SUPABASE DEPLOYMENT.**
