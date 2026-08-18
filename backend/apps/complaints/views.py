"""
apps/complaints/views.py

Phase 3 & Phase 4 complaint API views.

Access rules:
  - POST /api/v1/complaints/                   → Citizen only; submits a new complaint.
  - GET  /api/v1/complaints/                   → Citizen; returns ONLY their own complaints.
  - GET  /api/v1/complaints/<uuid>/            → Citizen; returns ONLY if owner.
  - POST /api/v1/complaints/<uuid>/route/      → System / Admin; triggers automated routing.
  - GET  /api/v1/categories/                   → Any authenticated user.
  - GET  /api/v1/categories/<id>/              → Any authenticated user.

  - GET  /api/v1/supervisor/complaints/unassigned/ → Supervisor; unassigned queue for supervisor's dept.
  - GET  /api/v1/supervisor/complaints/            → Supervisor; all complaints for supervisor's dept.
  - POST /api/v1/supervisor/complaints/<uuid>/assign/   → Supervisor; assigns employee.
  - POST /api/v1/supervisor/complaints/<uuid>/reassign/ → Supervisor; reassigns employee.

  - GET  /api/v1/employee/complaints/          → Ground-Level Employee; returns ONLY assigned complaints.
"""

import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from apps.complaints.models import Complaint, ComplaintCategory, ComplaintStatus
from apps.complaints.serializers import (
    ComplaintSubmitSerializer,
    ComplaintSubmitResponseSerializer,
    ComplaintListSerializer,
    ComplaintDetailSerializer,
    ComplaintCategorySerializer,
    SupervisorComplaintListSerializer,
    AssignEmployeeSerializer,
    ReassignEmployeeSerializer,
    SubmitVerificationSerializer,
    SubmitProgressUpdateSerializer,
    SubmitResolutionSerializer,
    ComplaintResolutionSerializer,
    ConfirmResolutionSerializer,
    RejectResolutionSerializer,
)
from apps.complaints.services import submit_complaint, validate_attachments
from apps.complaints.routing import route_complaint, RoutingFailureError
from apps.complaints.assignment import (
    assign_employee_to_complaint,
    reassign_employee_to_complaint,
)
from apps.users.models import Profile
from core.permissions.roles import (
    IsAuthenticatedViaSupabase,
    IsCitizen,
    IsSupervisor,
    IsGroundLevelEmployee,
    IsAssignedEmployeeOrDepartmentSupervisor,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Category views
# ---------------------------------------------------------------------------

class CategoryListView(generics.ListAPIView):
    """
    GET /api/v1/categories/
    Returns all active complaint categories.
    """
    permission_classes = [IsAuthenticatedViaSupabase]
    serializer_class = ComplaintCategorySerializer

    def get_queryset(self):
        return ComplaintCategory.objects.filter(is_active=True).order_by('name')


class CategoryDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/categories/<id>/
    Returns a single category.
    """
    permission_classes = [IsAuthenticatedViaSupabase]
    serializer_class = ComplaintCategorySerializer
    queryset = ComplaintCategory.objects.all()


# ---------------------------------------------------------------------------
# Citizen Complaint submission + listing
# ---------------------------------------------------------------------------

class ComplaintListCreateView(APIView):
    """
    GET  /api/v1/complaints/  → List citizen's own complaints.
    POST /api/v1/complaints/  → Submit a new complaint.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsCitizen]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        complaints = (
            Complaint.objects
            .filter(citizen_id=request.user.id)
            .select_related('category')
            .order_by('-submitted_at')
        )
        
        # Apply Query Parameter Filters
        status_param = request.query_params.get('status')
        if status_param and status_param != 'All':
            complaints = complaints.filter(status=status_param)
            
        category_param = request.query_params.get('category')
        if category_param and category_param != 'All':
            complaints = complaints.filter(category__name__iexact=category_param)
            
        search_param = request.query_params.get('search')
        if search_param:
            from django.db.models import Q
            complaints = complaints.filter(
                Q(complaint_number__icontains=search_param) |
                Q(category__name__icontains=search_param) |
                Q(district__icontains=search_param) |
                Q(location_address__icontains=search_param)
            )

        serializer = ComplaintListSerializer(complaints, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ComplaintSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_files = request.FILES.getlist('attachments')
        pending_attachments, att_errors = validate_attachments(uploaded_files)
        if att_errors:
            return Response({'attachments': att_errors}, status=status.HTTP_400_BAD_REQUEST)

        category = serializer.category
        if category and category.requires_attachment and not pending_attachments:
            return Response(
                {'attachments': [
                    f'Category "{category.name}" requires at least one attachment.'
                ]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        validated_data['category'] = category

        try:
            complaint = submit_complaint(
                citizen=request.user,
                validated_data=validated_data,
                pending_attachments=pending_attachments,
            )
        except Exception as exc:
            logger.exception('Complaint submission failed: %s', exc)
            return Response(
                {'detail': 'Complaint submission failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = ComplaintSubmitResponseSerializer(complaint).data
        return Response(response_data, status=status.HTTP_201_CREATED)


class ComplaintDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/complaints/<uuid>/
    Returns a single complaint. Only the owning citizen may retrieve it.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsCitizen]
    serializer_class = ComplaintDetailSerializer

    def get_queryset(self):
        return (
            Complaint.objects
            .filter(citizen_id=self.request.user.id)
            .select_related('category', 'assigned_department', 'assigned_employee')
            .prefetch_related('attachments', 'status_history', 'assignments')
        )


# ---------------------------------------------------------------------------
# Department Routing Trigger View
# ---------------------------------------------------------------------------

class RouteComplaintView(APIView):
    """
    POST /api/v1/complaints/<uuid:pk>/route/
    Triggers automatic department routing for a submitted complaint.
    """
    permission_classes = [IsAuthenticatedViaSupabase]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        try:
            department = route_complaint(complaint)
            return Response({
                'detail': f'Complaint routed successfully to {department.name}.',
                'assigned_department_id': str(department.id),
                'department_name': department.name,
                'status': complaint.status,
            })
        except RoutingFailureError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


# ---------------------------------------------------------------------------
# Supervisor Views (Phase 4)
# ---------------------------------------------------------------------------

class SupervisorUnassignedQueueView(APIView):
    """
    GET /api/v1/supervisor/complaints/unassigned/
    Returns unassigned complaints in the Supervisor's department.
    Criteria:
      - assigned_department_id == supervisor.department_id
      - status == UNDER_VERIFICATION
      - assigned_employee_id IS NULL
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsSupervisor]

    def get(self, request):
        supervisor = request.user
        if not supervisor.department_id:
            return Response(
                {'detail': 'Supervisor has no assigned department.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unassigned_complaints = (
            Complaint.objects
            .filter(
                assigned_department_id=supervisor.department_id,
                status=ComplaintStatus.UNDER_VERIFICATION,
                assigned_employee_id__isnull=True,
            )
            .select_related('category', 'assigned_department')
            .order_by('-submitted_at')
        )

        serializer = SupervisorComplaintListSerializer(unassigned_complaints, many=True)
        return Response(serializer.data)


class SupervisorDepartmentComplaintsView(APIView):
    """
    GET /api/v1/supervisor/complaints/
    Returns all complaints assigned to the Supervisor's department.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsSupervisor]

    def get(self, request):
        supervisor = request.user
        if not supervisor.department_id:
            return Response(
                {'detail': 'Supervisor has no assigned department.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        complaints = (
            Complaint.objects
            .filter(assigned_department_id=supervisor.department_id)
            .select_related('category', 'assigned_department', 'assigned_employee')
            .order_by('-submitted_at')
        )

        serializer = SupervisorComplaintListSerializer(complaints, many=True)
        return Response(serializer.data)


class SupervisorAssignEmployeeView(APIView):
    """
    POST /api/v1/supervisor/complaints/<uuid:pk>/assign/
    Assigns an unassigned complaint to a Ground-Level Employee in the same department.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsSupervisor]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        supervisor = request.user

        serializer = AssignEmployeeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        employee_id = serializer.validated_data['employee_id']
        assignment_reason = serializer.validated_data.get('assignment_reason', '')

        try:
            employee = Profile.objects.select_related('role').get(pk=employee_id)
        except Profile.DoesNotExist:
            return Response(
                {'detail': f'Employee with ID {employee_id} does not exist.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            updated_complaint = assign_employee_to_complaint(
                supervisor=supervisor,
                complaint=complaint,
                employee=employee,
                assignment_reason=assignment_reason,
            )
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ComplaintDetailSerializer(updated_complaint).data,
            status=status.HTTP_200_OK,
        )


class SupervisorReassignEmployeeView(APIView):
    """
    POST /api/v1/supervisor/complaints/<uuid:pk>/reassign/
    Reassigns an assigned complaint to a different Ground-Level Employee in the same department.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsSupervisor]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        supervisor = request.user

        serializer = ReassignEmployeeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        employee_id = serializer.validated_data['employee_id']
        reassignment_reason = serializer.validated_data.get('reassignment_reason', '')

        try:
            new_employee = Profile.objects.select_related('role').get(pk=employee_id)
        except Profile.DoesNotExist:
            return Response(
                {'detail': f'Employee with ID {employee_id} does not exist.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            updated_complaint = reassign_employee_to_complaint(
                supervisor=supervisor,
                complaint=complaint,
                new_employee=new_employee,
                reassignment_reason=reassignment_reason,
            )
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ComplaintDetailSerializer(updated_complaint).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Ground-Level Employee Views (Phase 4)
# ---------------------------------------------------------------------------

class EmployeeAssignedComplaintsView(APIView):
    """
    GET /api/v1/employee/complaints/
    Returns complaints assigned specifically to the authenticated Ground-Level Employee.
    Access is strictly filtered by: assigned_employee_id == request.user.id
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsGroundLevelEmployee]

    def get(self, request):
        employee = request.user
        assigned_complaints = (
            Complaint.objects
            .filter(assigned_employee_id=employee.id)
            .select_related('category', 'assigned_department')
            .order_by('-submitted_at')
        )
        serializer = SupervisorComplaintListSerializer(assigned_complaints, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Ground-Level Employee Verification Views (Phase 5)
# ---------------------------------------------------------------------------

class EmployeeVerifyComplaintView(APIView):
    """
    POST /api/v1/employee/complaints/<uuid:pk>/verify/
    Submits on-site physical verification for a complaint assigned to the authenticated Ground-Level Employee.
    Accepts: verification_result ('verified' | 'invalid'), verification_remarks (mandatory),
    site_inspection_notes (optional), attachments (optional evidence files).
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsGroundLevelEmployee]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        employee = request.user

        serializer = SubmitVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_files = request.FILES.getlist('attachments')
        pending_attachments, att_errors = validate_attachments(uploaded_files)
        if att_errors:
            return Response({'attachments': att_errors}, status=status.HTTP_400_BAD_REQUEST)

        verification_result = serializer.validated_data['verification_result']
        verification_remarks = serializer.validated_data['verification_remarks']
        site_inspection_notes = serializer.validated_data.get('site_inspection_notes', '')

        try:
            from apps.complaints.verification import verify_complaint
            verification, updated_complaint = verify_complaint(
                employee=employee,
                complaint=complaint,
                verification_result=verification_result,
                verification_remarks=verification_remarks,
                site_inspection_notes=site_inspection_notes,
                pending_attachments=pending_attachments,
            )
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ComplaintDetailSerializer(updated_complaint).data,
            status=status.HTTP_200_OK,
        )


class EmployeeComplaintVerificationDetailView(APIView):
    """
    GET /api/v1/employee/complaints/<uuid:pk>/verification/
    Retrieves verification decision and inspection findings for an assigned complaint.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsGroundLevelEmployee]

    def get(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        employee = request.user

        if str(complaint.assigned_employee_id) != str(employee.id):
            return Response(
                {'detail': 'You can only view verification records for complaints assigned to you.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        from apps.complaints.models import ComplaintVerification
        try:
            verification = ComplaintVerification.objects.select_related('verified_by').get(complaint_id=complaint.id)
        except ComplaintVerification.DoesNotExist:
            return Response(
                {'detail': 'No verification record found for this complaint.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.complaints.serializers import ComplaintVerificationSerializer
        return Response(ComplaintVerificationSerializer(verification).data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Progress & Resolution Views (Phase 6)
# ---------------------------------------------------------------------------

class EmployeeAddProgressUpdateView(APIView):
    """
    POST /api/v1/employee/complaints/<uuid:pk>/progress/
    Records an interim progress update on an assigned complaint.
    Authorized for assigned Ground-Level Employee OR Department Supervisor.
    Status transitions:
      - If VERIFIED: transitions to IN_PROGRESS.
      - If IN_PROGRESS: records progress update without duplicating status history.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsAssignedEmployeeOrDepartmentSupervisor]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        self.check_object_permissions(request, complaint)
        user = request.user

        serializer = SubmitProgressUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        progress_update = serializer.validated_data.get('progress_update', '')
        remarks = serializer.validated_data.get('remarks', '')
        expected_completion_date = serializer.validated_data.get('expected_completion_date')

        try:
            from apps.complaints.resolution import add_progress_update
            res_record, updated_complaint = add_progress_update(
                user=user,
                complaint=complaint,
                progress_update=progress_update,
                remarks=remarks,
                expected_completion_date=expected_completion_date,
            )
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ComplaintDetailSerializer(updated_complaint).data,
            status=status.HTTP_200_OK,
        )


class EmployeeResolveComplaintView(APIView):
    """
    POST /api/v1/employee/complaints/<uuid:pk>/resolve/
    Submits final resolution and proof for an active complaint.
    Authorized for assigned Ground-Level Employee OR Department Supervisor.
    Status transition:
      IN_PROGRESS -> RESOLVED
    Requires:
      - resolution_details (mandatory)
      - attachments (mandatory resolution proof photo/doc)
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsAssignedEmployeeOrDepartmentSupervisor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        self.check_object_permissions(request, complaint)
        user = request.user

        serializer = SubmitResolutionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_files = request.FILES.getlist('attachments')
        pending_attachments, att_errors = validate_attachments(uploaded_files)
        if att_errors:
            return Response({'attachments': att_errors}, status=status.HTTP_400_BAD_REQUEST)

        if not pending_attachments:
            return Response(
                {'attachments': ['Resolution proof attachment is mandatory to resolve a complaint.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resolution_details = serializer.validated_data['resolution_details']
        remarks = serializer.validated_data.get('remarks', '')

        try:
            from apps.complaints.resolution import resolve_complaint
            resolution, updated_complaint = resolve_complaint(
                user=user,
                complaint=complaint,
                resolution_details=resolution_details,
                remarks=remarks,
                pending_attachments=pending_attachments,
            )
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ComplaintDetailSerializer(updated_complaint).data,
            status=status.HTTP_200_OK,
        )


class EmployeeComplaintResolutionsListView(APIView):
    """
    GET /api/v1/employee/complaints/<uuid:pk>/resolutions/
    Lists all progress updates and final resolution entries for an assigned complaint.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsAssignedEmployeeOrDepartmentSupervisor]

    def get(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        self.check_object_permissions(request, complaint)

        from apps.complaints.models import ComplaintResolution
        resolutions = (
            ComplaintResolution.objects
            .filter(complaint_id=complaint.id)
            .select_related('updated_by')
            .order_by('created_at')
        )
        return Response(
            ComplaintResolutionSerializer(resolutions, many=True).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Citizen Confirmation & Rejection Views (Phase 7)
# ---------------------------------------------------------------------------

class CitizenConfirmResolutionView(APIView):
    """
    POST /api/v1/complaints/<uuid:pk>/confirm/
    Citizen confirms resolution of their complaint.
    Status transition:
      RESOLVED -> CLOSED
      closure_confirmation -> confirmed
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsCitizen]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        citizen = request.user

        serializer = ConfirmResolutionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        confirmation_remarks = serializer.validated_data.get('confirmation_remarks', '')

        try:
            from apps.complaints.closure import confirm_resolution
            updated_complaint = confirm_resolution(
                citizen=citizen,
                complaint=complaint,
                confirmation_remarks=confirmation_remarks,
            )
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ComplaintDetailSerializer(updated_complaint).data,
            status=status.HTTP_200_OK,
        )


class CitizenRejectResolutionView(APIView):
    """
    POST /api/v1/complaints/<uuid:pk>/reject/
    Citizen rejects resolution of their complaint due to unsatisfactory fix.
    Status transition:
      RESOLVED -> IN_PROGRESS
      closure_confirmation -> rejected
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsCitizen]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        citizen = request.user

        serializer = RejectResolutionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        rejection_reason = serializer.validated_data['rejection_reason']

        try:
            from apps.complaints.closure import reject_resolution
            updated_complaint = reject_resolution(
                citizen=citizen,
                complaint=complaint,
                rejection_reason=rejection_reason,
            )
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ComplaintDetailSerializer(updated_complaint).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Notification Views (Phase 3)
# ---------------------------------------------------------------------------

from apps.complaints.models import Notification
from apps.complaints.serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    """
    GET /api/v1/notifications/
    Returns all notifications for the authenticated user, ordered by newest first.
    """
    permission_classes = [IsAuthenticatedViaSupabase]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient_id=self.request.user.id).order_by('-created_at')


