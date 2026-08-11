from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models.asset import Agency, Jurisdiction, MaintenanceZone, Road, RoadSegment, InfrastructureAsset
from app.schemas.asset import (
    AgencyCreate, JurisdictionCreate, MaintenanceZoneCreate, 
    RoadCreate, RoadUpdate, RoadSegmentCreate, 
    InfrastructureAssetCreate, InfrastructureAssetUpdate
)

class AssetRepository:
    async def get_agencies(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Agency]:
        result = await db.execute(select(Agency).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_agency_by_id(self, db: AsyncSession, id: int) -> Optional[Agency]:
        result = await db.execute(select(Agency).where(Agency.id == id))
        return result.scalar_one_or_none()

    async def create_agency(self, db: AsyncSession, data: AgencyCreate) -> Agency:
        obj = Agency(**data.model_dump())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def get_jurisdictions(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Jurisdiction]:
        result = await db.execute(select(Jurisdiction).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_jurisdiction_by_id(self, db: AsyncSession, id: int) -> Optional[Jurisdiction]:
        result = await db.execute(select(Jurisdiction).where(Jurisdiction.id == id))
        return result.scalar_one_or_none()

    async def create_jurisdiction(self, db: AsyncSession, data: JurisdictionCreate) -> Jurisdiction:
        obj = Jurisdiction(**data.model_dump())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def get_maintenance_zones(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[MaintenanceZone]:
        result = await db.execute(select(MaintenanceZone).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_maintenance_zone_by_id(self, db: AsyncSession, id: int) -> Optional[MaintenanceZone]:
        result = await db.execute(select(MaintenanceZone).where(MaintenanceZone.id == id))
        return result.scalar_one_or_none()

    async def create_maintenance_zone(self, db: AsyncSession, data: MaintenanceZoneCreate) -> MaintenanceZone:
        obj = MaintenanceZone(**data.model_dump())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def get_roads(self, db: AsyncSession, skip: int = 0, limit: int = 100, classification: Optional[str] = None) -> List[Road]:
        from sqlalchemy.orm import selectinload
        stmt = select(Road).options(selectinload(Road.agency), selectinload(Road.jurisdiction), selectinload(Road.maintenance_zone), selectinload(Road.segments))
        if classification:
            stmt = stmt.where(Road.classification == classification)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_road_by_id(self, db: AsyncSession, id: int) -> Optional[Road]:
        from sqlalchemy.orm import selectinload
        stmt = select(Road).options(selectinload(Road.agency), selectinload(Road.jurisdiction), selectinload(Road.maintenance_zone), selectinload(Road.segments)).where(Road.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_roads_near(self, db: AsyncSession, lat: float, lng: float, radius_km: float) -> List[Road]:
        # Using Haversine approximation to find road segments near the point, then fetching the roads
        from sqlalchemy.orm import selectinload
        haversine = (
            6371 * func.acos(
                func.cos(func.radians(lat)) * func.cos(func.radians(RoadSegment.start_lat)) *
                func.cos(func.radians(RoadSegment.start_lng) - func.radians(lng)) +
                func.sin(func.radians(lat)) * func.sin(func.radians(RoadSegment.start_lat))
            )
        )
        stmt = (
            select(Road)
            .join(RoadSegment)
            .where(haversine <= radius_km)
            .options(selectinload(Road.agency), selectinload(Road.jurisdiction), selectinload(Road.maintenance_zone), selectinload(Road.segments))
            .distinct()
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create_road(self, db: AsyncSession, data: RoadCreate) -> Road:
        obj = Road(**data.model_dump())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update_road(self, db: AsyncSession, road: Road, data: RoadUpdate) -> Road:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(road, key, value)
        await db.commit()
        await db.refresh(road)
        return road

    async def get_segments_by_road(self, db: AsyncSession, road_id: int) -> List[RoadSegment]:
        result = await db.execute(select(RoadSegment).where(RoadSegment.road_id == road_id))
        return list(result.scalars().all())

    async def create_segment(self, db: AsyncSession, data: RoadSegmentCreate) -> RoadSegment:
        obj = RoadSegment(**data.model_dump())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def get_assets(self, db: AsyncSession, skip: int = 0, limit: int = 100, asset_type: Optional[str] = None) -> List[InfrastructureAsset]:
        stmt = select(InfrastructureAsset)
        if asset_type:
            stmt = stmt.where(InfrastructureAsset.asset_type == asset_type)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_asset_by_id(self, db: AsyncSession, id: int) -> Optional[InfrastructureAsset]:
        result = await db.execute(select(InfrastructureAsset).where(InfrastructureAsset.id == id))
        return result.scalar_one_or_none()

    async def get_assets_near(self, db: AsyncSession, lat: float, lng: float, radius_km: float) -> List[InfrastructureAsset]:
        haversine = (
            6371 * func.acos(
                func.cos(func.radians(lat)) * func.cos(func.radians(InfrastructureAsset.latitude)) *
                func.cos(func.radians(InfrastructureAsset.longitude) - func.radians(lng)) +
                func.sin(func.radians(lat)) * func.sin(func.radians(InfrastructureAsset.latitude))
            )
        )
        stmt = select(InfrastructureAsset).where(haversine <= radius_km)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create_asset(self, db: AsyncSession, data: InfrastructureAssetCreate) -> InfrastructureAsset:
        obj = InfrastructureAsset(**data.model_dump())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update_asset(self, db: AsyncSession, asset: InfrastructureAsset, data: InfrastructureAssetUpdate) -> InfrastructureAsset:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(asset, key, value)
        await db.commit()
        await db.refresh(asset)
        return asset

    async def get_nearest_road_segment(self, db: AsyncSession, lat: float, lng: float) -> Optional[RoadSegment]:
        haversine = (
            6371 * func.acos(
                func.cos(func.radians(lat)) * func.cos(func.radians(RoadSegment.start_lat)) *
                func.cos(func.radians(RoadSegment.start_lng) - func.radians(lng)) +
                func.sin(func.radians(lat)) * func.sin(func.radians(RoadSegment.start_lat))
            )
        )
        stmt = select(RoadSegment).order_by(haversine).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

asset_repo = AssetRepository()
