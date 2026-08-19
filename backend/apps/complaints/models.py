"""
apps/complaints/models.py

Phase 3 models:
  - ComplaintCategory   → public.complaint_categories
  - Complaint           → public.complaints
  - ComplaintAttachment → public.complaint_attachments
  - ComplaintStatusHistory → public.complaint_status_history

All tables are managed = False (Supabase owns the schema).
Django reads and writes these tables; it does NOT create or drop them.

PostGIS note:
  The 'location' column is geography(Point,4326) in PostgreSQL.
  We represent it as TextField here (storing WKT or the serialised form),
  because GeoDjango/PostGIS requires GDAL which is not guaranteed to be
  installed in every development environment.  The actual PostGIS geography
  column already exists in the database.  For writes, the service layer
  builds the ST_Point(...) expression using a raw SQL fragment.
  latitude/longitude are stored separately in numeric columns (location_lat,
  location_lng) for frontend/API compatibility — these are the primary way
  the API reads and writes location data.
"""

from django.db import models
from apps.users.models import Profile, Department


# ---------------------------------------------------------------------------
# ENUM choices as Python constants
# (the DB enforces these via PostgreSQL ENUM types)
# ---------------------------------------------------------------------------

class ComplaintStatus(models.TextChoices):
    SUBMITTED = 'submitted', 'Submitted'
    UNDER_VERIFICATION = 'under_verification', 'Under Verification'
    ASSIGNED = 'assigned', 'Assigned'
    VERIFIED = 'verified', 'Verified'
    IN_PROGRESS = 'in_progress', 'In Progress'
    RESOLVED = 'resolved', 'Resolved'
    CLOSED = 'closed', 'Closed'
    INVALID = 'invalid', 'Invalid'


class PriorityCategory(models.TextChoices):
    HIGH = 'high', 'High'
    MEDIUM = 'medium', 'Medium'
    LOW = 'low', 'Low'


