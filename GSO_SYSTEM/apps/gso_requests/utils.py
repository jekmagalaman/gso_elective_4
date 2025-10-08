# apps/gso_requests/utils.py
from django.db.models import Q
from apps.gso_requests.models import ServiceRequest
from apps.gso_inventory.models import InventoryItem
from apps.gso_reports.models import WorkAccomplishmentReport
from apps.gso_reports.utils import map_activity_name
from apps.ai_service.utils import generate_war_description  # AI util
from django.utils import timezone
import threading


# -------------------------------
# Request Filtering Helper
# -------------------------------
def filter_requests(queryset, search_query=None, unit_filter=None, status_filter=None):
    if search_query:
        queryset = queryset.filter(
            Q(requestor__username__icontains=search_query) |
            Q(requestor__first_name__icontains=search_query) |
            Q(requestor__last_name__icontains=search_query) |
            Q(unit__name__icontains=search_query) |
            Q(requestor__department__name__icontains=search_query)
        )
    if unit_filter:
        try:
            queryset = queryset.filter(unit_id=int(unit_filter))
        except ValueError:
            pass
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    return queryset


# -------------------------------
# Inventory Helper
# -------------------------------
def get_unit_inventory(unit, search_query=None):
    materials = InventoryItem.objects.filter(is_active=True, owned_by=unit)
    if search_query:
        materials = materials.filter(
            Q(name__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    return materials


# -------------------------------
# WAR Creation Helper (Non-blocking AI description)
# -------------------------------
def create_war_from_request(request):
    """
    Auto-generate a Work Accomplishment Report (WAR) when a request is completed.
    Generates AI description in a background thread to avoid blocking the request.
    """
    # Try to map activity name from reports/description
    task_reports_text = " ".join([t.report_text for t in request.reports.all()])
    activity = map_activity_name(task_reports_text) or map_activity_name(request.description)

    war, created = WorkAccomplishmentReport.objects.get_or_create(
        request=request,
        defaults={
            "date_started": request.created_at.date(),
            "date_completed": timezone.now().date(),
            "status": "Completed",
            "activity_name": activity.name if activity else "Miscellaneous",
            "unit": request.unit,
        }
    )

    # ✅ Ensure WAR is linked to the ServiceRequest
    if war.request_id != request.id:
        war.request = request
        war.save(update_fields=["request"])

    # ✅ Copy assigned personnel to WAR
    if request.assigned_personnel.exists():
        war.assigned_personnel.set(request.assigned_personnel.all())

    # ---------------------------
    # Generate AI description asynchronously
    # ---------------------------
    def generate_description_thread(war_instance, req):
        war_instance.description = generate_war_description(req)
        war_instance.save(update_fields=["description"])

    # Run AI generation in background thread
    threading.Thread(
        target=generate_description_thread,
        args=(war, request),
        daemon=True
    ).start()

    return war
