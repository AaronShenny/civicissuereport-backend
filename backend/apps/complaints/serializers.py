"""
apps/complaints/serializers.py

Serializers for complaints, categories, attachments, assignments, and notifications.

Security rules reflected in serializer design:
  - citizen_id, complaint_number, status, priority, assigned_department_id,
    assigned_employee_id, reporter_count are READ-ONLY — the backend sets them.
  - latitude/longitude are write-only on input; returned as numbers in responses.
  - Sensitive citizen fields (phone, email) are not exposed in complaint responses.
"""

from rest_framework import serializers
from apps.complaints.location import extract_coordinates_from_url, LocationExtractionError
from apps.complaints.models import (
    Complaint,
    ComplaintCategory,
    ComplaintAttachment,
    ComplaintStatusHistory,
    ComplaintAssignment,
    ComplaintVerification,
    ComplaintResolution,
    Notification,
)
from apps.users.serializers import StaffProfileSummarySerializer, DepartmentSummarySerializer


class ComplaintCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintCategory
        fields = [
            'id', 'name', 'description',
            'requires_attachment', 'is_active',
        ]


class ComplaintAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintAttachment
        fields = [
            'id', 'file_path', 'file_url',
            'file_type', 'mime_type', 'purpose',
            'uploaded_at',
        ]
        read_only_fields = fields


class ComplaintStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True, default='System')

    class Meta:
        model = ComplaintStatusHistory
        fields = [
            'id', 'old_status', 'new_status',
            'changed_by_name', 'change_reason', 'changed_at',
        ]
        read_only_fields = fields


class ComplaintAssignmentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True, default=None)
    assigned_by_name = serializers.CharField(source='assigned_by.full_name', read_only=True, default='System')

    class Meta:
        model = ComplaintAssignment
        fields = [
            'id', 'complaint_id', 'department_id', 'department_name',
            'employee_id', 'employee_name', 'assigned_by_id', 'assigned_by_name',
            'assignment_reason', 'reassignment_reason', 'assignment_date',
        ]
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient_id', 'complaint_id',
            'trigger_event', 'channel', 'message_content',
            'is_read', 'created_at',
        ]
        read_only_fields = fields


class ComplaintListSerializer(serializers.ModelSerializer):
    """Compact view for citizen list endpoint."""
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = Complaint
        fields = [
            'id', 'complaint_number', 'category_name',
            'status', 'submitted_at', 'location_address',
            'location_lat', 'location_lng',
        ]


class SupervisorComplaintListSerializer(serializers.ModelSerializer):
    """Queue serializer for supervisor and employee views."""
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    department_name = serializers.CharField(source='assigned_department.name', read_only=True, default=None)
    assigned_employee_name = serializers.CharField(source='assigned_employee.full_name', read_only=True, default=None)

    class Meta:
        model = Complaint
        fields = [
            'id', 'complaint_number', 'category_name',
            'status', 'assigned_department_id', 'department_name',
            'assigned_employee_id', 'assigned_employee_name',
            'location_address', 'location_lat', 'location_lng',
            'submitted_at', 'updated_at', 'priority_category',
        ]


class ComplaintVerificationSerializer(serializers.ModelSerializer):
    verified_by_name = serializers.CharField(source='verified_by.full_name', read_only=True)

    class Meta:
        model = ComplaintVerification
        fields = [
            'id', 'complaint_id', 'verified_by_id', 'verified_by_name',
            'site_inspection_notes', 'verification_result', 'verification_remarks',
            'verified_at',
        ]
        read_only_fields = fields


class ComplaintResolutionSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)

    class Meta:
        model = ComplaintResolution
        fields = [
            'id', 'complaint_id', 'updated_by_id', 'updated_by_name',
            'progress_update', 'remarks', 'expected_completion_date',
            'resolution_details', 'resolution_proof_url',
            'is_final_resolution', 'created_at',
        ]
        read_only_fields = fields


class ComplaintDetailSerializer(serializers.ModelSerializer):
    """Full view for a single complaint."""
    category = ComplaintCategorySerializer(read_only=True)
    assigned_department = DepartmentSummarySerializer(read_only=True)
    assigned_employee = StaffProfileSummarySerializer(read_only=True)
    attachments = ComplaintAttachmentSerializer(many=True, read_only=True)
    status_history = ComplaintStatusHistorySerializer(many=True, read_only=True)
    assignments = ComplaintAssignmentSerializer(many=True, read_only=True)
    verifications = ComplaintVerificationSerializer(many=True, read_only=True)
    resolutions = ComplaintResolutionSerializer(many=True, read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'complaint_number',
            'category', 'description',
            'location_lat', 'location_lng', 'location_address',
            'district', 'taluk', 'local_body', 'ward',
            'inconvenience_details', 'expected_solution',
            'status', 'priority_category',
            'assigned_department',
            'assigned_employee',
            'expected_completion_date',
            'closure_confirmation',
            'closure_due_at',
            'reporter_count',
            'submitted_at', 'updated_at',
            'attachments', 'status_history', 'assignments', 'verifications', 'resolutions',
        ]
        read_only_fields = fields


