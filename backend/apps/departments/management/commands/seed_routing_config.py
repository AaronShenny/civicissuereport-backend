"""
management/commands/seed_routing_config.py

Idempotent management command that creates the authoritative routing
configuration for the CIVIC complaint routing engine.

Creates:
  1. Departments (6) — the responsible authorities from the business mapping.
  2. Jurisdictions (2) — district-level records for Ernakulam and Idukki.
  3. DepartmentCategoryRules (8) — global category → department mappings.

Safe to run multiple times — uses get_or_create / update_or_create patterns.
Does NOT create user accounts, complaints, or fake data.
"""

import uuid
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.db import connection

from apps.users.models import Department
from apps.complaints.models import ComplaintCategory
from apps.departments.models import Jurisdiction, DepartmentCategoryRule


# ---------------------------------------------------------------
# Authoritative Category → Department Mapping
# ---------------------------------------------------------------
DEPARTMENT_DEFINITIONS = [
    {
        'name': 'Public Works Department (PWD), Kerala',
        'description': 'Road infrastructure, bridges, and public buildings maintenance.',
    },
    {
        'name': 'Kerala State Electricity Board (KSEB)',
        'description': 'Street lighting, electrical infrastructure, and power distribution.',
    },
    {
        'name': 'Kerala Water Authority (KWA)',
        'description': 'Water supply, distribution, and water quality management.',
    },
    {
        'name': 'Local Self Government Department (LSGD)',
        'description': 'General civic issues, drainage, and local governance.',
    },
    {
        'name': 'LSGD - Solid Waste Management',
        'description': 'Garbage collection, waste disposal, and solid waste management.',
    },
    {
        'name': 'LSGD - Health & Sanitation',
        'description': 'Public health, sanitation, and sewage management.',
    },
]

JURISDICTION_DEFINITIONS = [
    {'name': 'Ernakulam', 'area_type': 'district'},
    {'name': 'Idukki', 'area_type': 'district'},
]

# Category name → Department name (exactly as defined in DEPARTMENT_DEFINITIONS)
CATEGORY_DEPARTMENT_MAP = {
    'pothole': 'Public Works Department (PWD), Kerala',
    'road_damage': 'Public Works Department (PWD), Kerala',
    'streetlight': 'Kerala State Electricity Board (KSEB)',
    'water_supply': 'Kerala Water Authority (KWA)',
    'drainage': 'Local Self Government Department (LSGD)',
    'garbage': 'LSGD - Solid Waste Management',
    'sanitation': 'LSGD - Health & Sanitation',
    'other': 'Local Self Government Department (LSGD)',
}


class Command(BaseCommand):
    help = 'Seeds the authoritative routing configuration (departments, jurisdictions, category rules).'

    def handle(self, *args, **options):
        now = datetime.now(timezone.utc)

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Phase 8: Seed Routing Configuration ===\n'))

        # -----------------------------------------------------------
        # 1. Departments
        # -----------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING('--- Departments ---'))
        departments = {}
        for dept_def in DEPARTMENT_DEFINITIONS:
            dept, created = self._get_or_create_department(dept_def, now)
            departments[dept.name] = dept
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  [{status}] {dept.name}')

        # -----------------------------------------------------------
        # 2. Jurisdictions (district-level, boundary=NULL)
        # -----------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING('\n--- Jurisdictions ---'))
        jurisdictions = {}
        for jur_def in JURISDICTION_DEFINITIONS:
            jur, created = self._get_or_create_jurisdiction(jur_def, now)
            jurisdictions[jur.name] = jur
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  [{status}] {jur.name} ({jur.area_type})')

        # -----------------------------------------------------------
        # 3. Global DepartmentCategoryRules
        # -----------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING('\n--- Category -> Department Rules (Global) ---'))
        rules_created = 0
        rules_existing = 0

        for cat_name, dept_name in CATEGORY_DEPARTMENT_MAP.items():
            try:
                category = ComplaintCategory.objects.get(name=cat_name)
            except ComplaintCategory.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  [MISSING] Category "{cat_name}" not found in database!'))
                continue

            dept = departments.get(dept_name)
            if not dept:
                self.stdout.write(self.style.ERROR(f'  [MISSING] Department "{dept_name}" not found!'))
                continue

            rule, created = self._get_or_create_rule(category, dept, now)
            if created:
                rules_created += 1
                self.stdout.write(f'  [CREATED] {cat_name} -> {dept_name}')
            else:
                rules_existing += 1
                self.stdout.write(f'  [EXISTS]  {cat_name} -> {dept_name}')

        # -----------------------------------------------------------
        # Summary
        # -----------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING('\n--- Summary ---'))
        self.stdout.write(f'  Departments: {len(departments)}')
        self.stdout.write(f'  Jurisdictions: {len(jurisdictions)}')
        self.stdout.write(f'  Rules created: {rules_created}, existing: {rules_existing}')
        self.stdout.write(self.style.SUCCESS('\nRouting configuration seed complete.\n'))

    def _get_or_create_department(self, dept_def, now):
        """
        Idempotent department creation using raw SQL (managed=False model).
        """
        try:
            dept = Department.objects.get(name=dept_def['name'])
            return dept, False
        except Department.DoesNotExist:
            dept_id = uuid.uuid4()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO departments (id, name, description, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    [str(dept_id), dept_def['name'], dept_def['description'], True, now, now],
                )
            return Department.objects.get(id=dept_id), True

    def _get_or_create_jurisdiction(self, jur_def, now):
        """
        Idempotent jurisdiction creation using raw SQL (managed=False model).
        boundary is NULL for district-based MVP routing.
        """
        try:
            jur = Jurisdiction.objects.get(name=jur_def['name'], area_type=jur_def['area_type'])
            return jur, False
        except Jurisdiction.DoesNotExist:
            jur_id = uuid.uuid4()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO jurisdictions (id, name, area_type, boundary, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, NULL, %s, %s, %s)
                    """,
                    [str(jur_id), jur_def['name'], jur_def['area_type'], True, now, now],
                )
            return Jurisdiction.objects.get(id=jur_id), True

    def _get_or_create_rule(self, category, department, now):
        """
        Idempotent global category rule creation using raw SQL (managed=False model).
        Global rule: jurisdiction_id = NULL.
        """
        existing = DepartmentCategoryRule.objects.filter(
            department=department,
            category=category,
            jurisdiction__isnull=True,
        ).first()

        if existing:
            return existing, False

        rule_id = uuid.uuid4()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO department_category_rules
                    (id, department_id, category_id, jurisdiction_id, priority_rank, is_active, created_at)
                VALUES (%s, %s, %s, NULL, %s, %s, %s)
                """,
                [str(rule_id), str(department.id), category.id, 1, True, now],
            )
        return DepartmentCategoryRule.objects.get(id=rule_id), True
