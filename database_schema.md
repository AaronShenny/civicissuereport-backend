# Smart Public Complaint Management System
# Database Schema

## 1. Purpose

This document defines the finalized PostgreSQL/Supabase database schema for the Smart Public Complaint Management System.

The schema is based on:

- The Elaborated User Stories
- The existing Supabase Database Design
- The required complaint lifecycle
- Role-based department access
- AI classification and priority assessment
- Duplicate complaint handling
- Location-based assignment
- Verification and resolution
- Notifications
- Dashboards and reports

The database is designed for Supabase PostgreSQL with Row Level Security (RLS), Supabase Auth, Supabase Storage, PostgreSQL functions/triggers, and optional PostGIS support.

---

# 2. Architecture

```text
Supabase Auth
     │
     ▼
auth.users
     │
     ▼
profiles
     │
     ├── roles
     ├── departments
     ├── permissions
     └── supervisor hierarchy

complaints
     │
     ├── categories
     ├── attachments
     ├── AI classifications
     ├── priority assessments
     ├── duplicate detection
     ├── assignments
     ├── verifications
     ├── resolutions
     ├── status history
     └── notifications

Spatial / Assignment
     │
     ├── jurisdictions
     ├── department-category mappings
     └── reference locations

Administration
     │
     ├── audit logs
     ├── login audit
     ├── user permissions
     └── report exports
```

---

# 3. Database Conventions

## 3.1 Primary Keys

- UUIDs use `gen_random_uuid()`.
- Master/reference tables may use `smallint` or other compact identifiers.
- Audit/event tables may use `bigint` identity columns.

## 3.2 Timestamps

Use:

```sql
timestamptz
```

with:

```sql
default now()
```

## 3.3 Authentication

Supabase `auth.users` is the source of truth for authentication.

Do not store passwords in application tables.

`public.profiles.id` must reference `auth.users.id`.

## 3.4 Security

RLS must be enabled on every application table.

Access must be based on:

- authenticated user
- role
- department
- supervisor hierarchy
- ownership of complaint
- assignment relationship

## 3.5 Spatial Data

PostGIS is recommended.

Complaint locations should use:

```sql
geography(Point, 4326)
```

Department/jurisdiction boundaries should use:

```sql
geography(MultiPolygon, 4326)
```

Latitude/longitude values may also be retained where useful for frontend/API compatibility.

---

# 4. ENUM Types

## 4.1 role_type

```text
citizen
ground_level_employee
supervisor
department_admin
system_admin
```

## 4.2 account_status_type

```text
active
inactive
pending_verification
```

## 4.3 complaint_status_type

```text
submitted
under_verification
verified
invalid
assigned
in_progress
resolved
closed
```

## 4.4 priority_category_type

```text
high
medium
low
```

## 4.5 verification_result_type

```text
verified
invalid
```

## 4.6 merge_status_type

```text
independent
linked
merged
rejected
```

## 4.7 notification_channel_type

```text
email
sms
in_app
```

## 4.8 notification_event_type

```text
submission
classification
verification
assignment
status_change
deadline_change
resolution
closure
```

## 4.9 attachment_purpose_type

```text
submission_evidence
verification_evidence
resolution_proof
```

## 4.10 severity_level_type

```text
low
medium
high
critical
```

## 4.11 review_status_type

```text
pending
in_review
completed
dismissed
```

## 4.12 delivery_status_type

```text
pending
queued
sent
failed
```

## 4.13 closure_confirmation_type

```text
pending
confirmed
rejected
auto_closed
```

---

# 5. User Management

## 5.1 roles

Stores the five system roles.

| Column | Type | Constraints |
|---|---|---|
| id | smallint | PK, identity |
| role_name | role_type | NOT NULL, UNIQUE |
| description | text | NULL |
| created_at | timestamptz | NOT NULL, default now() |

Seed values:

```text
citizen
ground_level_employee
supervisor
department_admin
system_admin
```

---

# 5.2 departments

Stores government departments/offices.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| name | text | NOT NULL, UNIQUE |
| description | text | NULL |
| is_active | boolean | NOT NULL, default true |
| created_at | timestamptz | NOT NULL, default now() |
| updated_at | timestamptz | NOT NULL, default now() |