class ComplaintSubmitSerializer(serializers.Serializer):
    """
    Input serializer for POST /api/v1/complaints/

    Fields that must NOT appear here (backend-controlled):
      - citizen_id
      - complaint_number
      - status
      - priority_*
      - severity_*
      - assigned_department_id
      - assigned_employee_id
      - reporter_count
      - main_complaint_id
    """

    category_id = serializers.IntegerField()
    description = serializers.CharField(min_length=10, max_length=5000)
    state = serializers.CharField(min_length=2, max_length=100)
    district = serializers.CharField(min_length=2, max_length=100)
    google_maps_url = serializers.URLField(max_length=2000)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    location_address = serializers.CharField(required=False, allow_blank=True, max_length=500)
    taluk = serializers.CharField(required=False, allow_blank=True, max_length=100)
    local_body = serializers.CharField(required=False, allow_blank=True, max_length=100)
    ward = serializers.CharField(required=False, allow_blank=True, max_length=100)
    inconvenience_details = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    expected_solution = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate_category_id(self, value):
        try:
            cat = ComplaintCategory.objects.get(id=value)
        except ComplaintCategory.DoesNotExist:
            raise serializers.ValidationError(f'Category {value} does not exist.')
        if not cat.is_active:
            raise serializers.ValidationError(
                f'Category "{cat.name}" is not currently accepting complaints.'
            )
        self._category = cat
        return value

    def validate(self, attrs):
        google_maps_url = attrs.get('google_maps_url')
        if google_maps_url:
            try:
                lat, lng = extract_coordinates_from_url(google_maps_url)
                attrs['latitude'] = lat
                attrs['longitude'] = lng
            except LocationExtractionError as e:
                raise serializers.ValidationError({"google_maps_url": str(e)})
        return attrs

    @property
    def category(self):
        return getattr(self, '_category', None)


class ComplaintSubmitResponseSerializer(serializers.ModelSerializer):
    """Response returned after successful complaint submission."""
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = Complaint
        fields = [
            'id', 'complaint_number', 'status',
            'category_name', 'description',
            'location_lat', 'location_lng', 'location_address',
            'submitted_at',
        ]


class AssignEmployeeSerializer(serializers.Serializer):
    """Input serializer for Supervisor assigning an employee."""
    employee_id = serializers.UUIDField()
    assignment_reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class ReassignEmployeeSerializer(serializers.Serializer):
    """Input serializer for Supervisor reassigning an employee."""
    employee_id = serializers.UUIDField()
    reassignment_reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class SubmitVerificationSerializer(serializers.Serializer):
    """Input serializer for Ground-Level Employee submitting verification."""
    verification_result = serializers.ChoiceField(choices=['verified', 'invalid'])
    verification_remarks = serializers.CharField(min_length=5, max_length=3000)
    site_inspection_notes = serializers.CharField(required=False, allow_blank=True, max_length=3000)


class SubmitProgressUpdateSerializer(serializers.Serializer):
    """Input serializer for Ground-Level Employee recording a progress update."""
    progress_update = serializers.CharField(required=False, allow_blank=True, max_length=3000)
    remarks = serializers.CharField(required=False, allow_blank=True, max_length=3000)
    expected_completion_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        prog = (attrs.get('progress_update') or '').strip()
        rem = (attrs.get('remarks') or '').strip()
        if not prog and not rem:
            raise serializers.ValidationError('Either progress_update or remarks must be provided.')
        return attrs


class SubmitResolutionSerializer(serializers.Serializer):
    """Input serializer for Ground-Level Employee resolving a complaint."""
    resolution_details = serializers.CharField(min_length=10, max_length=4000)
    remarks = serializers.CharField(required=False, allow_blank=True, max_length=3000)


class ConfirmResolutionSerializer(serializers.Serializer):
    """Input serializer for Citizen confirming resolution."""
    confirmation_remarks = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class RejectResolutionSerializer(serializers.Serializer):
    """Input serializer for Citizen rejecting resolution."""
    rejection_reason = serializers.CharField(min_length=5, max_length=3000)

class PublicComplaintStatusHistorySerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='new_status')

    class Meta:
        model = ComplaintStatusHistory
        fields = ['status', 'changed_at']
        read_only_fields = fields


class PublicComplaintResolutionSerializer(serializers.ModelSerializer):
    details = serializers.CharField(source='resolution_details')
    resolved_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = ComplaintResolution
        fields = ['details', 'resolved_at']
        read_only_fields = fields


class PublicComplaintTrackingSerializer(serializers.ModelSerializer):
    """
    Publicly safe serializer for complaint tracking.
    Never includes PII, location details, internal notes, or employee information.
    Resolves duplicate complaints to their ultimate primary complaint.
    """
    category = serializers.CharField(source='category.name', read_only=True, default=None)
    status_history = serializers.SerializerMethodField()
    resolution = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_duplicate = serializers.SerializerMethodField()
    main_complaint_number = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = [
            'complaint_number',
            'category',
            'status',
            'submitted_at',
            'updated_at',
            'status_history',
            'resolution',
            'is_duplicate',
            'main_complaint_number',
        ]
        read_only_fields = fields

    def _get_target(self, obj):
        # We need to resolve to the ultimate primary complaint if it is a duplicate
        target = obj
        visited = set()
        while target.main_complaint_id:
            if target.id in visited:
                break
            visited.add(target.id)
            target = target.main_complaint
        return target

    def get_status(self, obj):
        return self._get_target(obj).status

    def get_updated_at(self, obj):
        return self._get_target(obj).updated_at

    def get_is_duplicate(self, obj):
        return obj.main_complaint_id is not None

    def get_main_complaint_number(self, obj):
        target = self._get_target(obj)
        return target.complaint_number if obj.id != target.id else None

    def get_status_history(self, obj):
        target = self._get_target(obj)
        return PublicComplaintStatusHistorySerializer(target.status_history.all(), many=True).data

    def get_resolution(self, obj):
        target = self._get_target(obj)
        res = target.resolutions.filter(is_final_resolution=True).order_by('-created_at').first()
        if res:
            return PublicComplaintResolutionSerializer(res).data
        return None