class SeverityLevel(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'


class ClosureConfirmation(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    REJECTED = 'rejected', 'Rejected'
    AUTO_CLOSED = 'auto_closed', 'Auto Closed'


class AttachmentPurpose(models.TextChoices):
    SUBMISSION_EVIDENCE = 'submission_evidence', 'Submission Evidence'
    VERIFICATION_EVIDENCE = 'verification_evidence', 'Verification Evidence'
    RESOLUTION_PROOF = 'resolution_proof', 'Resolution Proof'


class AttachmentFileType(models.TextChoices):
    PHOTO = 'photo', 'Photo'
    VIDEO = 'video', 'Video'
    DOCUMENT = 'document', 'Document'


class NotificationEventType(models.TextChoices):
    SUBMISSION = 'submission', 'Submission'
    CLASSIFICATION = 'classification', 'Classification'
    VERIFICATION = 'verification', 'Verification'
    ASSIGNMENT = 'assignment', 'Assignment'
    STATUS_CHANGE = 'status_change', 'Status Change'
    DEADLINE_CHANGE = 'deadline_change', 'Deadline Change'
    RESOLUTION = 'resolution', 'Resolution'
    CLOSURE = 'closure', 'Closure'


class VerificationResultType(models.TextChoices):
    VERIFIED = 'verified', 'Verified'
    INVALID = 'invalid', 'Invalid'


class NotificationChannelType(models.TextChoices):
    EMAIL = 'email', 'Email'
    SMS = 'sms', 'SMS'
    IN_APP = 'in_app', 'In App'


class DeliveryStatusType(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'


class ReviewStatusType(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_REVIEW = 'in_review', 'In Review'
    COMPLETED = 'completed', 'Completed'
    DISMISSED = 'dismissed', 'Dismissed'


# ---------------------------------------------------------------------------
# ComplaintCategory
# ---------------------------------------------------------------------------

class ComplaintCategory(models.Model):
    """
    Maps to public.complaint_categories.
    Seed data: pothole, drainage, garbage, streetlight, road_damage,
               water_supply, sanitation, other.
    """

    # PK is smallint identity in DB.
    id = models.SmallAutoField(primary_key=True)
    name = models.TextField(unique=True)
    description = models.TextField(null=True, blank=True)
    requires_attachment = models.BooleanField(default=False)
    base_priority = models.CharField(max_length=16, choices=PriorityCategory.choices, default=PriorityCategory.MEDIUM)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'complaint_categories'

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Complaint
# ---------------------------------------------------------------------------

class Complaint(models.Model):
    """
    Maps to public.complaints — the central complaint entity.

    Fields that the backend controls (never trusted from client input):
      - complaint_number  (generated server-side: CMP-YYYY-NNNNNN)
      - citizen_id        (from verified JWT)
      - status            (starts as 'submitted')
      - reporter_count    (starts as 1)
      - assigned_department_id  (Phase 4+)
      - assigned_employee_id    (Phase 4+)
      - priority_*              (Phase 5+)
      - severity_*              (Phase 5+)
      - main_complaint_id       (Phase 6+)
    """

    id = models.UUIDField(primary_key=True)
    complaint_number = models.TextField(unique=True)

    citizen = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        db_column='citizen_id',
        related_name='complaints',
    )
    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.PROTECT,
        db_column='category_id',
        null=True,
        blank=True,
    )

    description = models.TextField()

    # Location stored as text (WKT) here; actual DB column is geography(Point,4326).
    # We use location_lat / location_lng for all application-layer logic.
    location = models.TextField()
    location_lat = models.DecimalField(max_digits=9, decimal_places=6)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6)
    location_address = models.TextField(null=True, blank=True)

    district = models.TextField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    google_maps_url = models.TextField(null=True, blank=True)
    taluk = models.TextField(null=True, blank=True)
    local_body = models.TextField(null=True, blank=True)
    ward = models.TextField(null=True, blank=True)

    inconvenience_details = models.TextField(null=True, blank=True)
    expected_solution = models.TextField(null=True, blank=True)

    status = models.CharField(
        max_length=32,
        choices=ComplaintStatus.choices,
        default=ComplaintStatus.SUBMITTED,
    )

    # Priority / severity — populated by AI/priority engine in later phases.
    priority_category = models.CharField(
        max_length=16,
        choices=PriorityCategory.choices,
        null=True,
        blank=True,
    )
    priority_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    severity_level = models.CharField(
        max_length=16,
        choices=SeverityLevel.choices,
        null=True,
        blank=True,
    )
    severity_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # Assignment — populated during Phase 4+ assignment workflow.
    assigned_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        db_column='assigned_department_id',
        null=True,
        blank=True,
        related_name='assigned_complaints',
    )
    assigned_employee = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        db_column='assigned_employee_id',
        null=True,
        blank=True,
        related_name='assigned_complaints',
    )

    # Duplicate detection — Phase 6+.
    main_complaint = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        db_column='main_complaint_id',
        null=True,
        blank=True,
        related_name='duplicates',
    )
    reporter_count = models.IntegerField(default=1)

    expected_completion_date = models.DateField(null=True, blank=True)

    closure_confirmation = models.CharField(
        max_length=16,
        choices=ClosureConfirmation.choices,
        default=ClosureConfirmation.PENDING,
    )
    closure_due_at = models.DateTimeField(null=True, blank=True)

    submitted_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'complaints'

    def __str__(self):
        return f'{self.complaint_number} ({self.status})'


# ---------------------------------------------------------------------------
# ComplaintAttachment
# ---------------------------------------------------------------------------

class ComplaintAttachment(models.Model):
    """
    Maps to public.complaint_attachments.
    Actual files live in Supabase Storage (complaint-media bucket).
    Only the Storage object path is stored here.
    """

    id = models.UUIDField(primary_key=True)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        db_column='complaint_id',
        related_name='attachments',
    )

    # Path within the Supabase Storage bucket, e.g.:
    #   complaints/{complaint_id}/submission/photo-01.jpg
    file_path = models.TextField()

    # Public/signed URL (optional; may be regenerated on demand).
    file_url = models.TextField(null=True, blank=True)

    file_type = models.CharField(
        max_length=16,
        choices=AttachmentFileType.choices,
    )
    mime_type = models.TextField(null=True, blank=True)

    purpose = models.CharField(
        max_length=32,
        choices=AttachmentPurpose.choices,
    )

    uploaded_by = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        db_column='uploaded_by',
        related_name='uploaded_attachments',
    )
    uploaded_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'complaint_attachments'

    def __str__(self):
        return f'{self.complaint_id} / {self.file_path}'


