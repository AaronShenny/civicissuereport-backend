-- =============================================================================
-- Smart Public Complaint Management System
-- Supabase Initial Schema Migration
-- Timestamp: 20260818115322
-- =============================================================================
-- SECTIONS:
--   1. Extensions
--   2. ENUMs
--   3. Tables & Constraints
--   4. Sequences
--   5. Security-definer helper functions (for RLS — avoids recursion)
--   6. Triggers (database-owned only)
--   7. Row Level Security — ENABLE per table
--   8. RLS Policies
--   9. Indexes
--  10. Storage bucket + Storage object policies
--  11. Reference seed data (roles, complaint_categories)
-- =============================================================================


-- =============================================================================
-- 1. EXTENSIONS
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS postgis;


-- =============================================================================
-- 2. ENUMs
-- =============================================================================
CREATE TYPE role_type         AS ENUM ('citizen','ground_level_employee','supervisor','department_admin','system_admin');
CREATE TYPE account_status_type AS ENUM ('active','inactive','pending_verification');
CREATE TYPE complaint_status_type AS ENUM ('submitted','under_verification','verified','invalid','assigned','in_progress','resolved','closed');
CREATE TYPE priority_category_type AS ENUM ('high','medium','low');
CREATE TYPE verification_result_type AS ENUM ('verified','invalid');
CREATE TYPE merge_status_type  AS ENUM ('independent','linked','merged','rejected');
CREATE TYPE notification_channel_type AS ENUM ('email','sms','in_app');
CREATE TYPE notification_event_type  AS ENUM ('submission','classification','verification','assignment','status_change','deadline_change','resolution','closure');
CREATE TYPE attachment_purpose_type  AS ENUM ('submission_evidence','verification_evidence','resolution_proof');
CREATE TYPE attachment_file_type     AS ENUM ('photo','video','document');
CREATE TYPE severity_level_type      AS ENUM ('low','medium','high','critical');
CREATE TYPE review_status_type       AS ENUM ('pending','in_review','completed','dismissed');
CREATE TYPE delivery_status_type     AS ENUM ('pending','queued','sent','failed');
CREATE TYPE closure_confirmation_type AS ENUM ('pending','confirmed','rejected','auto_closed');


