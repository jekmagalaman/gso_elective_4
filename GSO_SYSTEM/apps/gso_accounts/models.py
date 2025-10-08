from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError

class Unit(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = [
        ('director', 'Director'),
        ('gso', 'GSO Office'),
        ('unit_head', 'Unit Head'),
        ('personnel', 'Personnel'),
        ('requestor', 'Requestor'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    account_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Relations
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True)

    # ✅ Fix clashes with Django auth
    groups = models.ManyToManyField(
        Group,
        related_name="gso_user_set",
        blank=True,
        help_text="The groups this user belongs to.",
        related_query_name="gso_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="gso_user_set",
        blank=True,
        help_text="Specific permissions for this user.",
        related_query_name="gso_user",
    )

    def clean(self):
        if self.role in ["director", "gso"] and (self.unit or self.department):
            raise ValidationError(f"{self.get_role_display()} should not be assigned to a unit or department.")

        if self.role in ["unit_head", "personnel"] and not self.unit:
            raise ValidationError(f"{self.get_role_display()} must be assigned to a unit.")

        if self.role == "requestor" and not self.department:
            raise ValidationError("Requestor accounts must belong to a department.")

    def __str__(self):
        if self.role == "requestor" and self.department:
            return f"{self.department.name} (Requestor)"
        return f"{self.get_full_name()} ({self.get_role_display()})"
