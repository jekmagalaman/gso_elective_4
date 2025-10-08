from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Unit, Department


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "unit", "department", "account_status", "is_staff")
    list_filter = ("role", "account_status", "unit", "department", "is_staff", "is_superuser")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role & Assignment", {"fields": ("role", "account_status", "unit", "department")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role & Assignment", {"fields": ("role", "account_status", "unit", "department")}),
    )


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
