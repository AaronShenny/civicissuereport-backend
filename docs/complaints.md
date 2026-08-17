# Complaints Module Documentation

## Overview
The complaints module manages the end-to-end lifecycle of civic complaints: category listing, citizen submission, server-side numbering, automated department routing, supervisor assignment & reassignment, work queues, on-site physical verification, work progress updates, resolution submission with photographic proof via Supabase Storage, and status history tracking.

---

## 1. Complaint Workflow & Lifecycle

```text
CITIZEN SUBMITS COMPLAINT
           ↓ (status = 'submitted', citizen_id = request.user.id)
SYSTEM DEPARTMENT ROUTING
           ↓ (status = 'under_verification', assigned_department_id set, supervisor notified)
SUPERVISOR UNASSIGNED QUEUE
           ↓ (Supervisor reviews unassigned department complaints)
SUPERVISOR EMPLOYEE ASSIGNMENT
           ↓ (status = 'assigned', assigned_employee_id set, employee notified, assignment history created)
GROUND-LEVEL EMPLOYEE INSPECTION & VERIFICATION (Phase 5)
           │
           ├───────────────────────────────┐
           │                               │
        [VERIFIED]                      [INVALID]
           ↓                               ↓
   status = 'verified'             status = 'invalid'
           ↓ (Employee/Supervisor starts work) ↓ (system auto-closure)
   status = 'in_progress'          status = 'closed'
           ↓ (Progress updates & deadline changes)
   status = 'in_progress'
           ↓ (Resolution submitted with proof)
   status = 'resolved'
           │
   [Phase 7: Citizen Confirmation & Closure]
```

### Critical Architectural Distinctions
- **Department Routing** (`assigned_department_id`): Identifies the responsible government department using category rules and geographic location. Sets status to `UNDER_VERIFICATION`. Does NOT assign an employee.
- **Employee Assignment** (`assigned_employee_id`): Performed by the department's **Supervisor**. Assigns a specific Ground-Level Employee within the department. Sets status to `ASSIGNED`.
- **Physical Verification**: Performed exclusively by the **assigned Ground-Level Employee**. Submits `VERIFIED` or `INVALID` decision with inspection findings, mandatory remarks, and optional verification evidence.
- **VERIFIED vs IN_PROGRESS**: `VERIFIED` does **NOT** automatically mean `IN_PROGRESS`. Submitting a verified outcome leaves the complaint in `VERIFIED`. The transition `VERIFIED → IN_PROGRESS` occurs when an authorized actor initiates work or records the first progress update.
- **Progress & Resolution Authorization**:
  - **Assigned Ground-Level Employee** (`complaint.assigned_employee_id == user.id`) **OR**
  - **Authorized Department Supervisor** (`user.department_id == complaint.assigned_department_id`).
  - Cross-department supervisors, unassigned employees, citizens, and department admins are denied.
- **Resolution**: A complaint must be in `IN_PROGRESS` before it can be resolved. Direct `VERIFIED → RESOLVED` is rejected. Submitting resolution requires mandatory resolution details, mandatory resolution proof uploaded to Supabase Storage, transitions status to `RESOLVED`, and notifies the citizen and supervisor.

---

## 2. Role Responsibilities

| Role | Allowed Actions | Restricted Actions |
|---|---|---|
| **Citizen** | Submits complaints, views own submitted complaints, receives progress/resolution notifications. | Cannot route, assign, verify, resolve, or view internal staff queues. |
| **Supervisor** | Views unassigned department complaints, views all department complaints, assigns and reassigns ground-level employees within their department, records progress updates and resolves complaints for their department. | Cannot access or update complaints of other departments; cannot assign across departments; does NOT perform physical ground-level verification. |
| **Ground-Level Employee** | Views assigned complaints (`assigned_employee_id == user.id`), performs on-site inspection (`VERIFIED` / `INVALID`), records progress updates (`VERIFIED → IN_PROGRESS`), sets expected completion dates, submits resolution with proof (`IN_PROGRESS → RESOLVED`). | Cannot view unassigned complaints, cannot update/resolve complaints assigned to others, cannot update across departments. |
| **Department Admin** | Department-level dashboard and administration. | Not the primary assignment, verification, or resolution actor. |
| **System Admin** | System-wide administrative visibility and configuration. | N/A |

