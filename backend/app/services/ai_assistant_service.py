"""AI Assistant & Intelligent Triage Service."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import ReportCategory, PriorityLevel
from app.schemas.ai_assistant import (
    AITriageRequest,
    AITriageResponse,
    AIChatRequest,
    AIChatResponse,
    AITriageImageResponse
)
from app.repositories.report_repo import report_repo
from app.ai.vision import get_vision_analyzer

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

    async def triage_image(
        self, image_bytes: bytes, notes: Optional[str] = None
    ) -> AITriageImageResponse:
        """Triage an uploaded image using Gemini Vision."""
        analyzer = get_vision_analyzer()
        try:
            result = await analyzer.analyze_image(image_bytes, prompt_context=notes)
            # If the analyzer fell back to mock due to missing/invalid API key, return ai_available=False
            if result.raw_response and result.raw_response.get("mock"):
                return AITriageImageResponse(
                    ai_available=False,
                    suggested_category="OTHER",
                    confidence_score=0.0,
                    suggested_priority="LOW",
                    priority_score=0,
                    urgency_reasoning="",
                    detected_objects=[],
                    suggested_department_code="GCS",
                    recommended_action="",
                    sla_info="",
                    error_message="AI Vision analysis unavailable: The GEMINI_API_KEY in .env is invalid or expired. Please update it with a valid key from aistudio.google.com."
                )
        except Exception as e:
            return AITriageImageResponse(
                ai_available=False,
                suggested_category="OTHER",
                confidence_score=0.0,
                suggested_priority="LOW",
                priority_score=0,
                urgency_reasoning="",
                detected_objects=[],
                suggested_department_code="GCS",
                recommended_action="",
                sla_info="",
                error_message="AI Vision analysis unavailable. Please review the information manually."
            )

        # map category to standard ReportCategory
        mapped_cat = ReportCategory.OTHER
        result_cat_lower = result.category.lower()
        if "pothole" in result_cat_lower:
            mapped_cat = ReportCategory.POTHOLE
        elif "water" in result_cat_lower or "leak" in result_cat_lower:
            mapped_cat = ReportCategory.WATER_LEAK
        elif "streetlight" in result_cat_lower or "light" in result_cat_lower:
            mapped_cat = ReportCategory.STREETLIGHT
        elif "traffic signal" in result_cat_lower or "light" in result_cat_lower:
            mapped_cat = ReportCategory.TRAFFIC_SIGNAL
        elif "dumping" in result_cat_lower or "trash" in result_cat_lower:
            mapped_cat = ReportCategory.TRASH
        elif "tree" in result_cat_lower or "branch" in result_cat_lower or "park" in result_cat_lower:
            mapped_cat = ReportCategory.PARK_DAMAGE
        elif "graffiti" in result_cat_lower:
            mapped_cat = ReportCategory.GRAFFITI

        dept_map = {
            ReportCategory.POTHOLE: "DPW",
            ReportCategory.WATER_LEAK: "DWS",
            ReportCategory.STREETLIGHT: "DPW",
            ReportCategory.TRAFFIC_SIGNAL: "DPW",
            ReportCategory.TRASH: "DSW",
            ReportCategory.GRAFFITI: "DPR",
            ReportCategory.PARK_DAMAGE: "DPR",
            ReportCategory.OTHER: "DPW",
        }
        dept_code = dept_map.get(mapped_cat, "DPW")

        priority_score = int(result.severity_score * 10)
        if result.safety_hazard:
            priority_score = min(100, priority_score + 20)

        if priority_score >= 80:
            suggested_prio = PriorityLevel.URGENT
        elif priority_score >= 60:
            suggested_prio = PriorityLevel.HIGH
        elif priority_score >= 40:
            suggested_prio = PriorityLevel.MEDIUM
        else:
            suggested_prio = PriorityLevel.LOW

        sla_map = {
            PriorityLevel.URGENT: "2-4 hours",
            PriorityLevel.HIGH: "24 hours",
            PriorityLevel.MEDIUM: "3 days",
            PriorityLevel.LOW: "7-14 days",
        }
        sla_info = f"Expected response time: {sla_map.get(suggested_prio, 'Unknown')}"

        return AITriageImageResponse(
            ai_available=True,
            suggested_category=mapped_cat.value,
            confidence_score=result.confidence,
            suggested_priority=suggested_prio.value,
            priority_score=priority_score,
            urgency_reasoning=result.description,
            detected_objects=result.tags,
            suggested_department_code=dept_code,
            recommended_action=f"Route to {dept_code} immediately.",
            sla_info=sla_info,
            error_message=None,
        )


ai_assistant_service = AIAssistantService()