# ---------------------------------------------------------------------------
# ComplaintStatusHistory
# ---------------------------------------------------------------------------

class ComplaintStatusHistory(models.Model):
    """
    Maps to public.complaint_status_history.
    Complete lifecycle audit — one row per status transition.

    Initial row on submission:
      old_status = NULL
      new_status = 'submitted'
    """

    id = models.UUIDField(primary_key=True)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        db_column='complaint_id',
        related_name='status_history',
    )
    old_status = models.CharField(
        max_length=32,
        choices=ComplaintStatus.choices,
        null=True,
        blank=True,
    )
    new_status = models.CharField(
        max_length=32,
        choices=ComplaintStatus.choices,
    )
    changed_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        db_column='changed_by',
        null=True,
        blank=True,
        related_name='status_changes',
    )
    change_reason = models.TextField(null=True, blank=True)
    changed_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'complaint_status_history'

    def __str__(self):
        return f'{self.complaint_id}: {self.old_status} → {self.new_status}'


# ---------------------------------------------------------------------------
# ComplaintAssignment
# ---------------------------------------------------------------------------

class ComplaintAssignment(models.Model):
    """
    Maps to public.complaint_assignments.
    Preserves full assignment and reassignment audit history.
    """

    id = models.UUIDField(primary_key=True)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        db_column='complaint_id',
        related_name='assignments',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        db_column='department_id',
        related_name='assignments',
    )
    employee = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        db_column='employee_id',
        null=True,
        blank=True,
        related_name='assigned_tasks',
    )
    assigned_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        db_column='assigned_by',
        null=True,
        blank=True,
        related_name='initiated_assignments',
    )
    assignment_reason = models.TextField(null=True, blank=True)
    assignment_date = models.DateTimeField()
    reassignment_reason = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'complaint_assignments'

    def __str__(self):
        return f'{self.complaint_id} -> {self.employee_id} ({self.assignment_date})'


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class Notification(models.Model):
    """
    Maps to public.notifications.
    Stores notification records for system events (routing, assignment, status change).
    """

    id = models.UUIDField(primary_key=True)
    recipient = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        db_column='recipient_id',
        related_name='notifications',
    )
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        db_column='complaint_id',
        null=True,
        blank=True,
        related_name='notifications',
    )
    trigger_event = models.CharField(
        max_length=32,
        choices=NotificationEventType.choices,
    )
    channel = models.CharField(
        max_length=16,
        choices=NotificationChannelType.choices,
        default=NotificationChannelType.IN_APP,
    )
    message_content = models.TextField()
    is_read = models.BooleanField(default=False)
    delivery_status = models.CharField(
        max_length=16,
        choices=DeliveryStatusType.choices,
        default=DeliveryStatusType.PENDING,
    )
    delivery_attempts = models.IntegerField(default=0)
    failure_reason = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'notifications'

    def __str__(self):
        return f'Notification to {self.recipient_id} ({self.trigger_event})'


# ---------------------------------------------------------------------------
# ComplaintVerification
# ---------------------------------------------------------------------------

class ComplaintVerification(models.Model):
    """
    Maps to public.complaint_verifications.
    Stores ground-level inspection findings, mandatory remarks, and verification decision.
    """

    id = models.UUIDField(primary_key=True)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        db_column='complaint_id',
        related_name='verifications',
    )
    verified_by = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        db_column='verified_by',
        related_name='completed_verifications',
    )
    site_inspection_notes = models.TextField(null=True, blank=True)
    verification_result = models.CharField(
        max_length=16,
        choices=VerificationResultType.choices,
    )
    verification_remarks = models.TextField()
    verified_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'complaint_verifications'

    def __str__(self):
        return f'{self.complaint_id}: {self.verification_result} by {self.verified_by_id}'


