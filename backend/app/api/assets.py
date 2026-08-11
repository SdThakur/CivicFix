from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import UserRole
from app.schemas.asset import (
    AgencyRead, AgencyCreate,
    JurisdictionRead, JurisdictionCreate,
    MaintenanceZoneRead, MaintenanceZoneCreate,
    RoadRead, RoadCreate, RoadUpdate,
    RoadSegmentRead, RoadSegmentCreate,
    InfrastructureAssetRead, InfrastructureAssetCreate, InfrastructureAssetUpdate
)
from app.repositories.asset_repo import asset_repo
from app.models.asset import RoadClassification, AssetType

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("/agencies", response_model=List[AgencyRead])
async def get_agencies(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await asset_repo.get_agencies(db, skip=skip, limit=limit)

@router.get("/agencies/{id}", response_model=AgencyRead)
async def get_agency(id: int, db: AsyncSession = Depends(get_db)):
    agency = await asset_repo.get_agency_by_id(db, id)
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency

@router.post("/agencies", response_model=AgencyRead)
async def create_agency(data: AgencyCreate, db: AsyncSession = Depends(get_db), current_user = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))):
    return await asset_repo.create_agency(db, data)

@router.get("/jurisdictions", response_model=List[JurisdictionRead])
async def get_jurisdictions(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await asset_repo.get_jurisdictions(db, skip=skip, limit=limit)

@router.get("/jurisdictions/{id}", response_model=JurisdictionRead)
async def get_jurisdiction(id: int, db: AsyncSession = Depends(get_db)):
    jurisdiction = await asset_repo.get_jurisdiction_by_id(db, id)
    if not jurisdiction:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")
    return jurisdiction

@router.post("/jurisdictions", response_model=JurisdictionRead)
async def create_jurisdiction(data: JurisdictionCreate, db: AsyncSession = Depends(get_db), current_user = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))):
    return await asset_repo.create_jurisdiction(db, data)

@router.get("/maintenance-zones", response_model=List[MaintenanceZoneRead])
async def get_maintenance_zones(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await asset_repo.get_maintenance_zones(db, skip=skip, limit=limit)

@router.post("/maintenance-zones", response_model=MaintenanceZoneRead)
async def create_maintenance_zone(data: MaintenanceZoneCreate, db: AsyncSession = Depends(get_db), current_user = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))):
    return await asset_repo.create_maintenance_zone(db, data)

@router.get("/roads", response_model=List[RoadRead])
async def get_roads(
    skip: int = 0, 
    limit: int = 100, 
    classification: Optional[RoadClassification] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    if lat is not None and lng is not None and radius_km is not None:
        return await asset_repo.get_roads_near(db, lat, lng, radius_km)
    return await asset_repo.get_roads(db, skip=skip, limit=limit, classification=classification)

@router.get("/roads/{id}", response_model=RoadRead)
async def get_road(id: int, db: AsyncSession = Depends(get_db)):
    road = await asset_repo.get_road_by_id(db, id)
    if not road:
        raise HTTPException(status_code=404, detail="Road not found")
    return road

@router.post("/roads", response_model=RoadRead)
async def create_road(data: RoadCreate, db: AsyncSession = Depends(get_db), current_user = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))):
    return await asset_repo.create_road(db, data)

@router.patch("/roads/{id}", response_model=RoadRead)
async def update_road(id: int, data: RoadUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))):
    road = await asset_repo.get_road_by_id(db, id)
    if not road:
        raise HTTPException(status_code=404, detail="Road not found")
    return await asset_repo.update_road(db, road, data)

@router.get("/roads/{road_id}/segments", response_model=List[RoadSegmentRead])
async def get_segments_by_road(road_id: int, db: AsyncSession = Depends(get_db)):
    return await asset_repo.get_segments_by_road(db, road_id)

@router.post("/roads/{road_id}/segments", response_model=RoadSegmentRead)
async def create_segment(road_id: int, data: RoadSegmentCreate, db: AsyncSession = Depends(get_db), current_user = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))):
    if data.road_id != road_id:
        data.road_id = road_id
    return await asset_repo.create_segment(db, data)

@router.get("/infrastructure", response_model=List[InfrastructureAssetRead])
async def get_infrastructure(
    skip: int = 0, 
    limit: int = 100, 
    asset_type: Optional[AssetType] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    if lat is not None and lng is not None and radius_km is not None:
        return await asset_repo.get_assets_near(db, lat, lng, radius_km)
    return await asset_repo.get_assets(db, skip=skip, limit=limit, asset_type=asset_type)

@router.get("/infrastructure/{id}", response_model=InfrastructureAssetRead)
async def get_infrastructure_by_id(id: int, db: AsyncSession = Depends(get_db)):
    asset = await asset_repo.get_asset_by_id(db, id)
    if not asset:
        raise HTTPException(status_code=404, detail="Infrastructure asset not found")
    return asset

@router.post("/infrastructure", response_model=InfrastructureAssetRead)
async def create_infrastructure(data: InfrastructureAssetCreate, db: AsyncSession = Depends(get_db), current_user = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))):
    return await asset_repo.create_asset(db, data)

@router.patch("/infrastructure/{id}", response_model=InfrastructureAssetRead)
async def update_infrastructure(id: int, data: InfrastructureAssetUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))):
    asset = await asset_repo.get_asset_by_id(db, id)
    if not asset:
        raise HTTPException(status_code=404, detail="Infrastructure asset not found")
    return await asset_repo.update_asset(db, asset, data)
