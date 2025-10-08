from django.urls import path
from . import views

app_name = "ai_service"

urlpatterns = [
    # Work Accomplishment Report (WAR) AI Summaries
    path("summaries/", views.ai_summary_list, name="ai_summary_list"),
    path("summaries/<int:report_id>/", views.ai_summary_detail, name="ai_summary_detail"),
    path("summaries/<int:report_id>/generate/", views.generate_ai_summary, name="generate_ai_summary"),

    # IPMT AI Summaries
    path("ipmt/<int:ipmt_id>/generate/", views.generate_ipmt_ai_summary, name="generate_ipmt_ai_summary"),
]
