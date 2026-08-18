from django.urls import path
from apps.users import views

urlpatterns = [
    path('me/', views.CurrentUserProfileView.as_view(), name='current-user-profile'),
    path('me/role/', views.CurrentUserRoleView.as_view(), name='current-user-role'),
    path('roles/', views.RoleListView.as_view(), name='role-list'),
    path('me/department/', views.CurrentUserDepartmentView.as_view(), name='current-user-department'),
    path('department-members/', views.DepartmentMembersView.as_view(), name='department-members'),
    path('employees/', views.EmployeeCreateView.as_view(), name='employee-create'),
    path('<uuid:pk>/transfer-location/', views.EmployeeLocationTransferView.as_view(), name='employee-transfer-location'),
    path('<uuid:pk>/transfer-department/', views.EmployeeDepartmentTransferView.as_view(), name='employee-transfer-department'),
    path('<uuid:pk>/', views.ProfileDetailView.as_view(), name='profile-detail'),
]
