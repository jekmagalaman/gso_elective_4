from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = "gso_accounts"

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='gso_accounts:login'), name='logout'),

    # Role-based redirect after login
    path('redirect/', views.role_redirect, name='role_redirect'),

    # Dashboard redirects for roles (optional, mostly for links)
    path('dashboard/gso/', views.gso_dashboard, name='gso-dashboard'),
    path('dashboard/unit-head/', views.unit_head_dashboard, name='unit-head-dashboard'),
    path('dashboard/personnel/', views.personnel_dashboard, name='personnel-dashboard'),
    # This is now optional; requestor will be redirected directly to request management
    #path('dashboard/requestor/', views.requestor_dashboard, name='requestor-dashboard'),

    # GSO Office Account Management
    path('accounts/', views.account_management, name='account_management'),
    path('accounts/add/', views.add_user, name='add_user'),
    path('accounts/edit/<int:user_id>/', views.edit_user, name='edit_user'),

    # Requestor Views
    path('requestor/account/', views.requestor_account, name='requestor_account'),
    path('requestor/profile/', views.profile, name='requestor_profile'),

    # AJAX endpoint
    path('search-personnel/', views.search_personnel, name='search_personnel'),
]
