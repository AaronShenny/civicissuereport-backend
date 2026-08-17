from django.urls import path
from apps.complaints import views

urlpatterns = [
    path('', views.ComplaintListCreateView.as_view(), name='complaint-list-create'),
    path('<uuid:pk>/', views.ComplaintDetailView.as_view(), name='complaint-detail'),
    path('<uuid:pk>/route/', views.RouteComplaintView.as_view(), name='complaint-route'),
    path('<uuid:pk>/confirm/', views.CitizenConfirmResolutionView.as_view(), name='complaint-confirm-resolution'),
    path('<uuid:pk>/reject/', views.CitizenRejectResolutionView.as_view(), name='complaint-reject-resolution'),
]
