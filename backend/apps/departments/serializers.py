"""
Serializers for the departments app.
Departments are managed by System Admins only.
"""

from rest_framework import serializers
from apps.users.models import Department
from apps.departments.models import DepartmentCategoryRule, Jurisdiction


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.IntegerField(read_only=True, required=False)
    complaint_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at', 'employee_count', 'complaint_count']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DepartmentCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['name', 'description', 'is_active']


class JurisdictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jurisdiction
        fields = ['id', 'name', 'area_type', 'boundary', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'boundary': {'required': False, 'allow_null': True, 'allow_blank': True}
        }


class DepartmentCategoryRuleSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    jurisdiction_name = serializers.CharField(source='jurisdiction.name', read_only=True, allow_null=True)

    class Meta:
        model = DepartmentCategoryRule
        fields = [
            'id', 'department_id', 'department_name', 
            'category_id', 'category_name', 
            'jurisdiction_id', 'jurisdiction_name',
            'priority_rank', 'is_active'
        ]
