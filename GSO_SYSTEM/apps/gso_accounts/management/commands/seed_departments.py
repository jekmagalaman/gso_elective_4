from django.core.management.base import BaseCommand
from apps.gso_accounts.models import Department

class Command(BaseCommand):
    help = "Seed initial departments for requestors"

    def handle(self, *args, **kwargs):
        departments = [
            "Registrar",
            "Cashier",
            "Accounting",
            "Library",
            "HR Office",
            "IT Department",
        ]
        for name in departments:
            dept, created = Department.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created department: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Already exists: {name}"))

        self.stdout.write(self.style.SUCCESS("Departments seeding completed."))
