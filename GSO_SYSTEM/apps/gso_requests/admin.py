from django.contrib import admin
from .models import ServiceRequest, RequestMaterial, TaskReport

admin.site.register(ServiceRequest)
admin.site.register(RequestMaterial)
admin.site.register(TaskReport)
