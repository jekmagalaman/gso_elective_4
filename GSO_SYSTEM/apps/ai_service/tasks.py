# apps/ai_service/tasks.py
from apps.gso_reports.models import WorkAccomplishmentReport, SuccessIndicator
from .utils import generate_war_description, generate_ipmt_summary

# -------------------------------
# Generate WAR AI Description
# -------------------------------
def generate_war_description(war_id: int):
    """
    Generate AI description for a specific Work Accomplishment Report (WAR)
    using the OpenRouter DeepSeek model.
    Updates the WAR.description field directly.
    """
    try:
        war = WorkAccomplishmentReport.objects.get(id=war_id)

        activity_name = war.activity_name or "Miscellaneous"
        unit_name = war.unit.name if war.unit else None
        personnel_names = [p.get_full_name() for p in war.assigned_personnel.all()] if war.assigned_personnel.exists() else None

        description = generate_war_description(
            activity_name=activity_name,
            unit=unit_name,
            personnel_names=personnel_names
        )

        war.description = description
        war.save(update_fields=["description"])
        return description
    except WorkAccomplishmentReport.DoesNotExist:
        return None

# -------------------------------
# Generate IPMT AI Summary
# -------------------------------
def generate_ipmt_summary(unit_name: str, month_filter: str):
    from apps.gso_reports.utils import collect_ipmt_reports
    """
    Generate AI summaries for IPMT rows for a given unit and month.
    Uses all WAR descriptions related to the unit and month.
    Returns a list of updated rows with 'remarks'.
    """
    try:
        year, month_num = map(int, month_filter.split("-"))
    except ValueError:
        return []

    # Collect IPMT rows
    ipmt_rows = collect_ipmt_reports(year, month_num, unit_name)

    updated_rows = []

    for row in ipmt_rows:
        war_id = row.get("war_id")
        description = row.get("description", "")
        indicator_code = row.get("indicator")

        # Generate AI remarks only if there is a description
        if description:
            remarks = generate_ipmt_summary(
                success_indicator=indicator_code,
                war_descriptions=[description]
            )
            row["remarks"] = remarks

        updated_rows.append(row)

    return updated_rows
