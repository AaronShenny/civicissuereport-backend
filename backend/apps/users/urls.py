from django.urls import path
from apps.users import views

urlpatterns = [
    path('me/', views.CurrentUserProfileView.as_view(), name='current-user-profile'),
    path('me/role/', views.CurrentUserRoleView.as_view(), name='current-user-role'),
    path('me/department/', views.CurrentUserDepartmentView.as_view(), name='current-user-department'),
    path('department-members/', views.DepartmentMembersView.as_view(), name='department-members'),
    path('<uuid:pk>/', views.ProfileDetailView.as_view(), name='profile-detail'),
]
