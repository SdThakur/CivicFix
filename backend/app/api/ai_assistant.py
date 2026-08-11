"""AI Assistant API Router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.ai_assistant import (
    AITriageRequest,
    AITriageResponse,
    AIChatRequest,
    AIChatResponse,
)
from app.services.ai_assistant_service import ai_assistant_service

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


@router.post("/triage", response_model=AITriageResponse)
async def triage_report(
    request: AITriageRequest,
    db: AsyncSession = Depends(get_db),
) -> AITriageResponse:
    """Analyze report details to determine category, priority, and department routing recommendation."""
    return await ai_assistant_service.triage(db=db, request=request)


@router.post("/chat", response_model=AIChatResponse)
async def chat_assistant(
    request: AIChatRequest,
    db: AsyncSession = Depends(get_db),
) -> AIChatResponse:
    """Interact with CivicFix citizen AI assistant for guidance and status support."""
    return await ai_assistant_service.chat(db=db, request=request)
