# apps/gso_reports/utils.py
from django.utils import timezone
from datetime import datetime
from apps.gso_accounts.models import Unit, User
from apps.gso_requests.models import ServiceRequest
from .models import WorkAccomplishmentReport, ActivityName, SuccessIndicator, IPMT
import io
import calendar
import pandas as pd


from django.apps import apps
from django.db import models


# -------------------------------
# Normalize Reports (for Accomplishment Report)
# -------------------------------
def normalize_report(obj):
    if isinstance(obj, ServiceRequest):
        assigned = obj.assigned_personnel.all()
        personnel_list = [p.get_full_name() or p.username for p in assigned] if assigned.exists() else ["Unassigned"]

        return {
            "type": "ServiceRequest",
            "source": "Live",
            "requesting_office": obj.department.name if obj.department else "",
            "description": obj.description,
            "unit": obj.unit.name if obj.unit else "",
            "date": obj.created_at,
            "personnel": personnel_list,
            "status": obj.status,
            "rating": getattr(obj, "rating", None),
            "request": obj,  # ✅ Added for template check {% if report.request %}
        }

    elif isinstance(obj, WorkAccomplishmentReport):
        date_value = obj.date_started
        if isinstance(date_value, datetime) and timezone.is_naive(date_value):
            date_value = timezone.make_aware(date_value)
        elif not isinstance(date_value, datetime):
            date_value = timezone.make_aware(datetime.combine(date_value, datetime.min.time()))

        assigned = obj.assigned_personnel.all()
        personnel_list = [p.get_full_name() or p.username for p in assigned] if assigned.exists() else ["Unassigned"]

        return {
            "type": "WorkAccomplishmentReport",
            "source": "Live" if obj.request else "Migrated",
            "requesting_office": obj.request.department.name if obj.request and obj.request.department else getattr(obj, "requesting_office", ""),
            "description": obj.description,
            "unit": obj.request.unit.name if obj.request and obj.request.unit else (obj.unit.name if obj.unit else ""),
            "date": date_value,
            "personnel": personnel_list,
            "status": obj.status or "Completed",
            "rating": getattr(obj, "rating", None),
            "request": obj.request,  # ✅ Added for template check
        }


# -------------------------------
# Activity Name Mapper
# -------------------------------
def map_activity_name(description: str):
    if not description:
        return ActivityName.objects.filter(name="Miscellaneous").first()

    description = description.lower()

    for activity in ActivityName.objects.all():
        if any(kw in description for kw in activity.keyword_list()):
            return activity

    return ActivityName.objects.filter(name="Miscellaneous").first()


def map_activity_name_from_reports(service_request):
    task_reports_text = " ".join([t.report_text for t in service_request.reports.all()])
    return map_activity_name(task_reports_text) or map_activity_name(service_request.description)


# -------------------------------
# Collect IPMT Reports (Indicator → Accomplishment → Remarks)
# -------------------------------
def collect_ipmt_reports(year: int, month_num: int, unit_name: str = None, personnel_names: list = None):
    from apps.ai_service.tasks import generate_ipmt_summary
    """
    Collect IPMT preview rows using activity_name → SuccessIndicator mapping per personnel.

    Returns a list of dicts per personnel:
    [
        {
            "personnel": str,
            "rows": [
                {
                    "indicator": str,
                    "description": str,  # compiled from WAR(s), AI-generated if multiple
                    "remarks": str,      # auto-filled from description
                    "war_ids": list      # list of contributing WAR IDs
                }
            ]
        }
    ]
    """

    result = []

    # 1. Get unit
    try:
        unit = Unit.objects.get(name__iexact=unit_name)
    except Unit.DoesNotExist:
        return []

    # 2. Filter personnel
    if personnel_names and "all" not in [p.lower() for p in personnel_names]:
        users = User.objects.filter(
            first_name__in=[p.split()[0].capitalize() for p in personnel_names],
            unit=unit
        )
    else:
        users = User.objects.filter(unit=unit, role="personnel")

    # 3. Filter WARs for this unit/month
    wars = WorkAccomplishmentReport.objects.filter(
        unit=unit,
        date_started__year=year,
        date_started__month=month_num
    ).prefetch_related("assigned_personnel").select_related("activity_name")

    # 4. Get active SuccessIndicators for the unit
    indicators = SuccessIndicator.objects.filter(unit=unit, is_active=True)

    for user in users:
        personnel_rows = []

        for indicator in indicators:
            # Filter WARs assigned to this user and matching the indicator
            matched_wars = [
                w for w in wars
                if user in w.assigned_personnel.all()
                and w.activity_name and w.activity_name.name == indicator.name
            ]

            if not matched_wars:
                description = ""
                war_ids = []
            elif len(matched_wars) == 1:
                description = matched_wars[0].description
                war_ids = [matched_wars[0].id]
            else:
                war_descriptions = [w.description for w in matched_wars if w.description]
                description = generate_ipmt_summary(indicator.name, war_descriptions)
                war_ids = [w.id for w in matched_wars]

            personnel_rows.append({
                "indicator": indicator.code,
                "description": description,
                "remarks": description,  # auto-fill remarks
                "war_ids": war_ids
            })

        result.append({
            "personnel": user.get_full_name() or user.username,
            "rows": personnel_rows
        })

    return result

