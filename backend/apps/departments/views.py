"""
apps/departments/views.py

Phase 2 department API views.

Access rules:
- GET list:    System Admin (all), Department Admin/Supervisor (own dept), others: 403.
- GET detail:  System Admin (any), Department Admin/Supervisor (own dept only).
- POST create: System Admin only.
- PATCH update: System Admin only.

Department creation and deactivation must not disrupt existing complaint
assignments (those come in later phases).
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import Department
from apps.departments.models import DepartmentCategoryRule, Jurisdiction
from apps.departments.serializers import (
    DepartmentSerializer, 
    DepartmentCreateUpdateSerializer,
    DepartmentCategoryRuleSerializer,
    JurisdictionSerializer
)
from core.permissions.roles import (
    IsAuthenticatedViaSupabase,
    IsSystemAdmin,
    IsDepartmentAdminOrSystemAdmin,
    IsSupervisorOrAbove,
)


class DepartmentCategoryRuleListView(generics.ListAPIView):
    """
    GET /api/v1/departments/category-rules/
        - System Admin: all rules.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsSystemAdmin]
    serializer_class = DepartmentCategoryRuleSerializer
    queryset = DepartmentCategoryRule.objects.all().select_related('department', 'category', 'jurisdiction').order_by('category__name', 'priority_rank')



class DepartmentListView(generics.ListAPIView):
    """
    GET /api/v1/departments/
        - System Admin: all departments.
        - Department Admin / Supervisor: own department only.
        - Others: forbidden.
    """

    permission_classes = [IsAuthenticatedViaSupabase, IsSupervisorOrAbove]
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        profile = self.request.user
        if profile.is_system_admin:
            return Department.objects.all().order_by('name')
        # Supervisors and Department Admins see only their own department.
        if profile.department_id:
            return Department.objects.filter(id=profile.department_id)
        return Department.objects.none()


class DepartmentCreateView(generics.CreateAPIView):
    """
    POST /api/v1/departments/
        System Admin only.
    """

    permission_classes = [IsAuthenticatedViaSupabase, IsSystemAdmin]
    serializer_class = DepartmentCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # NOTE: For managed=False models we call .save() directly.
        # In a real setup, the system admin uses Supabase dashboard or a
        # migration SQL script to create departments, then we surface them here.
        # We raise 501 until proper DB write flow is implemented.
        return Response(
            {'detail': 'Department creation via API not yet implemented. Use Supabase dashboard.'},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class DepartmentDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/departments/<uuid>/
        - System Admin: any department.
        - Department Admin / Supervisor: own department only.
    """

    permission_classes = [IsAuthenticatedViaSupabase, IsSupervisorOrAbove]
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        profile = self.request.user
        if profile.is_system_admin:
            return Department.objects.all()
        if profile.department_id:
            return Department.objects.filter(id=profile.department_id)
        return Department.objects.none()

class JurisdictionListView(generics.ListAPIView):
    """
    GET /api/v1/departments/jurisdictions/
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsDepartmentAdminOrSystemAdmin]
    serializer_class = JurisdictionSerializer
    queryset = Jurisdiction.objects.all().order_by('name')