---

## 3. Department Routing Engine (`apps/complaints/routing.py`)

- **Inputs**: Complaint Category + Location Coordinates.
- **Rules Table**: `department_category_rules` (`category_id`, `department_id`, `priority_rank`, `is_active`).
- **Transitions**:
  1. Finds the highest-priority active department rule matching `complaint.category_id`.
  2. Sets `complaint.assigned_department_id = department.id`.
  3. Sets `complaint.status = ComplaintStatus.UNDER_VERIFICATION`.
  4. Records `complaint_status_history` (`old_status = 'submitted'`, `new_status = 'under_verification'`, `changed_by = None`).
  5. Generates in-app `Notification` for active Supervisors in that department.
- **Failure Behavior**: If no active rule matches, raises `RoutingFailureError` without making partial updates.

---

## 4. Supervisor Assignment & Reassignment (`apps/complaints/assignment.py`)

### Initial Assignment
- **Validation**:
  1. Caller is an active `Supervisor` belonging to a department.
  2. Complaint is currently in `UNDER_VERIFICATION` status and has `assigned_department_id == supervisor.department_id`.
  3. Complaint is not currently assigned (`assigned_employee_id IS NULL`).
  4. Target employee has role `ground_level_employee`, status `active`, and belongs to the same department.
- **Atomic Operations**:
  1. Sets `complaint.assigned_employee_id = employee.id`.
  2. Transitions `complaint.status = ComplaintStatus.ASSIGNED`.
  3. Inserts `complaint_assignments` history record.
  4. Inserts `complaint_status_history` record (`UNDER_VERIFICATION` → `ASSIGNED`, `changed_by = supervisor.id`).
  5. Creates in-app `Notification` for the assigned employee.

### Reassignment
- **Validation**:
  1. Caller is the department `Supervisor`.
  2. Complaint belongs to supervisor's department.
  3. Target new employee is an active `ground_level_employee` in the same department.
- **Atomic Operations**:
  1. Updates `complaint.assigned_employee_id = new_employee.id`.
  2. Preserves status as `ASSIGNED`.
  3. Inserts a **new** `complaint_assignments` history record (historical assignment records are never overwritten).
  4. Creates in-app `Notification` for the newly assigned employee.

---

## 5. Ground-Level Employee Verification (`apps/complaints/verification.py`)

### Authorization & Pre-Conditions
- Authenticated user has role `ground_level_employee` and `account_status == 'active'`.
- Primary access condition: `complaint.assigned_employee_id == authenticated_user.id`.
- Complaint status must be `ASSIGNED`.
- Complaint must not already have a record in `complaint_verifications`.

### Verification Outcomes & Status Transitions
1. **Outcome: `VERIFIED`**
   - Single transition (Employee action): `ASSIGNED` → `VERIFIED` (`changed_by = employee.id`, `change_reason = verification_remarks`).
   - Final status: `verified`.
2. **Outcome: `INVALID`**
   - Step 1 (Employee action): `ASSIGNED` → `INVALID` (`changed_by = employee.id`, `change_reason = verification_remarks`).
   - Step 2 (Automated system closure): `INVALID` → `CLOSED` (`changed_by = None`, `change_reason = 'Automatically closed due to invalid verification.'`).
   - Final status: `closed`.

---

## 6. Progress Updates & Work Progression (`apps/complaints/resolution.py`)

### Authorization
- **Allowed**: Assigned Ground-Level Employee (`assigned_employee_id == user.id`) OR Department Supervisor (`user.department_id == complaint.assigned_department_id`).
- **Denied**: Supervisors from other departments, unassigned employees, citizens, department admins.