---

# 5.3 jurisdictions

Defines geographical areas used for location-based assignment.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| name | text | NOT NULL |
| area_type | text | NOT NULL |
| boundary | geography(MultiPolygon,4326) | NOT NULL |
| is_active | boolean | NOT NULL, default true |
| created_at | timestamptz | NOT NULL, default now() |
| updated_at | timestamptz | NOT NULL, default now() |

Example `area_type` values:

```text
state
district
taluk
municipality
corporation
panchayat
ward
```

---

# 5.4 profiles

Application profile extending Supabase Auth.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, FK → auth.users(id), ON DELETE CASCADE |
| full_name | text | NOT NULL |
| email | text | UNIQUE, NULL |
| phone | text | UNIQUE, NULL |
| role_id | smallint | NOT NULL, FK → roles(id) |
| department_id | uuid | FK → departments(id), NULL |
| supervisor_id | uuid | FK → profiles(id), NULL |
| account_status | account_status_type | NOT NULL, default pending_verification |
| created_at | timestamptz | NOT NULL, default now() |
| updated_at | timestamptz | NOT NULL, default now() |

Rules:

- Citizens normally have no department.
- Staff must have a department.
- Ground-level employees may have a supervisor.
- Supervisors belong to a department.
- Department Admins belong to a department.
- System Admin has no department requirement.

---

# 5.5 user_permissions

Optional permission overrides.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| user_id | uuid | NOT NULL, FK → profiles(id) |
| permission_key | text | NOT NULL |
| is_granted | boolean | NOT NULL, default true |
| modified_by | uuid | FK → profiles(id), NULL |
| modified_at | timestamptz | NOT NULL, default now() |

Constraint:

```text
UNIQUE(user_id, permission_key)
```

---

# 5.6 login_audit_log

Stores login attempts.

| Column | Type | Constraints |
|---|---|---|
| id | bigint | PK, identity |
| user_id | uuid | FK → profiles(id), NULL |
| attempted_identifier | text | NULL |
| status | text | NOT NULL |
| ip_address | inet | NULL |
| device_info | text | NULL |
| created_at | timestamptz | NOT NULL, default now() |

Allowed status:

```text
success
failure
```

---

# 5.7 audit_logs

General administrative audit trail.

| Column | Type | Constraints |
|---|---|---|
| id | bigint | PK, identity |
| actor_id | uuid | FK → profiles(id), NULL |
| action | text | NOT NULL |
| entity_type | text | NOT NULL |
| entity_id | text | NULL |
| old_value | jsonb | NULL |
| new_value | jsonb | NULL |
| created_at | timestamptz | NOT NULL, default now() |

`entity_id` is text so the audit system can represent UUID, bigint, and smallint identifiers.

---

# 6. Complaint Master Data

## 6.1 complaint_categories

| Column | Type | Constraints |
|---|---|---|
| id | smallint | PK, identity |
| name | text | NOT NULL, UNIQUE |
| description | text | NULL |
| requires_attachment | boolean | NOT NULL, default false |
| is_active | boolean | NOT NULL, default true |
| created_at | timestamptz | NOT NULL, default now() |
| updated_at | timestamptz | NOT NULL, default now() |

Initial categories:

```text
pothole
drainage
garbage
streetlight
road_damage
water_supply
sanitation
other
```

---

# 6.2 department_category_rules

Maps complaint categories to responsible departments.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| department_id | uuid | NOT NULL, FK → departments(id) |
| category_id | smallint | NOT NULL, FK → complaint_categories(id) |
| priority_rank | integer | NOT NULL, default 1 |
| is_active | boolean | NOT NULL, default true |
| created_at | timestamptz | NOT NULL, default now() |

Constraint:

```text
UNIQUE(department_id, category_id)
```

This table allows:

```text
Pothole → Public Works
Garbage → Waste Management
Streetlight → Electrical
```

---

# 7. Complaints

## 7.1 complaints

