from django.db import models
from django.conf import settings
from apps.gso_reports.models import WorkAccomplishmentReport


class AIReportSummary(models.Model):
    """
    Stores AI-generated summaries for a Work Accomplishment Report (WAR).
    Multiple summaries may exist per report (e.g., drafts, retries).
    """

    report = models.ForeignKey(
        WorkAccomplishmentReport,
        on_delete=models.CASCADE,
        related_name="ai_summaries"
    )
    summary_text = models.TextField()
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AI Summary for WAR #{self.report.id} (by {self.generated_by or 'System'})"
