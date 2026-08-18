"""
apps/users/views.py

Phase 2 user/profile API views.

Design rules:
- request.user is always a Profile (set by SupabaseAuthentication).
- Role and department values come from the server-side profile — never from
  the request body.
- No endpoint returns raw lists of all users to unprivileged callers.
- System Admins can view any profile.
- Department Admins and Supervisors can view profiles within their department.
- Citizens and Employees can only view their own profile.
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import Profile
from apps.users.serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    StaffProfileSummarySerializer,
)
from core.permissions.roles import (
    IsAuthenticatedViaSupabase,
    IsSupervisorOrAbove,
    IsDepartmentAdminOrSystemAdmin,
    IsSystemAdmin,
)


# ---------------------------------------------------------------------------
# /api/v1/users/me/
# ---------------------------------------------------------------------------

class CurrentUserProfileView(APIView):
    """
    GET  /api/v1/users/me/
        Returns the authenticated user's own profile.
        Any authenticated user with an active account can call this.

    PATCH /api/v1/users/me/
        Updates editable fields (full_name, phone) on the user's own profile.
        Role, department, supervisor and account_status are NOT changeable here.
    """

    permission_classes = [IsAuthenticatedViaSupabase]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProfileSerializer(request.user).data)


# ---------------------------------------------------------------------------
# /api/v1/users/me/role/
# ---------------------------------------------------------------------------

class CurrentUserRoleView(APIView):
    """
    GET /api/v1/users/me/role/
        Returns the authenticated user's role metadata.
        Used by React to determine which UI views to display.
        The role value is sourced from the server — React must NOT use a
        client-supplied role value for authorization decisions.
    """

    permission_classes = [IsAuthenticatedViaSupabase]

    def get(self, request):
        profile = request.user
        return Response({
            'role': profile.role.role_name,
            'role_id': profile.role.id,
            'role_description': profile.role.description,
        })


# ---------------------------------------------------------------------------
# /api/v1/users/me/department/
# ---------------------------------------------------------------------------

class CurrentUserDepartmentView(APIView):
    """
    GET /api/v1/users/me/department/
        Returns the authenticated user's department.
        Returns null for citizens and system admins who have no department.
    """

    permission_classes = [IsAuthenticatedViaSupabase]

    def get(self, request):
        profile = request.user
        dept = profile.department
        if dept is None:
            return Response({'department': None})
        return Response({
            'department': {
                'id': str(dept.id),
                'name': dept.name,
                'is_active': dept.is_active,
            }
        })


# ---------------------------------------------------------------------------
# /api/v1/users/department-members/
# ---------------------------------------------------------------------------

class DepartmentMembersView(generics.ListAPIView):
    """
    GET /api/v1/users/department-members/
        Returns profiles belonging to the caller's department.

        Access:
        - Supervisor: sees members of their own department.
        - Department Admin: sees all members of their department.
        - System Admin: must supply ?department_id= query param.
        - Citizens and Ground-Level Employees: not permitted.
    """

    permission_classes = [IsAuthenticatedViaSupabase, IsSupervisorOrAbove]
    serializer_class = StaffProfileSummarySerializer

    def get_queryset(self):
        profile = self.request.user

        if profile.is_system_admin:
            dept_id = self.request.query_params.get('department_id')
            if not dept_id:
                return Profile.objects.none()
            return (
                Profile.objects
                .select_related('role', 'department')
                .filter(department_id=dept_id)
            )

        # Department Admin and Supervisor see their own department.
        return (
            Profile.objects
            .select_related('role', 'department')
            .filter(department_id=profile.department_id)
        )


# ---------------------------------------------------------------------------
# /api/v1/users/<uuid:pk>/
# ---------------------------------------------------------------------------

class ProfileDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/users/<uuid>/
        Returns a profile by ID.

        Access rules:
        - System Admin: any profile.
        - Department Admin / Supervisor: profiles within their department only.
        - Others: own profile only (use /me/ instead).
    """

    permission_classes = [IsAuthenticatedViaSupabase]
    serializer_class = StaffProfileSummarySerializer

    def get_queryset(self):
        profile = self.request.user

        if profile.is_system_admin:
            return Profile.objects.select_related('role', 'department').all()

        if profile.is_department_admin or profile.is_supervisor:
            return (
                Profile.objects
                .select_related('role', 'department')
                .filter(department_id=profile.department_id)
            )

        # Citizens and ground-level employees may only retrieve their own.
        return Profile.objects.select_related('role', 'department').filter(id=profile.id)


from apps.users.models import Role
from apps.users.serializers import RoleSerializer

class RoleListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedViaSupabase, IsDepartmentAdminOrSystemAdmin]
    serializer_class = RoleSerializer
    queryset = Role.objects.all()

from apps.users.services import create_employee, transfer_location, transfer_department
from apps.users.serializers import EmployeeCreateSerializer, LocationTransferSerializer, DepartmentTransferSerializer

class EmployeeCreateView(APIView):
    """
    POST /api/v1/users/employees/
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsDepartmentAdminOrSystemAdmin]

    def post(self, request):
        serializer = EmployeeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            profile = create_employee(
                admin_profile=request.user,
                full_name=data['full_name'],
                email=data['email'],
                phone=data.get('phone', ''),
                role_id=data['role_id'],
                department_id=data.get('department_id'),
                jurisdiction_id=data.get('jurisdiction_id')
            )
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(StaffProfileSummarySerializer(profile).data, status=status.HTTP_201_CREATED)


class EmployeeLocationTransferView(APIView):
    """
    POST /api/v1/users/<uuid:pk>/transfer-location/
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsDepartmentAdminOrSystemAdmin]

    def post(self, request, pk):
        serializer = LocationTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            profile = transfer_location(
                admin_profile=request.user,
                employee_id=pk,
                new_jurisdiction_id=serializer.validated_data.get('jurisdiction_id')
            )
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(StaffProfileSummarySerializer(profile).data, status=status.HTTP_200_OK)


class EmployeeDepartmentTransferView(APIView):
    """
    POST /api/v1/users/<uuid:pk>/transfer-department/
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsSystemAdmin]

    def post(self, request, pk):
        serializer = DepartmentTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            profile = transfer_department(
                admin_profile=request.user,
                employee_id=pk,
                new_department_id=serializer.validated_data.get('department_id')
            )
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(StaffProfileSummarySerializer(profile).data, status=status.HTTP_200_OK)