The central complaint entity.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| complaint_number | text | NOT NULL, UNIQUE |
| citizen_id | uuid | NOT NULL, FK → profiles(id) |
| category_id | smallint | FK → complaint_categories(id), NULL |
| description | text | NOT NULL |
| location | geography(Point,4326) | NOT NULL |
| location_lat | numeric(9,6) | NOT NULL |
| location_lng | numeric(9,6) | NOT NULL |
| location_address | text | NULL |
| district | text | NULL |
| taluk | text | NULL |
| local_body | text | NULL |
| ward | text | NULL |
| inconvenience_details | text | NULL |
| expected_solution | text | NULL |
| status | complaint_status_type | NOT NULL, default submitted |
| priority_category | priority_category_type | NULL |
| priority_score | numeric(6,2) | NULL |
| severity_level | severity_level_type | NULL |
| severity_score | numeric(6,2) | NULL |
| assigned_department_id | uuid | FK → departments(id), NULL |
| assigned_employee_id | uuid | FK → profiles(id), NULL |
| main_complaint_id | uuid | FK → complaints(id), NULL |
| reporter_count | integer | NOT NULL, default 1 |
| expected_completion_date | date | NULL |
| closure_confirmation | closure_confirmation_type | NOT NULL, default pending |
| closure_due_at | timestamptz | NULL |
| submitted_at | timestamptz | NOT NULL, default now() |
| updated_at | timestamptz | NOT NULL, default now() |

Rules:

- `complaint_number` is generated by the backend/database.
- Newly submitted complaints start as `submitted`.
- Merged complaints reference `main_complaint_id`.
- Only the main complaint should be routed for action.
- `reporter_count` represents the number of citizens reporting the same issue.

---

# 8. Complaint Attachments

## 8.1 complaint_attachments

Actual files are stored in Supabase Storage.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| complaint_id | uuid | NOT NULL, FK → complaints(id) |
| file_path | text | NOT NULL |
| file_url | text | NULL |
| file_type | text | NOT NULL |
| mime_type | text | NULL |
| purpose | attachment_purpose_type | NOT NULL |
| uploaded_by | uuid | NOT NULL, FK → profiles(id) |
| uploaded_at | timestamptz | NOT NULL, default now() |

Allowed file types:

```text
photo
video
document
```

---

# 9. AI Classification

## 9.1 complaint_classifications

Stores every AI classification run and manual override.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| complaint_id | uuid | NOT NULL, FK → complaints(id) |
| detected_category_id | smallint | FK → complaint_categories(id) |
| confidence_score | numeric(5,2) | NULL |
| severity_level | severity_level_type | NULL |
| severity_score | numeric(6,2) | NULL |
| model_name | text | NULL |
| model_version | text | NULL |
| is_manual_override | boolean | NOT NULL, default false |
| classified_by | uuid | FK → profiles(id), NULL |
| classified_at | timestamptz | NOT NULL, default now() |

Confidence range:

```text
0–100
```

---

# 9.2 classification_review_tasks

Tracks low-confidence classifications requiring human review.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| complaint_id | uuid | NOT NULL, FK → complaints(id) |
| classification_id | uuid | NOT NULL, FK → complaint_classifications(id) |
| assigned_to | uuid | FK → profiles(id), NULL |
| reason | text | NOT NULL |
| status | review_status_type | NOT NULL, default pending |
| reviewed_by | uuid | FK → profiles(id), NULL |
| review_remarks | text | NULL |
| reviewed_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL, default now() |

---

# 10. Priority Assessment

## 10.1 priority_scoring_rules

Configurable weighted factors.

| Column | Type | Constraints |
|---|---|---|
| id | smallint | PK, identity |
| factor_name | text | NOT NULL, UNIQUE |
| weight | numeric(5,2) | NOT NULL |
| threshold_high | numeric(6,2) | NULL |
| threshold_medium | numeric(6,2) | NULL |
| is_active | boolean | NOT NULL, default true |
| updated_by | uuid | FK → profiles(id), NULL |
| updated_at | timestamptz | NOT NULL, default now() |

Example factors:

```text
high_traffic_area
near_school
near_hospital
severity
reporter_count
```

---

# 10.2 location_reference_points

Stores schools, hospitals and high-traffic locations.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| type | text | NOT NULL |
| name | text | NOT NULL |
| location | geography(Point,4326) | NOT NULL |
| location_lat | numeric(9,6) | NOT NULL |
| location_lng | numeric(9,6) | NOT NULL |
| created_at | timestamptz | NOT NULL, default now() |

