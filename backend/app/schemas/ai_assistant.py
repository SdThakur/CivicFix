"""Pydantic v2 schemas for AI Triage & Assistant."""

from typing import List, Optional
from pydantic import BaseModel
from app.models.report import PriorityLevel, ReportCategory


class AITriageRequest(BaseModel):
    """Payload to triage a citizen report using AI."""

    title: str
    description: str
    latitude: float
    longitude: float


class AITriageResponse(BaseModel):
    """AI triage recommendation."""

    suggested_category: ReportCategory
    confidence_score: float
    suggested_priority: PriorityLevel
    urgency_reasoning: str
    detected_keywords: List[str]
    suggested_department_code: str
    recommended_action: str


class AIChatRequest(BaseModel):
    """Payload for citizen AI assistant query."""

    prompt: str
    context_report_id: Optional[int] = None


class AIChatResponse(BaseModel):
    """AI assistant conversational response."""

    reply: str
    suggested_actions: List[str]
    related_resources: List[str]


class AITriageImageResponse(BaseModel):
    """AI triage recommendation from an image."""
    ai_available: bool
    suggested_category: str
    confidence_score: float
    suggested_priority: str
    priority_score: int
    urgency_reasoning: str
    detected_objects: List[str]
    suggested_department_code: str
    recommended_action: str
    sla_info: str
    error_message: Optional[str]