# -------------------------------
# Generate IPMT Excel
# -------------------------------
def generate_ipmt_excel(month_filter: str, unit_name: str = None, personnel_names: list = None):
    """
    Generate an Excel file for IPMT reports.
    - One sheet per personnel
    - Columns: Indicator, Accomplishment, Remarks
    """
    try:
        year, month_num = map(int, month_filter.split("-"))  # expects "YYYY-MM"
    except ValueError:
        raise ValueError("Month filter must be in 'YYYY-MM' format.")

    if not personnel_names or "all" in [p.lower() for p in personnel_names]:
        # Get all unique personnel with WARs this month
        personnel_names = set()
        wars = WorkAccomplishmentReport.objects.filter(
            date_started__year=year,
            date_started__month=month_num,
        )
        if unit_name and unit_name.lower() != "all":
            wars = wars.filter(unit__name__iexact=unit_name)
        for war in wars:
            for p in war.assigned_personnel.all():
                personnel_names.add(p.get_full_name() or p.username)
        personnel_names = list(personnel_names)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        for person in personnel_names:
            reports = collect_ipmt_reports(year, month_num, unit_name, [person])
            df = pd.DataFrame(reports)

            if df.empty:
                df = pd.DataFrame([{"indicator": "N/A", "description": "No reports", "remarks": ""}])

            # Match your sample format: Indicator → Accomplishment → Remarks
            df = df.rename(columns={
                "indicator": "Success Indicator",
                "description": "Accomplishment",
                "remarks": "Remarks"
            })

            sheet_title = (person[:30] if len(person) > 30 else person) or "Unassigned"
            df.to_excel(writer, index=False, sheet_name=sheet_title)

            worksheet = writer.sheets[sheet_title]
            worksheet.write(0, 4, f"Month: {calendar.month_name[month_num]} {year}")
            worksheet.write(1, 4, f"Personnel: {person}")
            if unit_name:
                worksheet.write(2, 4, f"Unit: {unit_name}")

    buffer.seek(0)

    from openpyxl import load_workbook
    wb = load_workbook(buffer)

    return wb

















def process_migration(file_path, target_model):
    """
    Reads Excel/CSV and inserts data into the target model.
    Works whether target_model is a string or a model class.
    """
    # Auto-detect file type
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # 🔹 If we got a string, resolve it to model class
    if isinstance(target_model, str):
        app_label, model_name = target_model.split(".")
        model_class = apps.get_model(app_label, model_name)
    elif isinstance(target_model, models.Model):
        model_class = target_model.__class__
    else:
        model_class = target_model   # already a class

    # Filter only valid fields to avoid unexpected columns
    valid_fields = {f.name for f in model_class._meta.get_fields()}

    for _, row in df.iterrows():
        data = {k: v for k, v in row.to_dict().items() if k in valid_fields}
        model_class.objects.create(**data)