-- =============================================================================
-- 3. TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- roles — reference / seed data
-- ---------------------------------------------------------------------------
CREATE TABLE public.roles (
    id          smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name   role_type  NOT NULL UNIQUE,
    description text,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- departments
-- ---------------------------------------------------------------------------
CREATE TABLE public.departments (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text        NOT NULL UNIQUE,
    description text,
    is_active   boolean     NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- jurisdictions  (districts, taluks, etc.)
-- ---------------------------------------------------------------------------
CREATE TABLE public.jurisdictions (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text        NOT NULL,
    area_type   text        NOT NULL,   -- 'district', 'taluk', etc.
    boundary    geography(MultiPolygon,4326) NOT NULL,
    is_active   boolean     NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- profiles  — FK to auth.users; role, department, jurisdiction
-- ---------------------------------------------------------------------------
CREATE TABLE public.profiles (
    id              uuid            PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name       text            NOT NULL,
    email           text            UNIQUE,
    phone           text            UNIQUE,
    role_id         smallint        NOT NULL REFERENCES public.roles(id),
    department_id   uuid            REFERENCES public.departments(id),
    supervisor_id   uuid            REFERENCES public.profiles(id),
    -- jurisdiction_id: district in which this supervisor/employee operates.
    -- NULL for citizens and system_admins.
    jurisdiction_id uuid            REFERENCES public.jurisdictions(id),
    account_status  account_status_type NOT NULL DEFAULT 'pending_verification',
    created_at      timestamptz     NOT NULL DEFAULT now(),
    updated_at      timestamptz     NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- user_permissions
-- ---------------------------------------------------------------------------
CREATE TABLE public.user_permissions (
    id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        uuid        NOT NULL REFERENCES public.profiles(id),
    permission_key text        NOT NULL,
    is_granted     boolean     NOT NULL DEFAULT true,
    modified_by    uuid        REFERENCES public.profiles(id),
    modified_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, permission_key)
);

-- ---------------------------------------------------------------------------
-- login_audit_log
-- ---------------------------------------------------------------------------
CREATE TABLE public.login_audit_log (
    id                   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id              uuid        REFERENCES public.profiles(id),
    attempted_identifier text,
    status               text        NOT NULL,
    ip_address           inet,
    device_info          text,
    created_at           timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- audit_logs
-- ---------------------------------------------------------------------------
CREATE TABLE public.audit_logs (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id    uuid        REFERENCES public.profiles(id),
    action      text        NOT NULL,
    entity_type text        NOT NULL,
    entity_id   text,
    old_value   jsonb,
    new_value   jsonb,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- complaint_categories — reference / seed data
-- ---------------------------------------------------------------------------
CREATE TABLE public.complaint_categories (
    id                  smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name                text        NOT NULL UNIQUE,
    description         text,
    requires_attachment boolean     NOT NULL DEFAULT false,
    is_active           boolean     NOT NULL DEFAULT true,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- department_category_rules
--   Maps (category, optional jurisdiction) → responsible department.
--   jurisdiction_id = NULL means the rule applies system-wide for that category.
--   jurisdiction_id = <district uuid> means the rule is district-specific.
-- ---------------------------------------------------------------------------
CREATE TABLE public.department_category_rules (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id   uuid        NOT NULL REFERENCES public.departments(id),
    category_id     smallint    NOT NULL REFERENCES public.complaint_categories(id),
    jurisdiction_id uuid        REFERENCES public.jurisdictions(id),   -- NULL = global fallback
    priority_rank   integer     NOT NULL DEFAULT 1,
    is_active       boolean     NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (department_id, category_id, jurisdiction_id)
);

-- ---------------------------------------------------------------------------
-- complaint_number_seq — DJANGO-OWNED number generation uses this sequence.
-- ---------------------------------------------------------------------------
CREATE SEQUENCE public.complaint_number_seq START 1;

-- ---------------------------------------------------------------------------
-- complaints
-- ---------------------------------------------------------------------------
CREATE TABLE public.complaints (
    id                      uuid                  PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_number        text                  NOT NULL UNIQUE,
    citizen_id              uuid                  NOT NULL REFERENCES public.profiles(id),
    category_id             smallint              REFERENCES public.complaint_categories(id),
    description             text                  NOT NULL,
    -- Citizen-supplied Google Maps link; coordinates extracted by backend.
    google_maps_url         text,
    location                geography(Point,4326) NOT NULL,
    location_lat            numeric(9,6)          NOT NULL,
    location_lng            numeric(9,6)          NOT NULL,
    location_address        text,
    -- Citizen-supplied administrative location (no reverse geocoding).
    state                   text,
    district                text,
    taluk                   text,
    local_body              text,
    ward                    text,
    inconvenience_details   text,
    expected_solution       text,
    status                  complaint_status_type NOT NULL DEFAULT 'submitted',
    -- Lifecycle:
    --   submitted → under_verification → assigned → verified → in_progress
    --   → resolved → closed
    -- Invalidation:   assigned → invalid → closed
    -- Citizen reject: resolved → in_progress
    -- Citizen confirm / auto: resolved → closed
    priority_category       priority_category_type,
    priority_score          numeric(6,2),
    severity_level          severity_level_type,
    severity_score          numeric(6,2),
    -- AI must never write directly to these assignment columns.
    assigned_department_id  uuid                  REFERENCES public.departments(id),
    assigned_employee_id    uuid                  REFERENCES public.profiles(id),
    main_complaint_id       uuid                  REFERENCES public.complaints(id),
    reporter_count          integer               NOT NULL DEFAULT 1,
    expected_completion_date date,
    closure_confirmation    closure_confirmation_type NOT NULL DEFAULT 'pending',
    closure_due_at          timestamptz,
    submitted_at            timestamptz           NOT NULL DEFAULT now(),
    updated_at              timestamptz           NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- complaint_attachments
-- ---------------------------------------------------------------------------
CREATE TABLE public.complaint_attachments (
    id           uuid                   PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id uuid                   NOT NULL REFERENCES public.complaints(id),
    file_path    text                   NOT NULL,
    file_url     text,
    file_type    text                   NOT NULL,
    mime_type    text,
    purpose      attachment_purpose_type NOT NULL,
    uploaded_by  uuid                   NOT NULL REFERENCES public.profiles(id),
    uploaded_at  timestamptz            NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- complaint_classifications  (AI severity — Phase 8)
-- ---------------------------------------------------------------------------
CREATE TABLE public.complaint_classifications (
    id                  uuid                PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id        uuid                NOT NULL REFERENCES public.complaints(id),
    detected_category_id smallint           REFERENCES public.complaint_categories(id),
    confidence_score    numeric(5,2),
    severity_level      severity_level_type,
    severity_score      numeric(6,2),
    model_name          text,
    model_version       text,
    is_manual_override  boolean             NOT NULL DEFAULT false,
    classified_by       uuid                REFERENCES public.profiles(id),
    classified_at       timestamptz         NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- classification_review_tasks
-- ---------------------------------------------------------------------------
CREATE TABLE public.classification_review_tasks (
    id                uuid             PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id      uuid             NOT NULL REFERENCES public.complaints(id),
    classification_id uuid             NOT NULL REFERENCES public.complaint_classifications(id),
    assigned_to       uuid             REFERENCES public.profiles(id),
    reason            text             NOT NULL,
    status            review_status_type NOT NULL DEFAULT 'pending',
    reviewed_by       uuid             REFERENCES public.profiles(id),
    review_remarks    text,
    reviewed_at       timestamptz,
    created_at        timestamptz      NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- priority_scoring_rules
-- ---------------------------------------------------------------------------
CREATE TABLE public.priority_scoring_rules (
    id               smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    factor_name      text        NOT NULL UNIQUE,
    weight           numeric(5,2) NOT NULL,
    threshold_high   numeric(6,2),
    threshold_medium numeric(6,2),
    is_active        boolean     NOT NULL DEFAULT true,
    updated_by       uuid        REFERENCES public.profiles(id),
    updated_at       timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- location_reference_points
-- ---------------------------------------------------------------------------
CREATE TABLE public.location_reference_points (
    id           uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    type         text         NOT NULL,
    name         text         NOT NULL,
    location     geography(Point,4326) NOT NULL,
    location_lat numeric(9,6) NOT NULL,
    location_lng numeric(9,6) NOT NULL,
    created_at   timestamptz  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- complaint_priority_assessments
-- ---------------------------------------------------------------------------
CREATE TABLE public.complaint_priority_assessments (
    id                   uuid                   PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id         uuid                   NOT NULL REFERENCES public.complaints(id),
    high_traffic_area    boolean                NOT NULL DEFAULT false,
    near_school          boolean                NOT NULL DEFAULT false,
    near_hospital        boolean                NOT NULL DEFAULT false,
    severity_score       numeric(6,2),
    reporter_count_factor numeric(6,2),
    total_priority_score numeric(6,2)           NOT NULL,
    priority_category    priority_category_type NOT NULL,
    assessed_at          timestamptz            NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- complaint_duplicates
-- ---------------------------------------------------------------------------
CREATE TABLE public.complaint_duplicates (
    id                      uuid             PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id            uuid             NOT NULL REFERENCES public.complaints(id),
    matched_complaint_id    uuid             NOT NULL REFERENCES public.complaints(id),
    match_criteria          jsonb,
    location_similarity_score numeric(5,2),
    text_similarity_score   numeric(5,2),
    image_similarity_score  numeric(5,2),
    similarity_score        numeric(5,2),
    merge_status            merge_status_type NOT NULL DEFAULT 'independent',
    reviewed_by             uuid             REFERENCES public.profiles(id),
    review_remarks          text,
    reviewed_at             timestamptz,
    created_at              timestamptz      NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- complaint_assignments
-- ---------------------------------------------------------------------------
CREATE TABLE public.complaint_assignments (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id        uuid        NOT NULL REFERENCES public.complaints(id),
    department_id       uuid        NOT NULL REFERENCES public.departments(id),
    employee_id         uuid        REFERENCES public.profiles(id),
    assigned_by         uuid        REFERENCES public.profiles(id),
    assignment_reason   text,
    assignment_date     timestamptz NOT NULL DEFAULT now(),
    reassignment_reason text
);

-- ---------------------------------------------------------------------------
-- complaint_verifications
-- ---------------------------------------------------------------------------
CREATE TABLE public.complaint_verifications (
    id                   uuid                    PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id         uuid                    NOT NULL REFERENCES public.complaints(id),
    verified_by          uuid                    NOT NULL REFERENCES public.profiles(id),
    site_inspection_notes text,
    verification_result  verification_result_type NOT NULL,
    verification_remarks text                    NOT NULL,
    verified_at          timestamptz             NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- complaint_resolutions
-- ---------------------------------------------------------------------------
CREATE TABLE public.complaint_resolutions (
    id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id            uuid        NOT NULL REFERENCES public.complaints(id),
    updated_by              uuid        NOT NULL REFERENCES public.profiles(id),
    progress_update         text,
    remarks                 text,
    expected_completion_date date,
    resolution_details      text,
    resolution_proof_url    text,
    is_final_resolution     boolean     NOT NULL DEFAULT false,
    created_at              timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- complaint_status_history   (DJANGO-OWNED writes — no DB trigger)
-- ---------------------------------------------------------------------------
CREATE TABLE public.complaint_status_history (
    id            uuid                  PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id  uuid                  NOT NULL REFERENCES public.complaints(id),
    old_status    complaint_status_type,
    new_status    complaint_status_type NOT NULL,
    changed_by    uuid                  REFERENCES public.profiles(id),
    change_reason text,
    changed_at    timestamptz           NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- notifications
-- ---------------------------------------------------------------------------
CREATE TABLE public.notifications (
    id               uuid                    PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id     uuid                    NOT NULL REFERENCES public.profiles(id),
    complaint_id     uuid                    REFERENCES public.complaints(id),
    trigger_event    notification_event_type NOT NULL,
    channel          notification_channel_type NOT NULL,
    message_content  text                    NOT NULL,
    is_read          boolean                 NOT NULL DEFAULT false,
    delivery_status  delivery_status_type    NOT NULL DEFAULT 'pending',
    delivery_attempts integer                NOT NULL DEFAULT 0,
    failure_reason   text,
    sent_at          timestamptz,
    last_attempt_at  timestamptz,
    created_at       timestamptz             NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- notification_preferences
-- ---------------------------------------------------------------------------
CREATE TABLE public.notification_preferences (
    user_id         uuid        PRIMARY KEY REFERENCES public.profiles(id),
    email_enabled   boolean     NOT NULL DEFAULT true,
    sms_enabled     boolean     NOT NULL DEFAULT false,
    in_app_enabled  boolean     NOT NULL DEFAULT true,
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- report_exports
-- ---------------------------------------------------------------------------
CREATE TABLE public.report_exports (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    requested_by uuid        NOT NULL REFERENCES public.profiles(id),
    report_type  text        NOT NULL,
    filters      jsonb,
    file_format  text        NOT NULL,
    file_url     text,
    created_at   timestamptz NOT NULL DEFAULT now()
);


-- =============================================================================
-- 5. SECURITY-DEFINER HELPER FUNCTIONS
--    These are called inside RLS USING() clauses.
--    SECURITY DEFINER + search_path = '' prevents privilege escalation.
--    They avoid recursive policy evaluation by bypassing RLS when checking roles.
-- =============================================================================

-- Returns the role_name of the currently authenticated user.
-- Called by RLS policies that need to branch on role.
CREATE OR REPLACE FUNCTION public.auth_user_role()
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT r.role_name::text
    FROM   public.profiles p
    JOIN   public.roles    r ON r.id = p.role_id
    WHERE  p.id = auth.uid()
$$;

-- Returns the department_id of the currently authenticated user.
CREATE OR REPLACE FUNCTION public.auth_user_department_id()
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT department_id
    FROM   public.profiles
    WHERE  id = auth.uid()
$$;

-- Returns the jurisdiction_id of the currently authenticated user.
CREATE OR REPLACE FUNCTION public.auth_user_jurisdiction_id()
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT jurisdiction_id
    FROM   public.profiles
    WHERE  id = auth.uid()
$$;

-- Returns the name of the jurisdiction (district) the authenticated user belongs to.
CREATE OR REPLACE FUNCTION public.auth_user_jurisdiction_name()
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT j.name
    FROM   public.profiles  p
    JOIN   public.jurisdictions j ON j.id = p.jurisdiction_id
    WHERE  p.id = auth.uid()
$$;


-- =============================================================================
-- 6. TRIGGERS (DATABASE-OWNED ONLY)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 6a. updated_at auto-timestamp
--     Safe to duplicate in DB and Django; DB version protects direct SQL edits.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER set_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER set_complaints_updated_at
    BEFORE UPDATE ON public.complaints
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 6b. auth.users → public.profiles auto-provisioning (DATABASE-OWNED)
--     Creates a minimal citizen profile on Supabase Auth sign-up.
--     role_id is resolved by name, never hard-coded as an integer.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    citizen_role_id smallint;
BEGIN
    SELECT id INTO citizen_role_id
    FROM   public.roles
    WHERE  role_name = 'citizen';

    INSERT INTO public.profiles (id, full_name, email, phone, role_id)
    VALUES (
        new.id,
        COALESCE(new.raw_user_meta_data->>'full_name', 'New User'),
        new.email,
        new.phone,
        citizen_role_id
    );
    RETURN new;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();

-- ---------------------------------------------------------------------------
-- TRIGGER OWNERSHIP NOTES (not implemented as DB triggers):
--   complaint_number      → DJANGO-OWNED (apps/complaints/number.py)
--   complaint_status_history → DJANGO-OWNED (assignment/verification/resolution/closure services)
--   verification_status   → DJANGO-OWNED (verification.py)
--   resolution_status     → DJANGO-OWNED (resolution.py / closure.py)
--   notifications         → DJANGO-OWNED (notification service)
-- ---------------------------------------------------------------------------


-- =============================================================================
-- 7. ROW LEVEL SECURITY — ENABLE ON ALL TABLES
--    Every table has an explicit RLS decision below.
-- =============================================================================
ALTER TABLE public.roles                       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jurisdictions               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles                    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_permissions            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.login_audit_log             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaint_categories        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.department_category_rules   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaints                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaint_attachments       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaint_classifications   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.classification_review_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.priority_scoring_rules      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.location_reference_points   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaint_priority_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaint_duplicates        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaint_assignments       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaint_verifications     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaint_resolutions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaint_status_history    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_preferences    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_exports              ENABLE ROW LEVEL SECURITY;


-- =============================================================================
-- 8. RLS POLICIES
--
-- Design conventions:
--   • All policies that inspect other rows use security-definer helper functions
--     (auth_user_role, auth_user_department_id, etc.) to avoid recursion.
--   • Role names are compared as text strings, never as integer IDs.
--   • "service_role" (the Django backend JWT) bypasses RLS automatically in
--     Supabase when using the service_role key — no explicit bypass needed.
--   • Policies labelled [staff] cover employees, supervisors, dept_admin,
--     system_admin (any non-citizen).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- roles  — public read-only reference data
-- ---------------------------------------------------------------------------
CREATE POLICY "roles: public read"
    ON public.roles FOR SELECT
    USING (true);

-- ---------------------------------------------------------------------------
-- departments  — public read-only reference data
-- ---------------------------------------------------------------------------
CREATE POLICY "departments: public read"
    ON public.departments FOR SELECT
    USING (true);

-- ---------------------------------------------------------------------------
-- jurisdictions  — public read-only reference data
-- ---------------------------------------------------------------------------
CREATE POLICY "jurisdictions: public read"
    ON public.jurisdictions FOR SELECT
    USING (true);

-- ---------------------------------------------------------------------------
-- complaint_categories  — public read-only reference data
-- ---------------------------------------------------------------------------
CREATE POLICY "categories: public read"
    ON public.complaint_categories FOR SELECT
    USING (true);

-- ---------------------------------------------------------------------------
-- department_category_rules  — read by any authenticated user (routing lookup)
-- ---------------------------------------------------------------------------
CREATE POLICY "dcr: authenticated read"
    ON public.department_category_rules FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- ---------------------------------------------------------------------------
-- profiles
--   • Any user reads their own row.
--   • Staff reads all profiles in their department (needed for assignment UI).
--   • System admin reads all profiles.
--   • NO recursive subquery — uses SECURITY DEFINER helpers.
-- ---------------------------------------------------------------------------
CREATE POLICY "profiles: own row read"
    ON public.profiles FOR SELECT
    USING (id = auth.uid());

CREATE POLICY "profiles: own row update"
    ON public.profiles FOR UPDATE
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- Staff can read profiles within their department or their own jurisdiction.
CREATE POLICY "profiles: staff reads department peers"
    ON public.profiles FOR SELECT
    USING (
        public.auth_user_role() IN ('ground_level_employee','supervisor','department_admin')
        AND department_id = public.auth_user_department_id()
    );

-- System admin reads everyone.
CREATE POLICY "profiles: system_admin full read"
    ON public.profiles FOR SELECT
    USING (public.auth_user_role() = 'system_admin');

-- System admin can update any profile (e.g. change account_status).
CREATE POLICY "profiles: system_admin full update"
    ON public.profiles FOR UPDATE
    USING (public.auth_user_role() = 'system_admin');

-- ---------------------------------------------------------------------------
-- user_permissions
--   • System admin manages all.
--   • Users read their own permissions.
-- ---------------------------------------------------------------------------
CREATE POLICY "user_permissions: own read"
    ON public.user_permissions FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "user_permissions: system_admin full"
    ON public.user_permissions FOR ALL
    USING (public.auth_user_role() = 'system_admin');

-- ---------------------------------------------------------------------------
-- login_audit_log  — write-only for anonymous/auth flow; system admin reads
-- ---------------------------------------------------------------------------
CREATE POLICY "login_audit_log: system_admin read"
    ON public.login_audit_log FOR SELECT
    USING (public.auth_user_role() = 'system_admin');

CREATE POLICY "login_audit_log: own read"
    ON public.login_audit_log FOR SELECT
    USING (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- audit_logs  — system admin read; append via service role (backend)
-- ---------------------------------------------------------------------------
CREATE POLICY "audit_logs: system_admin read"
    ON public.audit_logs FOR SELECT
    USING (public.auth_user_role() = 'system_admin');

-- ---------------------------------------------------------------------------
-- complaints
--   Citizens:   SELECT/INSERT own complaints.
--   Employees:  SELECT their specifically assigned complaint.
--   Supervisors: SELECT complaints for their department AND their district.
--   Dept Admin: SELECT all complaints in their department.
--   System Admin: SELECT all.
--   UPDATE/DELETE: handled by Django backend using service_role key (bypasses RLS).
-- ---------------------------------------------------------------------------
CREATE POLICY "complaints: citizen own read"
    ON public.complaints FOR SELECT
    USING (citizen_id = auth.uid());

CREATE POLICY "complaints: citizen insert"
    ON public.complaints FOR INSERT
    WITH CHECK (
        citizen_id = auth.uid()
        AND public.auth_user_role() = 'citizen'
    );

CREATE POLICY "complaints: employee assigned read"
    ON public.complaints FOR SELECT
    USING (
        assigned_employee_id = auth.uid()
        AND public.auth_user_role() = 'ground_level_employee'
    );

-- Supervisor sees complaints routed to their department AND their district.
CREATE POLICY "complaints: supervisor department+district read"
    ON public.complaints FOR SELECT
    USING (
        public.auth_user_role() = 'supervisor'
        AND assigned_department_id = public.auth_user_department_id()
        AND district = public.auth_user_jurisdiction_name()
    );

-- Department admin sees all complaints in their department.
CREATE POLICY "complaints: dept_admin department read"
    ON public.complaints FOR SELECT
    USING (
        public.auth_user_role() = 'department_admin'
        AND assigned_department_id = public.auth_user_department_id()
    );

-- System admin sees everything.
CREATE POLICY "complaints: system_admin full read"
    ON public.complaints FOR SELECT
    USING (public.auth_user_role() = 'system_admin');

-- ---------------------------------------------------------------------------
-- complaint_attachments
--   Citizens:   read attachments on their own complaints.
--   Employees:  read attachments on their assigned complaints.
--   Supervisors/Dept Admin: read attachments on department complaints.
--   System Admin: read all.
--   INSERT: citizen for submission; employee for verification/resolution evidence.
-- ---------------------------------------------------------------------------
CREATE POLICY "attachments: citizen own complaint"
    ON public.complaint_attachments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id = complaint_id
              AND c.citizen_id = auth.uid()
        )
    );

CREATE POLICY "attachments: employee assigned"
    ON public.complaint_attachments FOR SELECT
    USING (
        public.auth_user_role() = 'ground_level_employee'
        AND EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id = complaint_id
              AND c.assigned_employee_id = auth.uid()
        )
    );

CREATE POLICY "attachments: supervisor dept+district"
    ON public.complaint_attachments FOR SELECT
    USING (
        public.auth_user_role() = 'supervisor'
        AND EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id = complaint_id
              AND c.assigned_department_id = public.auth_user_department_id()
              AND c.district = public.auth_user_jurisdiction_name()
        )
    );

CREATE POLICY "attachments: dept_admin department"
    ON public.complaint_attachments FOR SELECT
    USING (
        public.auth_user_role() = 'department_admin'
        AND EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id = complaint_id
              AND c.assigned_department_id = public.auth_user_department_id()
        )
    );

CREATE POLICY "attachments: system_admin full read"
    ON public.complaint_attachments FOR SELECT
    USING (public.auth_user_role() = 'system_admin');

CREATE POLICY "attachments: citizen insert submission"
    ON public.complaint_attachments FOR INSERT
    WITH CHECK (
        uploaded_by = auth.uid()
        AND public.auth_user_role() = 'citizen'
        AND purpose = 'submission_evidence'
    );

CREATE POLICY "attachments: employee insert evidence"
    ON public.complaint_attachments FOR INSERT
    WITH CHECK (
        uploaded_by = auth.uid()
        AND public.auth_user_role() = 'ground_level_employee'
        AND purpose IN ('verification_evidence', 'resolution_proof')
    );

-- ---------------------------------------------------------------------------
-- complaint_classifications  (AI writes via service_role; staff reads)
--   Citizens read classification results on their own complaints.
--   Staff read classifications for accessible complaints.
-- ---------------------------------------------------------------------------
CREATE POLICY "classifications: citizen own complaint"
    ON public.complaint_classifications FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id = complaint_id AND c.citizen_id = auth.uid()
        )
    );

CREATE POLICY "classifications: staff read"
    ON public.complaint_classifications FOR SELECT
    USING (
        public.auth_user_role() IN ('ground_level_employee','supervisor','department_admin','system_admin')
    );

-- ---------------------------------------------------------------------------
-- classification_review_tasks  (assigned staff reads)
-- ---------------------------------------------------------------------------
CREATE POLICY "review_tasks: assigned read"
    ON public.classification_review_tasks FOR SELECT
    USING (
        assigned_to = auth.uid()
        OR public.auth_user_role() IN ('department_admin','system_admin')
    );

-- ---------------------------------------------------------------------------
-- priority_scoring_rules  — read by staff; written by system_admin via service role
-- ---------------------------------------------------------------------------
CREATE POLICY "priority_rules: staff read"
    ON public.priority_scoring_rules FOR SELECT
    USING (
        public.auth_user_role() IN ('supervisor','department_admin','system_admin')
    );

-- ---------------------------------------------------------------------------
-- location_reference_points  — read-only for all authenticated users
-- ---------------------------------------------------------------------------
CREATE POLICY "location_refs: authenticated read"
    ON public.location_reference_points FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- ---------------------------------------------------------------------------
-- complaint_priority_assessments  — same access as the parent complaint
-- ---------------------------------------------------------------------------
CREATE POLICY "priority_assessments: citizen own"
    ON public.complaint_priority_assessments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id = complaint_id AND c.citizen_id = auth.uid()
        )
    );

CREATE POLICY "priority_assessments: staff read"
    ON public.complaint_priority_assessments FOR SELECT
    USING (
        public.auth_user_role() IN ('ground_level_employee','supervisor','department_admin','system_admin')
    );

-- ---------------------------------------------------------------------------
-- complaint_duplicates  — staff only
-- ---------------------------------------------------------------------------
CREATE POLICY "duplicates: staff read"
    ON public.complaint_duplicates FOR SELECT
    USING (
        public.auth_user_role() IN ('supervisor','department_admin','system_admin')
    );

-- ---------------------------------------------------------------------------
-- complaint_assignments  — staff reads within scope
-- ---------------------------------------------------------------------------
CREATE POLICY "assignments: employee own"
    ON public.complaint_assignments FOR SELECT
    USING (employee_id = auth.uid());

CREATE POLICY "assignments: supervisor dept"
    ON public.complaint_assignments FOR SELECT
    USING (
        public.auth_user_role() = 'supervisor'
        AND department_id = public.auth_user_department_id()
    );

CREATE POLICY "assignments: dept_admin"
    ON public.complaint_assignments FOR SELECT
    USING (
        public.auth_user_role() = 'department_admin'
        AND department_id = public.auth_user_department_id()
    );

CREATE POLICY "assignments: system_admin"
    ON public.complaint_assignments FOR SELECT
    USING (public.auth_user_role() = 'system_admin');

-- ---------------------------------------------------------------------------
-- complaint_verifications  — employee who verified; supervisor/admin
-- ---------------------------------------------------------------------------
CREATE POLICY "verifications: verifier read"
    ON public.complaint_verifications FOR SELECT
    USING (verified_by = auth.uid());

CREATE POLICY "verifications: supervisor dept"
    ON public.complaint_verifications FOR SELECT
    USING (
        public.auth_user_role() IN ('supervisor','department_admin','system_admin')
        AND EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id = complaint_id
              AND (
                  public.auth_user_role() = 'system_admin'
                  OR c.assigned_department_id = public.auth_user_department_id()
              )
        )
    );

CREATE POLICY "verifications: citizen own complaint"
    ON public.complaint_verifications FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id = complaint_id AND c.citizen_id = auth.uid()
        )
    );

-- ---------------------------------------------------------------------------
-- complaint_resolutions  — citizen can see resolution on own complaint; staff
-- ---------------------------------------------------------------------------
CREATE POLICY "resolutions: citizen own"
    ON public.complaint_resolutions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id = complaint_id AND c.citizen_id = auth.uid()
        )
    );

CREATE POLICY "resolutions: staff read"
    ON public.complaint_resolutions FOR SELECT
    USING (
        public.auth_user_role() IN ('ground_level_employee','supervisor','department_admin','system_admin')
    );

-- ---------------------------------------------------------------------------
-- complaint_status_history  — citizens read own; staff reads assigned scope
-- ---------------------------------------------------------------------------
CREATE POLICY "status_history: citizen own"
    ON public.complaint_status_history FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id = complaint_id AND c.citizen_id = auth.uid()
        )
    );

CREATE POLICY "status_history: staff read"
    ON public.complaint_status_history FOR SELECT
    USING (
        public.auth_user_role() IN ('ground_level_employee','supervisor','department_admin','system_admin')
    );

-- ---------------------------------------------------------------------------
-- notifications  — each user reads only their own notifications
-- ---------------------------------------------------------------------------
CREATE POLICY "notifications: own read"
    ON public.notifications FOR SELECT
    USING (recipient_id = auth.uid());

CREATE POLICY "notifications: own mark read"
    ON public.notifications FOR UPDATE
    USING (recipient_id = auth.uid())
    WITH CHECK (recipient_id = auth.uid());

-- ---------------------------------------------------------------------------
-- notification_preferences  — own row only
-- ---------------------------------------------------------------------------
CREATE POLICY "notif_prefs: own read"
    ON public.notification_preferences FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "notif_prefs: own update"
    ON public.notification_preferences FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "notif_prefs: own insert"
    ON public.notification_preferences FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- report_exports  — own exports; dept_admin/system_admin reads all
-- ---------------------------------------------------------------------------
CREATE POLICY "report_exports: own read"
    ON public.report_exports FOR SELECT
    USING (requested_by = auth.uid());

CREATE POLICY "report_exports: admin read"
    ON public.report_exports FOR SELECT
    USING (
        public.auth_user_role() IN ('department_admin','system_admin')
    );


-- =============================================================================
-- 9. INDEXES
-- =============================================================================
CREATE INDEX profiles_role_id_idx         ON public.profiles(role_id);
CREATE INDEX profiles_department_id_idx   ON public.profiles(department_id);
CREATE INDEX profiles_jurisdiction_id_idx ON public.profiles(jurisdiction_id);
CREATE INDEX profiles_supervisor_id_idx   ON public.profiles(supervisor_id);
CREATE INDEX profiles_account_status_idx  ON public.profiles(account_status);

CREATE INDEX complaints_citizen_id_idx           ON public.complaints(citizen_id);
CREATE INDEX complaints_status_idx               ON public.complaints(status);
CREATE INDEX complaints_category_id_idx          ON public.complaints(category_id);
CREATE INDEX complaints_priority_category_idx    ON public.complaints(priority_category);
CREATE INDEX complaints_assigned_department_idx  ON public.complaints(assigned_department_id);
CREATE INDEX complaints_assigned_employee_idx    ON public.complaints(assigned_employee_id);
CREATE INDEX complaints_main_complaint_id_idx    ON public.complaints(main_complaint_id);
CREATE INDEX complaints_submitted_at_idx         ON public.complaints(submitted_at);
CREATE INDEX complaints_district_idx             ON public.complaints(district);
CREATE INDEX complaints_location_gist_idx        ON public.complaints USING GIST (location);

CREATE INDEX jurisdictions_boundary_gist_idx ON public.jurisdictions USING GIST (boundary);

CREATE INDEX attachments_complaint_id_idx    ON public.complaint_attachments(complaint_id);

CREATE INDEX classifications_complaint_id_idx ON public.complaint_classifications(complaint_id);
CREATE INDEX review_tasks_status_idx          ON public.classification_review_tasks(status);
CREATE INDEX review_tasks_assigned_to_idx     ON public.classification_review_tasks(assigned_to);

CREATE INDEX priority_assessments_complaint_idx ON public.complaint_priority_assessments(complaint_id);

CREATE INDEX duplicates_complaint_id_idx        ON public.complaint_duplicates(complaint_id);
CREATE INDEX duplicates_matched_id_idx          ON public.complaint_duplicates(matched_complaint_id);

CREATE INDEX assignments_complaint_id_idx       ON public.complaint_assignments(complaint_id);
CREATE INDEX assignments_department_id_idx      ON public.complaint_assignments(department_id);
CREATE INDEX assignments_employee_id_idx        ON public.complaint_assignments(employee_id);

CREATE INDEX verifications_complaint_id_idx     ON public.complaint_verifications(complaint_id);
CREATE INDEX resolutions_complaint_id_idx       ON public.complaint_resolutions(complaint_id);

CREATE INDEX status_history_complaint_id_idx    ON public.complaint_status_history(complaint_id);
CREATE INDEX status_history_changed_at_idx      ON public.complaint_status_history(changed_at);

CREATE INDEX notifications_recipient_id_idx     ON public.notifications(recipient_id);
CREATE INDEX notifications_complaint_id_idx     ON public.notifications(complaint_id);
CREATE INDEX notifications_is_read_idx          ON public.notifications(is_read);

CREATE INDEX audit_logs_actor_id_idx            ON public.audit_logs(actor_id);
CREATE INDEX audit_logs_entity_idx              ON public.audit_logs(entity_type, entity_id);

CREATE INDEX dcr_category_id_idx                ON public.department_category_rules(category_id);
CREATE INDEX dcr_jurisdiction_id_idx            ON public.department_category_rules(jurisdiction_id);


-- =============================================================================
-- 10. STORAGE — complaint-media bucket + policies
-- =============================================================================

-- Create private bucket.
INSERT INTO storage.buckets (id, name, public)
VALUES ('complaint-media', 'complaint-media', false)
ON CONFLICT (id) DO NOTHING;

-- Storage path convention:
--   complaints/{complaint_id}/submission/{filename}
--   complaints/{complaint_id}/verification/{filename}
--   complaints/{complaint_id}/resolution/{filename}
--
-- (storage.foldername(name))[1] = 'complaints'
-- (storage.foldername(name))[2] = complaint_id

-- Citizens can upload submission evidence to their own complaint folder.
CREATE POLICY "storage: citizen upload submission"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'complaint-media'
        AND (storage.foldername(name))[1] = 'complaints'
        AND (storage.foldername(name))[3] = 'submission'
        AND public.auth_user_role() = 'citizen'
        AND EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id::text = (storage.foldername(name))[2]
              AND c.citizen_id = auth.uid()
        )
    );

-- Employees can upload verification/resolution evidence.
CREATE POLICY "storage: employee upload evidence"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'complaint-media'
        AND (storage.foldername(name))[1] = 'complaints'
        AND (storage.foldername(name))[3] IN ('verification','resolution')
        AND public.auth_user_role() = 'ground_level_employee'
        AND EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id::text = (storage.foldername(name))[2]
              AND c.assigned_employee_id = auth.uid()
        )
    );