Allowed types:

```text
school
hospital
high_traffic_area
```

---

# 10.3 complaint_priority_assessments

Stores every priority calculation.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| complaint_id | uuid | NOT NULL, FK → complaints(id) |
| high_traffic_area | boolean | NOT NULL, default false |
| near_school | boolean | NOT NULL, default false |
| near_hospital | boolean | NOT NULL, default false |
| severity_score | numeric(6,2) | NULL |
| reporter_count_factor | numeric(6,2) | NULL |
| total_priority_score | numeric(6,2) | NOT NULL |
| priority_category | priority_category_type | NOT NULL |
| assessed_at | timestamptz | NOT NULL, default now() |

Latest assessment is copied to:

```text
complaints.priority_score
complaints.priority_category
```

---

# 11. Duplicate Detection

## 11.1 complaint_duplicates

Stores possible duplicate matches.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| complaint_id | uuid | NOT NULL, FK → complaints(id) |
| matched_complaint_id | uuid | NOT NULL, FK → complaints(id) |
| match_criteria | jsonb | NULL |
| location_similarity_score | numeric(5,2) | NULL |
| text_similarity_score | numeric(5,2) | NULL |
| image_similarity_score | numeric(5,2) | NULL |
| similarity_score | numeric(5,2) | NULL |
| merge_status | merge_status_type | NOT NULL, default independent |
| reviewed_by | uuid | FK → profiles(id), NULL |
| review_remarks | text | NULL |
| reviewed_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL, default now() |

Duplicate comparison should consider:

```text
location
category
description
images
```

---

# 12. Complaint Assignment

## 12.1 complaint_assignments

Preserves assignment history.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| complaint_id | uuid | NOT NULL, FK → complaints(id) |
| department_id | uuid | NOT NULL, FK → departments(id) |
| employee_id | uuid | FK → profiles(id), NULL |
| assigned_by | uuid | FK → profiles(id), NULL |
| assignment_reason | text | NULL |
| assignment_date | timestamptz | NOT NULL, default now() |
| reassignment_reason | text | NULL |

Every assignment should create a new history row.

---

# 13. Complaint Verification

## 13.1 complaint_verifications

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| complaint_id | uuid | NOT NULL, FK → complaints(id) |
| verified_by | uuid | NOT NULL, FK → profiles(id) |
| site_inspection_notes | text | NULL |
| verification_result | verification_result_type | NOT NULL |
| verification_remarks | text | NOT NULL |
| verified_at | timestamptz | NOT NULL, default now() |

Rules:

- Only employees in the assigned department can verify.
- Remarks are mandatory.
- `verified` moves the complaint forward.
- `invalid` closes the complaint as invalid.

---

# 14. Complaint Resolution

## 14.1 complaint_resolutions

Stores progress and final resolution updates.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| complaint_id | uuid | NOT NULL, FK → complaints(id) |
| updated_by | uuid | NOT NULL, FK → profiles(id) |
| progress_update | text | NULL |
| remarks | text | NULL |
| expected_completion_date | date | NULL |
| resolution_details | text | NULL |
| resolution_proof_url | text | NULL |
| is_final_resolution | boolean | NOT NULL, default false |
| created_at | timestamptz | NOT NULL, default now() |

Rule:

```text
is_final_resolution = true
→ resolution_proof_url must exist
```

---

# 15. Complaint Status History

## 15.1 complaint_status_history

Complete lifecycle audit.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| complaint_id | uuid | NOT NULL, FK → complaints(id) |
| old_status | complaint_status_type | NULL |
| new_status | complaint_status_type | NOT NULL |
| changed_by | uuid | FK → profiles(id), NULL |
| change_reason | text | NULL |
| changed_at | timestamptz | NOT NULL, default now() |

Initial record:

```text
old_status = NULL
new_status = submitted
```

---

# 16. Notifications

