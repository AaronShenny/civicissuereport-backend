"""
Serializers for the departments app.
Departments are managed by System Admins only.
"""

from rest_framework import serializers
from apps.users.models import Department


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DepartmentCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['name', 'description', 'is_active']
