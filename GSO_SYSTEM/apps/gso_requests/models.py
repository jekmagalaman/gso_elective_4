from django.db import models
from django.conf import settings
from apps.gso_accounts.models import Unit, Department
from apps.gso_inventory.models import InventoryItem


class ServiceRequest(models.Model):
    """
    Represents a service request submitted by a user (requestor).
    Tracks workflow status, assigned personnel, and requested materials.
    """

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("In Progress", "In Progress"),
        ("Done for Review", "Done for Review"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    # Who made the request
    requestor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requests"
    )
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    # If request is made on behalf of someone else
    custom_full_name = models.CharField(max_length=255, blank=True, null=True)
    custom_email = models.EmailField(blank=True, null=True)
    custom_contact_number = models.CharField(max_length=50, blank=True, null=True)

    # Details
    activity_name = models.CharField(  # ✅ Auto-filled from keywords/AI
        max_length=255,
        blank=True,
        null=True,
        help_text="Short standardized activity name (auto-mapped from description)"
    )
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Assignment
    assigned_personnel = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="assigned_requests"
    )

    # Materials used
    materials = models.ManyToManyField(
        InventoryItem,
        through="RequestMaterial",
        blank=True,
        related_name="requests"
    )

    def __str__(self):
        display_name = self.custom_full_name or self.requestor.get_full_name()
        return f"Request #{self.id} by {display_name} - {self.unit.name}"

    @property
    def assigned_personnel_names(self):
        personnel = self.assigned_personnel.all()
        if personnel.exists():
            return ", ".join([p.get_full_name() or p.username for p in personnel])
        return ""


class RequestMaterial(models.Model):
    """Through model for materials used in a request."""
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE)
    material = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.material.name} x {self.quantity} (Request #{self.request.id})"


class TaskReport(models.Model):
    """Individual report written by personnel assigned to a request."""
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="reports")
    personnel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    report_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TaskReport by {self.personnel} (Request #{self.request.id})"