## 16.1 notifications

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| recipient_id | uuid | NOT NULL, FK → profiles(id) |
| complaint_id | uuid | FK → complaints(id), NULL |
| trigger_event | notification_event_type | NOT NULL |
| channel | notification_channel_type | NOT NULL |
| message_content | text | NOT NULL |
| is_read | boolean | NOT NULL, default false |
| delivery_status | delivery_status_type | NOT NULL, default pending |
| delivery_attempts | integer | NOT NULL, default 0 |
| failure_reason | text | NULL |
| sent_at | timestamptz | NULL |
| last_attempt_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL, default now() |

---

# 16.2 notification_preferences

| Column | Type | Constraints |
|---|---|---|
| user_id | uuid | PK, FK → profiles(id) |
| email_enabled | boolean | NOT NULL, default true |
| sms_enabled | boolean | NOT NULL, default false |
| in_app_enabled | boolean | NOT NULL, default true |
| updated_at | timestamptz | NOT NULL, default now() |

---

# 17. Reports

## 17.1 report_exports

Tracks generated reports.

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| requested_by | uuid | NOT NULL, FK → profiles(id) |
| report_type | text | NOT NULL |
| filters | jsonb | NULL |
| file_format | text | NOT NULL |
| file_url | text | NULL |
| created_at | timestamptz | NOT NULL, default now() |

Allowed formats:

```text
excel
pdf
```

---

# 18. Dashboard Views

Dashboards should generally be SQL views rather than separate tables.

## 18.1 vw_citizen_dashboard

Provides:

- My complaints
- Pending count
- Completed count
- Complaint status
- Nearby public complaints
- Unread notifications

Filter:

```sql
citizen_id = auth.uid()
```

---

## 18.2 vw_department_dashboard

Provides:

- Total complaints
- Pending complaints
- Completed complaints
- High-priority complaints
- Overdue complaints
- Complaints by category
- Complaints by location
- Assigned complaints
- Employee performance

Department filtering must use the authenticated user's department.

---

## 18.3 vw_admin_dashboard

System-wide statistics:

- Total users
- Total complaints
- Pending complaints
- Resolved complaints
- Invalid complaints
- High-priority complaints
- Department performance
- Complaint category distribution
- Average resolution time

Only System Admins can access system-wide data.

---

## 18.4 vw_resolution_time_report

Calculates average resolution time.

Formula:

```text
closure timestamp - verification timestamp
```

Only resolved/closed complaints are included.

Invalid complaints are excluded.

---

# 19. Complaint Lifecycle

The standard lifecycle is:

```text
SUBMITTED
    │
    ▼
UNDER_VERIFICATION
    │
    ▼
ASSIGNED
    │
    ├──────────────► INVALID ───► CLOSED
    │
    ▼
VERIFIED
    │
    ▼
IN_PROGRESS
    │
    ▼
RESOLVED
    │
    ▼
CLOSED
```

Merged complaints:

```text
New Complaint
      │
      ▼
Duplicate Detection
      │
      ▼
MERGED
      │
      ▼
main_complaint_id
      │
      ▼
Main Complaint continues lifecycle
```

---

# 20. Database Triggers / Functions

The implementation should include database functions/triggers for the following.

## 20.1 New Auth User

After a new `auth.users` record:

```text
auth.users
    ↓
create profiles row
```

---

## 20.2 Complaint Number

Generate a unique human-readable complaint number.

Example:

```text
CMP-2026-000001
```

---

## 20.3 Status History

Whenever `complaints.status` changes:

```text
complaints
    ↓
complaint_status_history
```

---

## 20.4 Verification Status

When a verification is inserted:

```text
verified → complaint.status = verified
invalid  → complaint.status = invalid
```

---

## 20.5 Final Resolution

When a final resolution is inserted:

```text
is_final_resolution = true
        ↓
resolution_proof_url required
        ↓
complaint.status = resolved
```

---

## 20.6 Notifications

Status/lifecycle changes should create notification records.

Actual email/SMS dispatch should be handled outside the database, preferably by Edge Functions.

---

## 20.7 Updated Timestamps

Mutable tables should automatically update:

```text
updated_at
```

---

# 21. RLS Rules

RLS is mandatory.

## 21.1 Citizen

Citizen can:

```text
SELECT own complaints
INSERT own complaints
UPDATE permitted own complaint fields
SELECT own attachments
INSERT own attachments
SELECT own notifications
UPDATE own notifications as read
```

