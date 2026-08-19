from django.urls import path
from apps.complaints import views

urlpatterns = [
    path('', views.ComplaintListCreateView.as_view(), name='complaint-list-create'),
    path('public/<str:complaint_number>/', views.PublicComplaintTrackingView.as_view(), name='complaint-public-track'),
    path('<uuid:pk>/', views.ComplaintDetailView.as_view(), name='complaint-detail'),
    path('<uuid:pk>/staff/', views.StaffComplaintDetailView.as_view(), name='complaint-detail-staff'),
    path('<uuid:pk>/route/', views.RouteComplaintView.as_view(), name='complaint-route'),
    path('<uuid:pk>/confirm/', views.CitizenConfirmResolutionView.as_view(), name='complaint-confirm-resolution'),
    path('<uuid:pk>/reject/', views.CitizenRejectResolutionView.as_view(), name='complaint-reject-resolution'),
]
