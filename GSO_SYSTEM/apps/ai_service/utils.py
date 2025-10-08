# apps/ai_service/utils.py
import os
import requests
from apps.gso_requests.models import ServiceRequest, TaskReport  # ✅ Import models for richer prompts

# -------------------------------
# Local AI Model Config
# -------------------------------
AI_API_URL = os.getenv("AI_API_URL", "http://127.0.0.1:8001/v1/generate")
AI_API_KEY = os.getenv("AI_API_KEY", "mysecretkey")

# -------------------------------
# Query Local Private Model
# -------------------------------
def query_local_ai(prompt: str) -> str:
    """
    Send a prompt to the local private AI server (Flan-T5 model)
    and return the generated text.
    """
    try:
        response = requests.post(
            AI_API_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": AI_API_KEY,
            },
            json={"prompt": prompt},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("result", "").strip()
    except Exception as e:
        return f"[AI Error] {e}"

# -------------------------------
# Enhanced WAR Description Generator
# -------------------------------
def generate_war_description(request_obj: ServiceRequest) -> str:
    """
    Generate a professional, two-sentence Work Accomplishment Report (WAR) description
    using the local AI model. The first sentence summarizes the task done concisely,
    and the second adds brief supporting detail if available.
    """
    try:
        # --- Gather base info ---
        activity_name = getattr(request_obj, "activity_name", "Service Request")
        unit = request_obj.unit.name if request_obj.unit else "General Services"
        requestor_description = (
            request_obj.description.strip() if request_obj.description else "No description provided."
        )

        # --- Gather personnel info ---
        personnel_names = [p.get_full_name() or p.username for p in request_obj.assigned_personnel.all()]
        personnel_str = ", ".join(personnel_names) if personnel_names else "N/A"

        # --- Gather task reports ---
        task_reports = TaskReport.objects.filter(request=request_obj)
        report_texts = [r.report_text.strip() for r in task_reports if r.report_text.strip()]
        reports_str = "\n".join([f"- {txt}" for txt in report_texts]) or "No personnel reports available."

        # --- Build detailed prompt ---
        prompt = (
                    "You are an AI that generates short, professional government work logs.\n\n"
                    f"Requestor description:\n{requestor_description}\n\n"
                    f"Personnel task reports:\n{reports_str}\n\n"
                    "Write ONE concise sentence that summarizes the accomplishment clearly and factually. "
                    "Do not include names or personnel, focus only on the task performed. "
                    "Keep it formal, brief, and specific."
                )

        # --- Query AI model ---
        return query_local_ai(prompt)

    except Exception as e:
        return f"[AI Error] Failed to generate WAR: {e}"

# -------------------------------
# IPMT Summary Generator
# -------------------------------
def generate_ipmt_summary(success_indicator: str, war_descriptions: list) -> str:
    """
    Generate a summary statement for a given Success Indicator
    based on multiple WARs, using the local AI model.
    """
    if not war_descriptions:
        return f"No accomplishments recorded for indicator: {success_indicator}."

    activities_text = "\n".join([f"- {desc}" for desc in war_descriptions])
    prompt = (
        f"Summarize the following accomplishments for the success indicator '{success_indicator}':\n\n"
        f"{activities_text}\n\n"
        "Write in a concise, factual way about what was achieved."
    )

    return query_local_ai(prompt)
