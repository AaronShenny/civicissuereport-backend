from django.urls import path
from apps.departments import views

urlpatterns = [
    path('category-rules/', views.DepartmentCategoryRuleListCreateView.as_view(), name='department-category-rules'),
    path('category-rules/<uuid:pk>/', views.DepartmentCategoryRuleDetailView.as_view(), name='department-category-rule-detail'),
    path('jurisdictions/', views.JurisdictionListCreateView.as_view(), name='jurisdiction-list'),
    path('jurisdictions/<uuid:pk>/', views.JurisdictionDetailView.as_view(), name='jurisdiction-detail'),
    path('', views.DepartmentListView.as_view(), name='department-list'),
    path('create/', views.DepartmentCreateView.as_view(), name='department-create'),
    path('<uuid:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    path('<uuid:pk>/performance/', views.DepartmentPerformanceView.as_view(), name='department-performance'),
]