-- Citizens can read media on their own complaints.
CREATE POLICY "storage: citizen read own"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'complaint-media'
        AND (storage.foldername(name))[1] = 'complaints'
        AND public.auth_user_role() = 'citizen'
        AND EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id::text = (storage.foldername(name))[2]
              AND c.citizen_id = auth.uid()
        )
    );

-- Employees can read media on their assigned complaints.
CREATE POLICY "storage: employee read assigned"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'complaint-media'
        AND (storage.foldername(name))[1] = 'complaints'
        AND public.auth_user_role() = 'ground_level_employee'
        AND EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id::text = (storage.foldername(name))[2]
              AND c.assigned_employee_id = auth.uid()
        )
    );

-- Supervisors/dept admins read media within their department scope.
CREATE POLICY "storage: supervisor read dept"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'complaint-media'
        AND (storage.foldername(name))[1] = 'complaints'
        AND public.auth_user_role() IN ('supervisor','department_admin')
        AND EXISTS (
            SELECT 1 FROM public.complaints c
            WHERE c.id::text = (storage.foldername(name))[2]
              AND c.assigned_department_id = public.auth_user_department_id()
        )
    );

-- System admin reads all media.
CREATE POLICY "storage: system_admin full read"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'complaint-media'
        AND public.auth_user_role() = 'system_admin'
    );


-- =============================================================================
-- 11. REFERENCE SEED DATA
--     Only roles and complaint categories — no fake users, complaints, or staff.
-- =============================================================================

INSERT INTO public.roles (role_name, description) VALUES
    ('citizen',               'A member of the public who submits civic complaints.'),
    ('ground_level_employee', 'Field staff who verify and resolve complaints on-site.'),
    ('supervisor',            'Department supervisor who manages employees and oversees complaint resolution.'),
    ('department_admin',      'Administrative head of a government department.'),
    ('system_admin',          'Platform-level administrator with full access.');

INSERT INTO public.complaint_categories (name, description, requires_attachment, is_active) VALUES
    ('pothole',        'Road surface potholes and craters.',              false, true),
    ('drainage',       'Blocked or broken drainage systems.',             false, true),
    ('garbage',        'Uncollected garbage or overflowing bins.',        false, true),
    ('streetlight',    'Damaged or non-functioning street lights.',       false, true),
    ('road_damage',    'General road damage not classified as pothole.',  false, true),
    ('water_supply',   'Water supply interruption or quality issues.',    false, true),
    ('sanitation',     'Public sanitation and sewage issues.',            false, true),
    ('other',          'Complaints not covered by existing categories.',  false, true);