# ---------------------------------------------------------------------------
# ComplaintResolution
# ---------------------------------------------------------------------------

class ComplaintResolution(models.Model):
    """
    Maps to public.complaint_resolutions.
    Stores interim progress updates, expected completion dates, and final resolution evidence.
    """

    id = models.UUIDField(primary_key=True)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        db_column='complaint_id',
        related_name='resolutions',
    )
    updated_by = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        db_column='updated_by',
        related_name='submitted_resolutions',
    )
    progress_update = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    expected_completion_date = models.DateField(null=True, blank=True)
    resolution_details = models.TextField(null=True, blank=True)
    resolution_proof_url = models.TextField(null=True, blank=True)
    is_final_resolution = models.BooleanField(default=False)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'complaint_resolutions'

    def __str__(self):
        return f'{self.complaint_id}: {"Final Resolution" if self.is_final_resolution else "Progress Update"} by {self.updated_by_id}'


# ---------------------------------------------------------------------------
# ComplaintClassification (Phase 8: AI Severity Assessment)
# ---------------------------------------------------------------------------

class ComplaintClassification(models.Model):
    """
    Maps to public.complaint_classifications.

    Stores every AI classification run and manual override.
    Records are NEVER overwritten — each AI run inserts a new row.
    The latest record (by classified_at) is the authoritative classification.

    Phase 8 populates:
        severity_level, severity_score, confidence_score, model_name,
        model_version, is_manual_override=False.

    Future phases may populate:
        detected_category_id (AI category classification — Phase 9+).
    """

    id = models.UUIDField(primary_key=True)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        db_column='complaint_id',
        related_name='classifications',
    )
    # detected_category_id is intentionally retained for future category AI.
    # Phase 8 inserts NULL here.
    detected_category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.SET_NULL,
        db_column='detected_category_id',
        null=True,
        blank=True,
        related_name='ai_classifications',
    )
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    severity_level = models.CharField(
        max_length=16,
        choices=SeverityLevel.choices,
        null=True,
        blank=True,
    )
    severity_score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    model_name = models.TextField(null=True, blank=True)
    model_version = models.TextField(null=True, blank=True)
    is_manual_override = models.BooleanField(default=False)
    classified_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        db_column='classified_by',
        null=True,
        blank=True,
        related_name='performed_classifications',
    )
    classified_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'complaint_classifications'

    def __str__(self):
        return (
            f'{self.complaint_id}: severity={self.severity_level} '
            f'score={self.severity_score} confidence={self.confidence_score} '
            f'at {self.classified_at}'
        )


# ---------------------------------------------------------------------------
# ClassificationReviewTask (Phase 8: low-confidence review routing)
# ---------------------------------------------------------------------------

class ClassificationReviewTask(models.Model):
    """
    Maps to public.classification_review_tasks.

    Created automatically when an AI classification confidence score falls
    below the configured AI_CONFIDENCE_THRESHOLD.

    The review workflow UI is deferred to a later phase.
    """

    id = models.UUIDField(primary_key=True)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        db_column='complaint_id',
        related_name='review_tasks',
    )
    classification = models.ForeignKey(
        ComplaintClassification,
        on_delete=models.CASCADE,
        db_column='classification_id',
        related_name='review_tasks',
    )
    assigned_to = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        db_column='assigned_to',
        null=True,
        blank=True,
        related_name='assigned_review_tasks',
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=ReviewStatusType.choices,
        default=ReviewStatusType.PENDING,
    )
    reviewed_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        db_column='reviewed_by',
        null=True,
        blank=True,
        related_name='completed_review_tasks',
    )
    review_remarks = models.TextField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'classification_review_tasks'

    def __str__(self):
        return f'ReviewTask for {self.complaint_id} [{self.status}]'

