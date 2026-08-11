from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.api.deps import get_db
from app.services.jurisdiction_service import jurisdiction_service

router = APIRouter(prefix="/jurisdictions", tags=["Jurisdictions"])

@router.get("/resolve", response_model=dict)
async def resolve_ownership(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    db: AsyncSession = Depends(get_db)
):
    """Resolve ownership chain for a location."""
    return await jurisdiction_service.resolve_ownership(db=db, lat=lat, lng=lng)

@router.get("/geocode", response_model=dict)
async def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude")
):
    """Reverse geocode a location to address."""
    return await jurisdiction_service.reverse_geocode(lat=lat, lng=lng)

@router.get("/")
async def list_jurisdictions(db: AsyncSession = Depends(get_db)):
    """List all jurisdictions."""
    return []
