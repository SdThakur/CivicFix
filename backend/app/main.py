"""CivicFix FastAPI Main Application entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
import app.models  # Load models for metadata registration
from app.api import (
    auth,
    reports,
    issues,
    work_orders,
    users,
    departments,
    analytics,
    notifications,
    search,
    ai_assistant,
    assets,
    service_requests,
    inspections,
    sla,
    crews,
    equipment,
    assignments,
    risk,
    preventive,
    gis,
    transparency,
    jurisdictions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database tables exist on application startup."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"[CivicFix Startup Warning] Could not auto-create tables: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api/v1
api_prefix = settings.API_V1_STR

# ─── Existing Core Routes ────────────────────────────────────────────────────
app.include_router(auth.router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)
app.include_router(issues.router, prefix=api_prefix)
app.include_router(work_orders.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(departments.router, prefix=api_prefix)
app.include_router(analytics.router, prefix=api_prefix)
app.include_router(notifications.router, prefix=api_prefix)
app.include_router(search.router, prefix=api_prefix)
app.include_router(ai_assistant.router, prefix=api_prefix)

# ─── Asset & Infrastructure Management ──────────────────────────────────────
app.include_router(assets.router, prefix=api_prefix)
app.include_router(jurisdictions.router, prefix=api_prefix)

# ─── 311 Service Request & Inspection Workflow ───────────────────────────────
app.include_router(service_requests.router, prefix=api_prefix)
app.include_router(inspections.router, prefix=api_prefix)

# ─── SLA & Escalation Engine ─────────────────────────────────────────────────
app.include_router(sla.router, prefix=api_prefix)

# ─── Crew, Equipment & Intelligent Assignment ─────────────────────────────────
app.include_router(crews.router, prefix=api_prefix)
app.include_router(equipment.router, prefix=api_prefix)
app.include_router(assignments.router, prefix=api_prefix)

# ─── GIS, Risk Scoring & Preventive Maintenance ───────────────────────────────
app.include_router(gis.router, prefix=api_prefix)
app.include_router(risk.router, prefix=api_prefix)
app.include_router(preventive.router, prefix=api_prefix)

# ─── Public Transparency ──────────────────────────────────────────────────────
app.include_router(transparency.router, prefix=api_prefix)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint for status inspection."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}