Citizens may also view restricted public nearby complaint information without exposing private citizen data.

---

## 21.2 Ground-Level Employee

A Ground-Level Employee can access complaints assigned to them.

Access is determined by:

```text
complaint.assigned_employee_id
=
employee.id

## 21.3 Supervisor

Supervisor can access:

- Complaints belonging to their department
- Complaints assigned to their team
- Assignment management within their department
- Verification/resolution monitoring
- Department dashboard data

---

## 21.4 Department Admin

Department Admin can access:

- All complaints in their department
- Employees in their department
- Supervisors in their department
- Department reports
- Department dashboard
- Department assignments

They cannot access another department's operational data.

---

## 21.5 System Admin

System Admin can access all system data and manage:

- Users
- Roles
- Permissions
- Departments
- Categories
- Priority rules
- Assignment rules
- Reports
- Audit logs

---

# 22. Required Indexes

Recommended indexes:

```text
profiles(role_id)
profiles(department_id)
profiles(supervisor_id)

complaints(citizen_id)
complaints(status)
complaints(category_id)
complaints(priority_category)
complaints(assigned_department_id)
complaints(assigned_employee_id)
complaints(main_complaint_id)
complaints(submitted_at)

complaint_attachments(complaint_id)

complaint_classifications(complaint_id)
classification_review_tasks(status)
classification_review_tasks(assigned_to)

complaint_priority_assessments(complaint_id)

complaint_duplicates(complaint_id)
complaint_duplicates(matched_complaint_id)

complaint_assignments(complaint_id)
complaint_assignments(department_id)
complaint_assignments(employee_id)

complaint_verifications(complaint_id)
complaint_verifications(verified_by)

complaint_resolutions(complaint_id)

complaint_status_history(complaint_id)
complaint_status_history(changed_at)

notifications(recipient_id)
notifications(complaint_id)
notifications(is_read)

audit_logs(actor_id)
audit_logs(entity_type, entity_id)
```

For PostGIS:

```sql
CREATE INDEX complaints_location_gist_idx
ON complaints
USING GIST (location);
```

and:

```sql
CREATE INDEX jurisdictions_boundary_gist_idx
ON jurisdictions
USING GIST (boundary);
```

---

# 23. Storage

Create a Supabase Storage bucket:

```text
complaint-media
```

Recommended object structure:

```text
complaints/
  {complaint_id}/
    submission/
    verification/
    resolution/
```

Do not store binary files directly in PostgreSQL.

Store the Storage object path in:

```text
complaint_attachments.file_path
```

---

# 24. Security Rules

Never expose:

- Password hashes
- Private citizen information
- Internal audit information
- Staff information to unauthorized citizens
- Other departments' complaint data

Use:

```text
auth.uid()
```

inside RLS policies.

Role checks should use a security-definer helper function where appropriate.

Example conceptual helpers:

```text
is_system_admin(user_id)
is_department_admin(user_id)
is_supervisor(user_id)
is_employee(user_id)
get_user_department(user_id)
```

---

# 25. Business Rules

## User Management

1. Email/phone must be unique.
2. Passwords are managed by Supabase Auth.
3. Every user has exactly one primary role.
4. Staff accounts require a department.
5. Deactivated users immediately lose access.
6. Role/permission changes are audited.

## Complaint Submission

1. Category, description and location are mandatory.
2. Every complaint receives a unique Complaint ID.
3. New complaints start as `submitted`.
4. Attachments are optional unless required by category.
5. Submission is recorded in audit history.

## Classification

1. AI classification produces category and severity.
2. Confidence is stored.
3. Low-confidence classifications create review tasks.
4. Manual overrides are preserved.
5. Classification history is never overwritten.

## Priority

1. Priority uses configurable weighted factors.
2. High/medium/low categories are calculated from the score.
3. Location and classification changes can trigger recalculation.
4. Priority history is preserved.

## Duplicate Detection

1. Compare location, category, description and images.
2. Preserve duplicate relationships.
3. Merged complaints retain `main_complaint_id`.
4. Reporter count increases after merging.
5. Only the main complaint is routed.

## Assignment

1. Assignment uses location and complaint category.
2. Department assignment is recorded.
3. Employee assignment is recorded.
4. Reassignments preserve history.
5. Departments cannot access other departments' complaints.

## Verification

1. Only authorized department employees can verify.
2. Verification remarks are mandatory.
3. Verified complaints continue to resolution.
4. Invalid complaints become invalid/closed according to workflow.
5. Verification is audited.

## Resolution

1. Assigned employee or authorized supervisor can update progress.
2. Expected completion dates are tracked.
3. Deadline changes are logged.
4. Final resolution requires proof.
5. Resolved complaints can move to closed after citizen confirmation or closure window.

## Notifications

1. Submission generates confirmation.
2. Status changes generate notifications.
3. Assignment generates department notification.
4. Deadline changes generate notifications.
5. Resolution generates notification.
6. Delivery failures are recorded.

---

# 26. AI / Backend Integration Boundaries

The database should store AI results but should not contain model-specific implementation logic.

Recommended flow:

```text
Complaint Created
      ↓