class NotificationUnreadCountView(APIView):
    """
    GET /api/v1/notifications/unread-count/
    Returns the count of unread notifications for the authenticated user.
    """
    permission_classes = [IsAuthenticatedViaSupabase]

    def get(self, request):
        count = Notification.objects.filter(recipient_id=request.user.id, is_read=False).count()
        return Response({'count': count}, status=status.HTTP_200_OK)


class NotificationMarkReadView(APIView):
    """
    POST /api/v1/notifications/<uuid:pk>/read/
    Marks a single notification as read.
    """
    permission_classes = [IsAuthenticatedViaSupabase]

    def post(self, request, pk):
        # We enforce ownership via get_object_or_404 against the user-scoped queryset
        notification = get_object_or_404(
            Notification.objects.filter(recipient_id=request.user.id),
            pk=pk
        )
        
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)


class NotificationMarkAllReadView(APIView):
    """
    POST /api/v1/notifications/read-all/
    Marks all unread notifications for the authenticated user as read.
    """
    permission_classes = [IsAuthenticatedViaSupabase]

    def post(self, request):
        unread_notifications = Notification.objects.filter(
            recipient_id=request.user.id,
            is_read=False
        )
        updated_count = unread_notifications.update(is_read=True)
        return Response({'updated': updated_count}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Public Complaint Tracking View (Phase 10A)
# ---------------------------------------------------------------------------

from rest_framework.permissions import AllowAny
from apps.complaints.serializers import PublicComplaintTrackingSerializer

class PublicComplaintTrackingView(APIView):
    """
    GET /api/v1/complaints/public/<complaint_number>/
    Public, unauthenticated endpoint to track complaint status securely.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, complaint_number):
        # Explicit lookup by complaint_number, case-insensitive mapping if needed
        # Assuming exact match based on existing convention (e.g. CMP-YYYY-NNNNNN)
        complaint = get_object_or_404(
            Complaint.objects.select_related('category')
            .prefetch_related('status_history', 'resolutions'),
            complaint_number__iexact=complaint_number
        )

        serializer = PublicComplaintTrackingSerializer(complaint)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Reporting & Analytics Views (Phase 13)
# ---------------------------------------------------------------------------

from core.permissions.roles import IsDepartmentAdminOrSystemAdmin
from apps.complaints.reporting import get_filtered_complaints_queryset, get_analytics_data, generate_excel_report, generate_pdf_report
from django.http import HttpResponse

class AdminAnalyticsView(APIView):
    """
    GET /api/v1/admin/reports/analytics/
    Returns aggregated JSON statistics based on query parameters.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsDepartmentAdminOrSystemAdmin]

    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_403_FORBIDDEN)

        filters = request.query_params
        queryset = get_filtered_complaints_queryset(profile, filters)
        analytics_data = get_analytics_data(queryset)

        return Response(analytics_data, status=status.HTTP_200_OK)


class AdminExportView(APIView):
    """
    GET /api/v1/admin/reports/export/
    Returns generated Excel or PDF report based on query parameters.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsDepartmentAdminOrSystemAdmin]

    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_403_FORBIDDEN)

        filters = request.query_params
        fmt = filters.get('format', 'xlsx').lower()

        if fmt not in ['xlsx', 'pdf']:
            return Response({'detail': 'Invalid format. Use xlsx or pdf.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = get_filtered_complaints_queryset(profile, filters)
        analytics_data = get_analytics_data(queryset)

        if fmt == 'xlsx':
            file_data = generate_excel_report(analytics_data, queryset)
            response = HttpResponse(file_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="civic_report.xlsx"'
            return response
        else:
            file_data = generate_pdf_report(analytics_data, queryset, filters)
            response = HttpResponse(file_data, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="civic_report.pdf"'
            return response
