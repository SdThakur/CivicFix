"""AI Assistant & Intelligent Triage Service."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import ReportCategory, PriorityLevel
from app.schemas.ai_assistant import (
    AITriageRequest,
    AITriageResponse,
    AIChatRequest,
    AIChatResponse,
)
from app.repositories.report_repo import report_repo

# Keyword matching table for smart classification fallback / local NLP heuristic
KEYWORD_CATEGORY_MAP = {
    "pothole": (ReportCategory.POTHOLE, "DPW", PriorityLevel.MEDIUM),
    "hole": (ReportCategory.POTHOLE, "DPW", PriorityLevel.LOW),
    "asphalt": (ReportCategory.POTHOLE, "DPW", PriorityLevel.MEDIUM),
    "signal": (ReportCategory.TRAFFIC_SIGNAL, "DPW", PriorityLevel.HIGH),
    "traffic light": (ReportCategory.TRAFFIC_SIGNAL, "DPW", PriorityLevel.HIGH),
    "intersection": (ReportCategory.TRAFFIC_SIGNAL, "DPW", PriorityLevel.HIGH),
    "light": (ReportCategory.STREETLIGHT, "DPW", PriorityLevel.LOW),
    "lamp": (ReportCategory.STREETLIGHT, "DPW", PriorityLevel.LOW),
    "dark": (ReportCategory.STREETLIGHT, "DPW", PriorityLevel.MEDIUM),
    "water": (ReportCategory.WATER_LEAK, "DWS", PriorityLevel.HIGH),
    "pipe": (ReportCategory.WATER_LEAK, "DWS", PriorityLevel.HIGH),
    "leak": (ReportCategory.WATER_LEAK, "DWS", PriorityLevel.HIGH),
    "burst": (ReportCategory.WATER_LEAK, "DWS", PriorityLevel.URGENT),
    "graffiti": (ReportCategory.GRAFFITI, "DPR", PriorityLevel.LOW),
    "spray": (ReportCategory.GRAFFITI, "DPR", PriorityLevel.LOW),
    "paint": (ReportCategory.GRAFFITI, "DPR", PriorityLevel.LOW),
    "trash": (ReportCategory.TRASH, "DSW", PriorityLevel.MEDIUM),
    "garbage": (ReportCategory.TRASH, "DSW", PriorityLevel.MEDIUM),
    "litter": (ReportCategory.TRASH, "DSW", PriorityLevel.LOW),
    "dumping": (ReportCategory.TRASH, "DSW", PriorityLevel.HIGH),
    "park": (ReportCategory.PARK_DAMAGE, "DPR", PriorityLevel.LOW),
    "bench": (ReportCategory.PARK_DAMAGE, "DPR", PriorityLevel.LOW),
    "playground": (ReportCategory.PARK_DAMAGE, "DPR", PriorityLevel.MEDIUM),
    "tree": (ReportCategory.PARK_DAMAGE, "DPR", PriorityLevel.MEDIUM),
}


class AIAssistantService:
    """Business logic for AI triage and civic assistant chat."""

    async def triage(
        self, db: AsyncSession, request: AITriageRequest
    ) -> AITriageResponse:
        """Perform automated AI classification and urgency evaluation on a report."""
        text = f"{request.title} {request.description}".lower()
        detected_keywords = []

        selected_cat = ReportCategory.OTHER
        selected_dept = "GCS"
        selected_priority = PriorityLevel.MEDIUM
        confidence = 0.65

        for kw, (cat, dept, prio) in KEYWORD_CATEGORY_MAP.items():
            if kw in text:
                detected_keywords.append(kw)
                selected_cat = cat
                selected_dept = dept
                selected_priority = prio
                confidence = 0.92
                break

        # Danger / Urgency keyword boost
        urgent_terms = ["hazard", "danger", "burst", "collapse", "blocking", "injury"]
        if any(term in text for term in urgent_terms):
            selected_priority = PriorityLevel.URGENT
            confidence = min(0.98, confidence + 0.05)
            reasoning = "High urgency triggered due to safety hazard terms detected in submission."
        else:
            reasoning = f"Categorized as {selected_cat.value} based on text features."

        return AITriageResponse(
            suggested_category=selected_cat,
            confidence_score=round(confidence, 2),
            suggested_priority=selected_priority,
            urgency_reasoning=reasoning,
            detected_keywords=detected_keywords,
            suggested_department_code=selected_dept,
            recommended_action=f"Route ticket immediately to {selected_dept} for inspection.",
        )

    async def chat(
        self, db: AsyncSession, request: AIChatRequest
    ) -> AIChatResponse:
        """Process conversational query from citizen regarding civic services."""
        prompt_lower = request.prompt.lower()

        context_info = ""
        if request.context_report_id:
            report = await report_repo.get_by_id(db, request.context_report_id)
            if report:
                context_info = f" (regarding report #{report.tracking_number} - {report.title})"

        if "how long" in prompt_lower or "time" in prompt_lower or "status" in prompt_lower:
            reply = f"Potholes and streetlight issues are typically reviewed within 24-48 hours. Field work orders are dispatched based on priority levels{context_info}."
            actions = [
                "Track existing report status",
                "View average neighborhood resolution times",
            ]
            resources = [
                "/api/v1/reports",
                "/api/v1/analytics/resolution-times",
            ]
        elif "emergency" in prompt_lower or "danger" in prompt_lower:
            reply = "If there is an immediate threat to life or property (such as live power lines or major main breaks), please dial emergency services immediately!"
            actions = [
                "Call 911 for life safety emergency",
                "Contact 311 City Hotline",
            ]
            resources = ["https://cityservices.gov/emergency"]
        else:
            reply = f"Thank you for contacting CivicFix AI Assistant{context_info}. You can report infrastructure damage, view active public issues, or track repair status directly from your dashboard."
            actions = ["Submit new report", "Search nearby issues"]
            resources = ["/api/v1/reports", "/api/v1/search"]

        return AIChatResponse(
            reply=reply,
            suggested_actions=actions,
            related_resources=resources,
        )


ai_assistant_service = AIAssistantService()
