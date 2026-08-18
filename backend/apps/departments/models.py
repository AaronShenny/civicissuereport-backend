"""
apps/departments/models.py

Models for departments, jurisdictions, and category routing rules.
All tables are managed = False (owned by Supabase PostgreSQL).
"""

from django.db import models
from apps.users.models import Department
from apps.complaints.models import ComplaintCategory


class Jurisdiction(models.Model):
    """
    Maps to public.jurisdictions.
    Defines geographical areas used for location-based assignment.
    """

    id = models.UUIDField(primary_key=True)
    name = models.TextField()
    area_type = models.TextField()
    boundary = models.TextField()  # geography(MultiPolygon,4326) in PostgreSQL
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'jurisdictions'

    def __str__(self):
        return f'{self.name} ({self.area_type})'


class DepartmentCategoryRule(models.Model):
    """
    Maps to public.department_category_rules.
    Maps complaint categories to responsible departments.
    """

    id = models.UUIDField(primary_key=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        db_column='department_id',
        related_name='category_rules',
    )
    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.CASCADE,
        db_column='category_id',
        related_name='department_rules',
    )
    jurisdiction = models.ForeignKey(
        Jurisdiction,
        on_delete=models.CASCADE,
        db_column='jurisdiction_id',
        null=True,
        blank=True,
        related_name='category_rules',
    )
    priority_rank = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'department_category_rules'
        unique_together = ('department', 'category', 'jurisdiction')

    def __str__(self):
        return f'{self.category.name} → {self.department.name} (rank {self.priority_rank})'
