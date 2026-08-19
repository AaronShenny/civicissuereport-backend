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


class DepartmentCategoryRuleListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/departments/category-rules/
        - System Admin: all rules.
    POST /api/v1/departments/category-rules/
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsSystemAdmin]
    serializer_class = DepartmentCategoryRuleSerializer
    queryset = DepartmentCategoryRule.objects.all().select_related('department', 'category', 'jurisdiction').order_by('category__name', 'priority_rank')

    def perform_create(self, serializer):
        from rest_framework.exceptions import ValidationError
        import uuid
        from datetime import datetime, timezone
        from apps.users.audit_logger import log_audit_event
        
        department = serializer.validated_data.get('department_id') or serializer.validated_data.get('department')
        category = serializer.validated_data.get('category_id') or serializer.validated_data.get('category')
        jurisdiction = serializer.validated_data.get('jurisdiction_id') or serializer.validated_data.get('jurisdiction')
        
        dept_id = department.id if hasattr(department, 'id') else department
        cat_id = category.id if hasattr(category, 'id') else category
        jur_id = jurisdiction.id if hasattr(jurisdiction, 'id') else jurisdiction
        
        # Prevent duplicate conflicting rules
        if DepartmentCategoryRule.objects.filter(
            department_id=dept_id, category_id=cat_id, jurisdiction_id=jur_id, is_active=True
        ).exists():
            raise ValidationError({'non_field_errors': 'An active routing rule already exists for this combination.'})

        now = datetime.now(timezone.utc)
        rule = serializer.save(id=uuid.uuid4(), created_at=now)

        log_audit_event(
            actor=self.request.user.profile,
            action='category_rule_created',
            entity_type='DepartmentCategoryRule',
            entity_id=str(rule.id),
            old_value=None,
            new_value={'department_id': str(dept_id), 'category_id': str(cat_id), 'jurisdiction_id': str(jur_id) if jur_id else None}
        )

class DepartmentCategoryRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE /api/v1/departments/category-rules/<uuid:pk>/
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsSystemAdmin]
    serializer_class = DepartmentCategoryRuleSerializer
    queryset = DepartmentCategoryRule.objects.all()

    def perform_update(self, serializer):
        from rest_framework.exceptions import ValidationError
        from apps.users.audit_logger import log_audit_event
        
        department = serializer.validated_data.get('department_id') or serializer.validated_data.get('department')
        category = serializer.validated_data.get('category_id') or serializer.validated_data.get('category')
        jurisdiction = serializer.validated_data.get('jurisdiction_id') or serializer.validated_data.get('jurisdiction')
        
        dept_id = department.id if hasattr(department, 'id') else (department or self.get_object().department_id)
        cat_id = category.id if hasattr(category, 'id') else (category or self.get_object().category_id)
        jur_id = jurisdiction.id if hasattr(jurisdiction, 'id') else (jurisdiction or self.get_object().jurisdiction_id)
        
        if DepartmentCategoryRule.objects.filter(
            department_id=dept_id, category_id=cat_id, jurisdiction_id=jur_id, is_active=True
        ).exclude(id=self.get_object().id).exists():
            raise ValidationError({'non_field_errors': 'An active routing rule already exists for this combination.'})

        rule = serializer.save()

        log_audit_event(
            actor=self.request.user.profile,
            action='category_rule_updated',
            entity_type='DepartmentCategoryRule',
            entity_id=str(rule.id),
            old_value={'is_active': self.get_object().is_active, 'priority_rank': self.get_object().priority_rank},
            new_value={'is_active': rule.is_active, 'priority_rank': rule.priority_rank}
        )

    def perform_destroy(self, instance):
        from apps.users.audit_logger import log_audit_event
        # Soft delete
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        log_audit_event(
            actor=self.request.user.profile,
            action='category_rule_deactivated',
            entity_type='DepartmentCategoryRule',
            entity_id=str(instance.id),
            old_value={'is_active': True},
            new_value={'is_active': False}
        )



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
        from django.db.models import Count
        profile = self.request.user
        queryset = Department.objects.all().order_by('name')
        if not profile.is_system_admin:
            # Supervisors and Department Admins see only their own department.
            if profile.department_id:
                queryset = queryset.filter(id=profile.department_id)
            else:
                queryset = queryset.none()
        
        queryset = queryset.annotate(
            employee_count=Count('profiles', distinct=True),
            complaint_count=Count('assigned_complaints', distinct=True)
        )
        return queryset


