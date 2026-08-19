from django.db.models import Count, Q
from apps.users.models import Profile, Role
from apps.complaints.models import Complaint
from apps.complaints.reporting import get_filtered_complaints_queryset, get_analytics_data

def get_dashboard_analytics(profile, filters):
    """
    Returns analytics tailored specifically for the Dashboard UI, 
    reusing Phase 14 reporting aggregations where possible.
    """
    queryset = get_filtered_complaints_queryset(profile, filters)
    
    # Reuse base aggregations from Phase 14
    data = get_analytics_data(queryset)
    
    # Add specific metrics needed for DepartmentAdminDashboard
    in_progress = queryset.filter(status='in_progress').count()
    data['summary']['in_progress'] = in_progress
    
    # 2. Employee Workload (Only for Department Admins and Supervisors)
    if profile.role_name in [Role.DEPARTMENT_ADMIN, Role.SUPERVISOR] and profile.department_id:
        employee_stats = Profile.objects.filter(
            department_id=profile.department_id,
            role__role_name=Role.GROUND_LEVEL_EMPLOYEE
        ).annotate(
            assigned=Count('assigned_complaints', filter=Q(assigned_complaints__status__in=['assigned', 'verified'])),
            in_progress=Count('assigned_complaints', filter=Q(assigned_complaints__status='in_progress')),
            resolved=Count('assigned_complaints', filter=Q(assigned_complaints__status__in=['resolved', 'closed']))
        ).values('full_name', 'assigned', 'in_progress', 'resolved').order_by('-assigned')
        
        data['workload'] = list(employee_stats)
    else:
        data['workload'] = []
        
    # 3. System Admin Specific Metrics (User counts)
    if profile.role_name == Role.SYSTEM_ADMIN:
        user_counts = Profile.objects.aggregate(
            total_users=Count('id'),
            citizens=Count('id', filter=Q(role__role_name=Role.CITIZEN)),
            employees=Count('id', filter=Q(role__role_name=Role.GROUND_LEVEL_EMPLOYEE))
        )
        data['users'] = user_counts
        
    return data
