from apps.users.models import Department, Profile, Role
from apps.departments.models import Jurisdiction, DepartmentCategoryRule
from apps.complaints.models import ComplaintCategory

print("=== DEPARTMENTS ===")
for d in Department.objects.all():
    print(f"- {d.name} (active: {d.is_active})")

print("\n=== COMPLAINT CATEGORIES ===")
for c in ComplaintCategory.objects.all():
    print(f"- {c.id}: {c.name} (active: {c.is_active})")

print("\n=== JURISDICTIONS ===")
for j in Jurisdiction.objects.all():
    print(f"- {j.name} ({j.area_type}, active: {j.is_active})")

print("\n=== DEPARTMENT CATEGORY RULES ===")
for r in DepartmentCategoryRule.objects.all():
    jur_name = r.jurisdiction.name if r.jurisdiction else 'Global'
    print(f"- {r.category.name} -> {r.department.name} | Jurisdiction: {jur_name} | Active: {r.is_active}")

print("\n=== PROFILES ===")
for p in Profile.objects.filter(role__role_name__in=[Role.SUPERVISOR, Role.GROUND_LEVEL_EMPLOYEE]):
    dept_name = p.department.name if p.department else 'None'
    print(f"- {p.full_name} ({p.role.role_name}) | Dept: {dept_name}")
