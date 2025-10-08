from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', lambda request: redirect('gso_accounts:login'), name='home'),
    path('admin/', admin.site.urls),
    path('gso_accounts/', include('apps.gso_accounts.urls', namespace='gso_accounts')),
    path('gso_requests/', include('apps.gso_requests.urls', namespace='gso_requests')),
    path('gso_inventory/', include('apps.gso_inventory.urls', namespace='gso_inventory')),
    path('gso_reports/', include('apps.gso_reports.urls', namespace='gso_reports')),
    path('ai/', include('apps.ai_service.urls', namespace='ai_service')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
]