class DepartmentCreateView(generics.CreateAPIView):
    """
    POST /api/v1/departments/
        System Admin only.
    """

    permission_classes = [IsAuthenticatedViaSupabase, IsSystemAdmin]
    serializer_class = DepartmentCreateUpdateSerializer

    def perform_create(self, serializer):
        import uuid
        from datetime import datetime, timezone
        from rest_framework.exceptions import ValidationError
        from apps.users.audit_logger import log_audit_event

        name = serializer.validated_data.get('name')
        if Department.objects.filter(name__iexact=name).exists():
            raise ValidationError({'name': 'A department with this name already exists.'})

        now = datetime.now(timezone.utc)
        department = serializer.save(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            is_active=True
        )

        log_audit_event(
            actor=self.request.user.profile,
            action='department_created',
            entity_type='Department',
            entity_id=str(department.id),
            old_value=None,
            new_value={
                'id': str(department.id),
                'name': department.name,
                'description': department.description,
                'is_active': department.is_active,
            }
        )


class DepartmentDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/departments/<uuid:pk>/
        - System Admin: any department.
        - Department Admin / Supervisor: own department only.
    PATCH/PUT /api/v1/departments/<uuid:pk>/
        - System Admin only.
    """

    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticatedViaSupabase(), IsSystemAdmin()]
        return [IsAuthenticatedViaSupabase(), IsSupervisorOrAbove()]

    def get_queryset(self):
        from django.db.models import Count
        profile = self.request.user
        queryset = Department.objects.all().order_by('name')
        if not profile.is_system_admin:
            if profile.department_id:
                queryset = queryset.filter(id=profile.department_id)
            else:
                queryset = queryset.none()
        
        queryset = queryset.annotate(
            employee_count=Count('profiles', distinct=True),
            complaint_count=Count('assigned_complaints', distinct=True)
        )
        return queryset

    def perform_update(self, serializer):
        from rest_framework.exceptions import ValidationError
        from datetime import datetime, timezone
        from apps.users.models import Profile
        from apps.departments.models import DepartmentCategoryRule
        from apps.complaints.models import Complaint
        from apps.users.audit_logger import log_audit_event
        
        instance = self.get_object()
        old_active = instance.is_active
        new_active = self.request.data.get('is_active', old_active)

        if isinstance(new_active, str):
            new_active = new_active.lower() in ['true', '1', 'yes']

        # Safety Check for Deactivation (non-destructive)
        if old_active and not new_active:
            force = self.request.data.get('force', False) or self.request.query_params.get('force', False)
            if isinstance(force, str):
                force = force.lower() in ['true', '1', 'yes']

            if not force:
                active_profiles = Profile.objects.filter(
                    department_id=instance.id,
                    account_status='active'
                ).select_related('role')
                
                active_employees = active_profiles.filter(role__role_name='ground_level_employee')
                active_supervisors = active_profiles.filter(role__role_name='supervisor')
                active_admins = active_profiles.filter(role__role_name='department_admin')
                
                active_rules = DepartmentCategoryRule.objects.filter(
                    department_id=instance.id,
                    is_active=True
                )
                
                pending_complaints = Complaint.objects.filter(
                    assigned_department_id=instance.id
                ).exclude(status__in=['resolved', 'closed', 'invalid'])
                
                errors = []
                if active_employees.exists():
                    errors.append(f"{active_employees.count()} active employee(s)")
                if active_supervisors.exists():
                    errors.append(f"{active_supervisors.count()} active supervisor(s)")
                if active_admins.exists():
                    errors.append(f"{active_admins.count()} active department admin(s)")
                if active_rules.exists():
                    errors.append(f"{active_rules.count()} active routing rule(s)")
                if pending_complaints.exists():
                    errors.append(f"{pending_complaints.count()} unresolved complaint(s)")
                    
                if errors:
                    raise ValidationError(
                        f"Cannot deactivate department: {', '.join(errors)} remaining."
                    )
            else:
                # Force deactivation: auto-deactivate active routing rules for this department
                DepartmentCategoryRule.objects.filter(
                    department_id=instance.id,
                    is_active=True
                ).update(is_active=False)

        old_values = {
            'name': instance.name,
            'description': instance.description,
            'is_active': instance.is_active,
        }

        department = serializer.save(updated_at=datetime.now(timezone.utc))

        new_values = {
            'name': department.name,
            'description': department.description,
            'is_active': department.is_active,
        }

        if old_active and not new_active:
            action = 'department_deactivated'
        elif not old_active and new_active:
            action = 'department_reactivated'
        else:
            action = 'department_updated'

        log_audit_event(
            actor=self.request.user.profile,
            action=action,
            entity_type='Department',
            entity_id=str(department.id),
            old_value=old_values,
            new_value=new_values
        )


class DepartmentPerformanceView(APIView):
    """
    GET /api/v1/admin/departments/<uuid:pk>/performance/
        - System Admin: any department.
        - Department Admin / Supervisor: own department only.
    """
    permission_classes = [IsAuthenticatedViaSupabase, IsSupervisorOrAbove]

    def get(self, request, pk):
        profile = request.user
        
        if not profile.is_system_admin:
            if str(profile.department_id) != str(pk):
                return Response(
                    {'detail': 'You do not have permission to view other department performance.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        try:
            department = Department.objects.get(id=pk)
        except Department.DoesNotExist:
            return Response({'detail': 'Department not found.'}, status=status.HTTP_404_NOT_FOUND)

        from apps.complaints.models import Complaint, ComplaintStatusHistory
        from django.db.models import Count, Q, Avg, Min, Max, F, ExpressionWrapper, fields, Subquery, OuterRef
        
        filters = request.query_params
        queryset = Complaint.objects.filter(assigned_department_id=pk)

        # Filters
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        if start_date:
            queryset = queryset.filter(submitted_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(submitted_at__lte=end_date)
        
        category = filters.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
            
        district = filters.get('district')
        if district:
            queryset = queryset.filter(district__iexact=district)

        priority = filters.get('priority')
        if priority:
            queryset = queryset.filter(priority_category__iexact=priority)

        status_filter = filters.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        total_count = queryset.count()
        pending_count = queryset.filter(status__in=['submitted', 'under_verification', 'assigned', 'verified', 'in_progress']).count()
        in_progress_count = queryset.filter(status='in_progress').count()
        resolved_count = queryset.filter(status='resolved').count()
        closed_count = queryset.filter(status='closed').count()
        invalid_count = queryset.filter(status='invalid').count()
        
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        week_count = queryset.filter(submitted_at__gte=start_of_week).count()
        month_count = queryset.filter(submitted_at__gte=start_of_month).count()

        priority_breakdown = list(queryset.values('priority_category').annotate(count=Count('id')).order_by('-count'))
        priority_data = {item['priority_category'] or 'Unassessed': item['count'] for item in priority_breakdown}

        category_breakdown = list(queryset.values('category__name').annotate(count=Count('id')).order_by('-count'))
        category_data = {item['category__name'] or 'Uncategorized': item['count'] for item in category_breakdown}

        district_breakdown = list(queryset.values('district').annotate(count=Count('id')).order_by('-count'))
        district_data = {item['district'] or 'Unknown': item['count'] for item in district_breakdown}

        resolved_history_subquery = ComplaintStatusHistory.objects.filter(
            complaint=OuterRef('pk'),
            new_status='resolved'
        ).order_by('-changed_at').values('changed_at')[:1]
        
        resolved_qs = queryset.filter(status__in=['resolved', 'closed']).annotate(
            resolved_at=Subquery(resolved_history_subquery)
        ).exclude(resolved_at__isnull=True)
        
        resolved_durations = resolved_qs.annotate(
            duration=ExpressionWrapper(F('resolved_at') - F('submitted_at'), output_field=fields.DurationField())
        )
        
        avg_res = resolved_durations.aggregate(
            avg_time=Avg('duration'),
            min_time=Min('duration'),
            max_time=Max('duration')
        )
        
        avg_time = avg_res['avg_time']
        min_time = avg_res['min_time']
        max_time = avg_res['max_time']
        
        resolved_with_expected = resolved_durations.exclude(expected_completion_date__isnull=True)
        total_with_expected = resolved_with_expected.count()
        resolved_on_time = 0
        if total_with_expected > 0:
            resolved_on_time = resolved_with_expected.annotate(
                is_on_time=ExpressionWrapper(
                    Q(resolved_at__lte=F('expected_completion_date')),
                    output_field=fields.BooleanField()
                )
            ).filter(is_on_time=True).count()

        from apps.users.models import Profile, Role
        employees = Profile.objects.filter(
            department_id=pk,
            role__role_name=Role.GROUND_LEVEL_EMPLOYEE
        ).annotate(
            assigned=Count('assigned_complaints', filter=Q(assigned_complaints__status='assigned')),
            in_progress=Count('assigned_complaints', filter=Q(assigned_complaints__status='in_progress')),
            resolved=Count('assigned_complaints', filter=Q(assigned_complaints__status='resolved')),
            closed=Count('assigned_complaints', filter=Q(assigned_complaints__status='closed')),
            invalid=Count('assigned_complaints', filter=Q(assigned_complaints__status='invalid')),
        ).values('full_name', 'role__role_name', 'assigned', 'in_progress', 'resolved', 'closed', 'invalid')
        
        employee_workload = []
        for emp in employees:
            emp_resolved_qs = resolved_durations.filter(assigned_employee__full_name=emp['full_name'])
            emp_avg_time = emp_resolved_qs.aggregate(avg_time=Avg('duration'))['avg_time']
            
            employee_workload.append({
                'name': emp['full_name'],
                'role': emp['role__role_name'],
                'assigned': emp['assigned'],
                'in_progress': emp['in_progress'],
                'resolved': emp['resolved'],
                'closed': emp['closed'],
                'invalid': emp['invalid'],
                'avg_resolution_time': str(emp_avg_time) if emp_avg_time else None
            })

        avg_res_str = str(avg_time) if avg_time else None
        min_res_str = str(min_time) if min_time else None
        max_res_str = str(max_time) if max_time else None

        response_data = {
            'department_id': str(department.id),
            'department_name': department.name,
            'description': department.description,
            'is_active': department.is_active,
            'volume': {
                'total': total_count,
                'week': week_count,
                'month': month_count,
                'pending': pending_count,
                'in_progress': in_progress_count,
                'resolved': resolved_count,
                'closed': closed_count,
                'invalid': invalid_count,
            },
            'priority_breakdown': priority_data,
            'category_breakdown': category_data,
            'district_breakdown': district_data,
            'resolution_performance': {
                'avg_resolution_time': avg_res_str,
                'fastest_resolution': min_res_str,
                'slowest_resolution': max_res_str,
                'total_with_expected': total_with_expected,
                'resolved_on_time': resolved_on_time,
            },
            'employee_workload': employee_workload,
        }
        return Response(response_data, status=status.HTTP_200_OK)

class JurisdictionListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/departments/jurisdictions/
    POST /api/v1/departments/jurisdictions/
    """
    serializer_class = JurisdictionSerializer
    queryset = Jurisdiction.objects.all().order_by('name')

    def get_permissions(self):
        if self.request.method == 'GET':
            from core.permissions.roles import IsDepartmentAdminOrSystemAdmin
            return [IsAuthenticatedViaSupabase(), IsDepartmentAdminOrSystemAdmin()]
        return [IsAuthenticatedViaSupabase(), IsSystemAdmin()]

    def perform_create(self, serializer):
        from rest_framework.exceptions import ValidationError
        import uuid
        from datetime import datetime, timezone
        from apps.users.audit_logger import log_audit_event
        
        name = serializer.validated_data.get('name')
        if Jurisdiction.objects.filter(name__iexact=name, is_active=True).exists():
            raise ValidationError({'name': 'An active jurisdiction with this name already exists.'})

        now = datetime.now(timezone.utc)
        jurisdiction = serializer.save(id=uuid.uuid4(), created_at=now, updated_at=now)

        log_audit_event(
            actor=self.request.user.profile,
            action='jurisdiction_created',
            entity_type='Jurisdiction',
            entity_id=str(jurisdiction.id),
            old_value=None,
            new_value={'name': jurisdiction.name}
        )

class JurisdictionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE /api/v1/departments/jurisdictions/<uuid:pk>/
    """
    serializer_class = JurisdictionSerializer
    queryset = Jurisdiction.objects.all()

    def get_permissions(self):
        if self.request.method == 'GET':
            from core.permissions.roles import IsDepartmentAdminOrSystemAdmin
            return [IsAuthenticatedViaSupabase(), IsDepartmentAdminOrSystemAdmin()]
        return [IsAuthenticatedViaSupabase(), IsSystemAdmin()]

    def perform_update(self, serializer):
        from rest_framework.exceptions import ValidationError
        from datetime import datetime, timezone
        from apps.users.audit_logger import log_audit_event
        
        name = serializer.validated_data.get('name')
        if name:
            if Jurisdiction.objects.filter(name__iexact=name, is_active=True).exclude(id=self.get_object().id).exists():
                raise ValidationError({'name': 'An active jurisdiction with this name already exists.'})

        now = datetime.now(timezone.utc)
        jurisdiction = serializer.save(updated_at=now)

        log_audit_event(
            actor=self.request.user.profile,
            action='jurisdiction_updated',
            entity_type='Jurisdiction',
            entity_id=str(jurisdiction.id),
            old_value={'name': self.get_object().name, 'is_active': self.get_object().is_active},
            new_value={'name': jurisdiction.name, 'is_active': jurisdiction.is_active}
        )

    def perform_destroy(self, instance):
        from datetime import datetime, timezone
        from apps.users.audit_logger import log_audit_event
        # Soft delete
        instance.is_active = False
        instance.updated_at = datetime.now(timezone.utc)
        instance.save()
        log_audit_event(
            actor=self.request.user.profile,
            action='jurisdiction_deactivated',
            entity_type='Jurisdiction',
            entity_id=str(instance.id),
            old_value={'is_active': True},
            new_value={'is_active': False}
        )
