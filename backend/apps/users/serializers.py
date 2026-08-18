"""
Serializers for the users app.

Rules:
- Do NOT expose: password hashes, Supabase service keys, supervisor PIIs of other users.
- Nested representations are shallow (ID + name only) to avoid data leakage.
- Write operations are explicitly controlled — most fields are read-only from
  Django's perspective because the canonical write path is Supabase Auth +
  PostgreSQL triggers.
"""

from rest_framework import serializers
from apps.users.models import Profile, Role, Department


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'role_name', 'description']


class DepartmentSummarySerializer(serializers.ModelSerializer):
    """Minimal department representation — safe to embed in profile responses."""

    class Meta:
        model = Department
        fields = ['id', 'name', 'is_active']


class SupervisorSummarySerializer(serializers.Serializer):
    """
    Minimal supervisor representation exposed to a subordinate.
    Only id + full_name to avoid exposing sensitive data.
    """

    id = serializers.UUIDField()
    full_name = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Full profile representation for the authenticated user's own profile.
    Nested role and department are read-only summary objects.
    """

    role = RoleSerializer(read_only=True)
    department = DepartmentSummarySerializer(read_only=True)
    supervisor = SupervisorSummarySerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'role',
            'department',
            'supervisor',
            'account_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'role',
            'department',
            'supervisor',
            'account_status',
            'created_at',
            'updated_at',
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the authenticated user's own editable fields.
    Role, department, supervisor and status are NOT user-editable here.
    """

    class Meta:
        model = Profile
        fields = ['full_name', 'phone']


class StaffProfileSummarySerializer(serializers.ModelSerializer):
    """
    Reduced profile view for supervisors/dept-admins viewing their team.
    Deliberately omits phone — visible only when the accessor has authority.
    """

    role_name = serializers.CharField(source='role.role_name', read_only=True)
    department_name = serializers.CharField(
        source='department.name', read_only=True, default=None
    )

    class Meta:
        model = Profile
        fields = [
            'id',
            'full_name',
            'email',
            'role_name',
            'department_name',
            'account_status',
        ]

class EmployeeCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    role_id = serializers.IntegerField()
    department_id = serializers.UUIDField(required=False, allow_null=True)
    jurisdiction_id = serializers.UUIDField(required=False, allow_null=True)

class LocationTransferSerializer(serializers.Serializer):
    jurisdiction_id = serializers.UUIDField(allow_null=True)

class DepartmentTransferSerializer(serializers.Serializer):
    department_id = serializers.UUIDField(allow_null=True)
