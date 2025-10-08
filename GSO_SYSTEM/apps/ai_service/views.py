from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import AIReportSummary
from apps.gso_reports.models import WorkAccomplishmentReport
from .tasks import generate_war_description, generate_ipmt_summary


@login_required
def ai_summary_list(request):
    """
    List all AI-generated summaries (for Director / GSO staff).
    """
    summaries = AIReportSummary.objects.select_related("report", "generated_by").all().order_by("-created_at")
    return render(request, "ai_service/ai_summary_list.html", {"summaries": summaries})


@login_required
def ai_summary_detail(request, report_id):
    """
    View AI-generated summaries for a specific Work Accomplishment Report (WAR).
    """
    report = get_object_or_404(WorkAccomplishmentReport, id=report_id)
    summaries = report.ai_summaries.all()
    return render(request, "ai_service/ai_summary_detail.html", {"report": report, "summaries": summaries})


@login_required
def generate_ai_summary(request, report_id):
    """
    Trigger Celery task to generate AI summary for a WAR.
    """
    report = get_object_or_404(WorkAccomplishmentReport, id=report_id)

    if request.method == "POST":
        generate_war_description.delay(report.id)  # async task
        messages.success(request, f"AI summary generation started for WAR #{report.id}.")
        return redirect("ai_service:ai_summary_detail", report_id=report.id)

    return render(request, "ai_service/generate_ai_summary.html", {"report": report})


@login_required
def generate_ipmt_ai_summary(request, unit_name, month_filter):
    """
    Trigger Celery task to generate AI summary for IPMT.
    Now works directly on IPMT rows rather than drafts.
    """
    from apps.gso_reports.utils import collect_ipmt_reports

    try:
        year, month_num = map(int, month_filter.split("-"))
    except ValueError:
        messages.error(request, "Invalid month format. Use YYYY-MM.")
        return redirect("gso_reports:preview_ipmt")

    reports = collect_ipmt_reports(year, month_num, unit_name)

    if request.method == "POST":
        # Assuming generate_ipmt_summary can accept multiple rows
        report_ids = [r["war_id"] for r in reports if r["war_id"]]
        generate_ipmt_summary.delay(report_ids)
        messages.success(request, f"AI summary generation started for IPMT {unit_name} {month_filter}.")
        return redirect("gso_reports:preview_ipmt")

    return render(request, "ai_service/generate_ipmt_summary.html", {
        "unit_name": unit_name,
        "month_filter": month_filter,
        "reports": reports,
    })