Edge Function / Backend Worker
      ↓
AI Classification
      ↓
complaint_classifications
      ↓
Priority Engine
      ↓
complaint_priority_assessments
      ↓
Duplicate Detection
      ↓
complaint_duplicates
      ↓
Department Assignment
      ↓
complaint_assignments
```

AI models can be replaced without redesigning the core complaint schema.

---

# 27. Recommended Implementation Order

The backend agent must not attempt the entire system in one step.

Implement in this order:

```text
Phase 1
Database extensions + ENUMs

Phase 2
Roles + Departments + Profiles

Phase 3
RLS foundation

Phase 4
Complaint categories + Complaints

Phase 5
Supabase Storage + Attachments

Phase 6
Complaint status history

Phase 7
Verification

Phase 8
Assignment

Phase 9
Resolution

Phase 10
AI Classification

Phase 11
Priority Assessment

Phase 12
Duplicate Detection

Phase 13
Notifications

Phase 14
Dashboards

Phase 15
Reports

Phase 16
Audit + Security hardening

Phase 17
Integration testing
```

Each phase should be completed and tested before the next phase begins.

---

# 28. MVP Priority

The recommended MVP should include:

```text
Authentication
Complaint submission
Photo upload
Location capture
Complaint classification
Location-based department assignment
Complaint verification
Complaint resolution
Complaint tracking
Basic notifications
Basic department dashboard
Basic admin management
```

The following can be added after the core workflow:

```text
Advanced duplicate detection
Advanced AI priority scoring
Advanced analytics
PDF/Excel reports
Advanced notification channels
```

---

# 29. Final Relationship Summary

```text
auth.users
    │
    └── profiles
          │
          ├── roles
          ├── departments
          ├── supervisors
          └── user_permissions

departments
    ├── department_category_rules
    ├── profiles
    ├── complaints
    └── complaint_assignments

complaints
    ├── complaint_categories
    ├── complaint_attachments
    ├── complaint_classifications
    ├── classification_review_tasks
    ├── complaint_priority_assessments
    ├── complaint_duplicates
    ├── complaint_assignments
    ├── complaint_verifications
    ├── complaint_resolutions
    ├── complaint_status_history
    ├── notifications
    └── complaints (main_complaint_id)

priority_scoring_rules
    └── complaint_priority_assessments

location_reference_points
    └── complaint_priority_assessments

jurisdictions
    └── location-based assignment

profiles
    ├── complaints
    ├── verifications
    ├── resolutions
    ├── notifications
    ├── audit_logs
    └── login_audit_log
```

---

# 30. Schema Freeze Rule

Once this schema is approved for implementation:

- Do not create duplicate tables for the same responsibility.
- Do not store passwords in public tables.
- Do not bypass RLS from the frontend.
- Do not store complaint media directly in PostgreSQL.
- Do not overwrite historical classification, assignment, verification, resolution, or status records.
- Do not implement role checks only in the frontend.
- Do not allow one department to access another department's data.
- Do not allow the AI layer to silently overwrite human decisions.
- Do not move to the next implementation phase until the current phase passes its tests.

This document is the database contract for the backend implementation.
