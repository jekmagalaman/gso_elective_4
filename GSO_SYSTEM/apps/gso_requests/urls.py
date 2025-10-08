from django.urls import path
from . import views

app_name = "gso_requests"

urlpatterns = [
    # Director
    path('director/requests/', views.director_request_management, name='director_request_management'),
    path('approve/<int:pk>/', views.approve_request, name='approve_request'),

    # GSO Office
    path('management/', views.request_management, name='request_management'),

    # Unit Head
    path('unit-head/management/', views.unit_head_request_management, name='unit_head_request_management'),
    path('unit-head/detail/<int:pk>/', views.unit_head_request_detail, name='unit_head_request_detail'),
    path('unit-head/history/', views.unit_head_request_history, name='unit_head_request_history'),
    path('unit-head/inventory/', views.unit_head_inventory, name='unit_head_inventory'),

    # Personnel
    path('personnel/tasks/', views.personnel_task_management, name='personnel_task_management'),
    path('personnel/task/<int:pk>/', views.personnel_task_detail, name='personnel_task_detail'),
    path('personnel/history/', views.personnel_history, name='personnel_history'),
    path('personnel/inventory/', views.personnel_inventory, name='personnel_inventory'),  # NEW

    # Requestor
    path('requestor/management/', views.requestor_request_management, name='requestor_request_management'),
    path('requestor/add/', views.add_request, name='add_request'),
    path('requestor/cancel/<int:pk>/', views.cancel_request, name='cancel_request'),
    path('requestor/history/', views.requestor_request_history, name='requestor_request_history'),
]
