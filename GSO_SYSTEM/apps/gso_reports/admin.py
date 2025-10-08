from django.contrib import admin
from .models import WorkAccomplishmentReport, SuccessIndicator, ActivityName


@admin.register(ActivityName)
class ActivityNameAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name", "keywords")
    list_filter = ("is_active",)


@admin.register(SuccessIndicator)
class SuccessIndicatorAdmin(admin.ModelAdmin):
    list_display = ("code", "unit", "description", "activity_name", "is_active")
    list_filter = ("unit", "is_active")
    search_fields = ("code", "description", "activity_name__name")


@admin.register(WorkAccomplishmentReport)
class WorkAccomplishmentReportAdmin(admin.ModelAdmin):
    list_display = ("activity_name", "unit", "date_started", "status", "total_cost")
    list_filter = ("unit", "status", "date_started")
    search_fields = ("activity_name", "description")
