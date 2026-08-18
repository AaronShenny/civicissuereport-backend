from django.urls import path, include
from . import health
from apps.complaints import views as complaint_views

urlpatterns = [
    path('health/', health.health_check, name='health_check'),
    path('users/', include('apps.users.urls')),
    path('departments/', include('apps.departments.urls')),
    path('complaints/', include('apps.complaints.urls')),
    path('categories/', complaint_views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', complaint_views.CategoryDetailView.as_view(), name='category-detail'),

    # Supervisor queues and assignment actions
    path('supervisor/complaints/unassigned/', complaint_views.SupervisorUnassignedQueueView.as_view(), name='supervisor-unassigned-queue'),
    path('supervisor/complaints/', complaint_views.SupervisorDepartmentComplaintsView.as_view(), name='supervisor-department-complaints'),
    path('supervisor/complaints/<uuid:pk>/assign/', complaint_views.SupervisorAssignEmployeeView.as_view(), name='supervisor-assign-employee'),
    path('supervisor/complaints/<uuid:pk>/reassign/', complaint_views.SupervisorReassignEmployeeView.as_view(), name='supervisor-reassign-employee'),

    # Ground-Level Employee actions (Phase 5 & 6)
    path('employee/complaints/', complaint_views.EmployeeAssignedComplaintsView.as_view(), name='employee-assigned-complaints'),
    path('employee/complaints/<uuid:pk>/verify/', complaint_views.EmployeeVerifyComplaintView.as_view(), name='employee-verify-complaint'),
    path('employee/complaints/<uuid:pk>/verification/', complaint_views.EmployeeComplaintVerificationDetailView.as_view(), name='employee-complaint-verification'),
    path('employee/complaints/<uuid:pk>/progress/', complaint_views.EmployeeAddProgressUpdateView.as_view(), name='employee-add-progress'),
    path('employee/complaints/<uuid:pk>/resolve/', complaint_views.EmployeeResolveComplaintView.as_view(), name='employee-resolve-complaint'),
    path('employee/complaints/<uuid:pk>/resolutions/', complaint_views.EmployeeComplaintResolutionsListView.as_view(), name='employee-complaint-resolutions'),

    # Notifications (Phase 3)
    path('notifications/', complaint_views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/unread-count/', complaint_views.NotificationUnreadCountView.as_view(), name='notification-unread-count'),
    path('notifications/read-all/', complaint_views.NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('notifications/<uuid:pk>/read/', complaint_views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
]