### Work Initiation & Status Transition
- **Trigger**: First progress update submitted on a complaint with `status == 'verified'`.
- **Action**: Transitions `VERIFIED → IN_PROGRESS`.
- **Status History**: Exactly 1 record created (`old_status = 'verified'`, `new_status = 'in_progress'`, `changed_by = user.id`).
- **Subsequent Updates**: On complaints already `IN_PROGRESS`, records progress updates without duplicating status history rows.
- **Expected Completion Date**: Can be set/updated. If changed, generates a `DEADLINE_CHANGE` notification for the citizen.
- **Table**: Inserts row into `complaint_resolutions` with `is_final_resolution = false`.

---

## 7. Complaint Resolution (`apps/complaints/resolution.py`)

### Prerequisites & Submission Rules
- Complaint status must be `IN_PROGRESS` (direct `VERIFIED → RESOLVED` is rejected).
- Caller must be the assigned Ground-Level Employee (`assigned_employee_id == user.id`) OR Department Supervisor (`user.department_id == complaint.assigned_department_id`).
- `resolution_details` is mandatory.
- Resolution proof attachment (photo/document) is mandatory.

### Atomic Operations
1. Sets `complaint.status = ComplaintStatus.RESOLVED`.
2. Inserts `complaint_status_history` record (`old_status = 'in_progress'`, `new_status = 'resolved'`, `changed_by = user.id`, `change_reason = resolution_details`).
3. Inserts `complaint_attachments` record (`purpose = 'resolution_proof'`, `uploaded_by = user`).
4. Uploads resolution proof file to Supabase Storage (`complaints/{complaint_id}/resolution/{uuid}.ext`).
5. Inserts `complaint_resolutions` record (`is_final_resolution = true`, `resolution_proof_url = primary_path`).
6. Generates notifications (`trigger_event = 'resolution'`) for the citizen and the department supervisor.

---

## 8. API Endpoints Reference

### Citizen Endpoints
- `GET /api/v1/categories/` — List active complaint categories.
- `GET /api/v1/categories/<int:pk>/` — Category details.
- `GET /api/v1/complaints/` — List caller's submitted complaints.
- `POST /api/v1/complaints/` — Submit a new complaint (supports multipart evidence).
- `GET /api/v1/complaints/<uuid:pk>/` — Complaint detail (caller's own only).

### Department Routing Endpoint
- `POST /api/v1/complaints/<uuid:pk>/route/` — Triggers automated routing for a submitted complaint.

### Supervisor Endpoints
- `GET /api/v1/supervisor/complaints/unassigned/` — Unassigned queue for supervisor's department.
- `GET /api/v1/supervisor/complaints/` — All complaints in supervisor's department.
- `POST /api/v1/supervisor/complaints/<uuid:pk>/assign/` — Assign complaint to a Ground-Level Employee.
- `POST /api/v1/supervisor/complaints/<uuid:pk>/reassign/` — Reassign complaint to a different Ground-Level Employee.

### Ground-Level Employee & Work Progress Endpoints
- `GET /api/v1/employee/complaints/` — Complaints assigned to authenticated employee.
- `POST /api/v1/employee/complaints/<uuid:pk>/verify/` — Submit on-site physical verification (`verified` / `invalid`) [Assigned Employee Only].
- `GET /api/v1/employee/complaints/<uuid:pk>/verification/` — Retrieve verification record and inspection findings [Assigned Employee Only].
- `POST /api/v1/employee/complaints/<uuid:pk>/progress/` — Record progress update & start work (`VERIFIED → IN_PROGRESS`) [Assigned Employee OR Dept Supervisor].
- `POST /api/v1/employee/complaints/<uuid:pk>/resolve/` — Submit final resolution with proof (`IN_PROGRESS → RESOLVED`) [Assigned Employee OR Dept Supervisor].
- `GET /api/v1/employee/complaints/<uuid:pk>/resolutions/` — List all progress updates and final resolution entries [Assigned Employee OR Dept Supervisor].
