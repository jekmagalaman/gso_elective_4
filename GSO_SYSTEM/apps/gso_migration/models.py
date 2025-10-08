from django.db import models

TARGET_MODELS = [
    ('gso_inventory.InventoryItem', 'Inventory Items'),
    ('gso_reports.DataMigration', 'Work Accomplishment Reports'),
    ('gso_requests.ServiceRequest', 'Service Requests'),
]


class DataMigration(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='migrations/')
    target_model = models.CharField(max_length=100, choices=TARGET_MODELS)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} → {self.target_model}"
