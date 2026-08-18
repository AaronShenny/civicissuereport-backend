from django.urls import path
from apps.departments import views

urlpatterns = [
    path('category-rules/', views.DepartmentCategoryRuleListView.as_view(), name='department-category-rules'),
    path('jurisdictions/', views.JurisdictionListView.as_view(), name='jurisdiction-list'),
    path('', views.DepartmentListView.as_view(), name='department-list'),
    path('create/', views.DepartmentCreateView.as_view(), name='department-create'),
    path('<uuid:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
]
