import enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Integer, Float, Boolean, JSON, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class RoadClassification(str, enum.Enum):
    INTERSTATE = "INTERSTATE"
    US_ROUTE = "US_ROUTE"
    STATE_ROUTE = "STATE_ROUTE"
    COUNTY_ROAD = "COUNTY_ROAD"
    MUNICIPAL_STREET = "MUNICIPAL_STREET"
    PRIVATE_ROAD = "PRIVATE_ROAD"
    UNKNOWN = "UNKNOWN"

class OwnershipConfidence(str, enum.Enum):
    VERIFIED = "VERIFIED"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"

class AssetType(str, enum.Enum):
    ROAD = "ROAD"
    TRAFFIC_SIGNAL = "TRAFFIC_SIGNAL"
    STREETLIGHT = "STREETLIGHT"
    SIGN = "SIGN"
    SIDEWALK = "SIDEWALK"
    DRAINAGE = "DRAINAGE"
    GUARDRAIL = "GUARDRAIL"
    CROSSWALK = "CROSSWALK"
    BRIDGE = "BRIDGE"
    BUS_STOP = "BUS_STOP"
    OTHER = "OTHER"

class AssetCondition(str, enum.Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    CRITICAL = "CRITICAL"

class AssetStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    UNDER_REPAIR = "UNDER_REPAIR"
    DECOMMISSIONED = "DECOMMISSIONED"

class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    agency_code: Mapped[str] = mapped_column(String(50), unique=True)
    agency_type: Mapped[str] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    jurisdiction_level: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    jurisdiction_code: Mapped[str] = mapped_column(String(50), unique=True)
    jurisdiction_type: Mapped[str] = mapped_column(String(50))
    agency_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agencies.id", ondelete="SET NULL"))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("jurisdictions.id", ondelete="SET NULL"))
    latitude_center: Mapped[Optional[float]] = mapped_column(Float)
    longitude_center: Mapped[Optional[float]] = mapped_column(Float)
    boundary_geojson: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    agency: Mapped[Optional["Agency"]] = relationship("Agency")
    parent: Mapped[Optional["Jurisdiction"]] = relationship("Jurisdiction", remote_side=[id], back_populates="children")
    children: Mapped[List["Jurisdiction"]] = relationship("Jurisdiction", back_populates="parent")
    roads: Mapped[List["Road"]] = relationship("Road", back_populates="jurisdiction")

class MaintenanceZone(Base):
    __tablename__ = "maintenance_zones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    zone_code: Mapped[str] = mapped_column(String(50), unique=True)
    jurisdiction_id: Mapped[Optional[int]] = mapped_column(ForeignKey("jurisdictions.id", ondelete="SET NULL"))
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"))
    supervisor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    latitude_center: Mapped[Optional[float]] = mapped_column(Float)
    longitude_center: Mapped[Optional[float]] = mapped_column(Float)
    boundary_geojson: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    jurisdiction: Mapped[Optional["Jurisdiction"]] = relationship("Jurisdiction")
    roads: Mapped[List["Road"]] = relationship("Road", back_populates="maintenance_zone")
    assets: Mapped[List["InfrastructureAsset"]] = relationship("InfrastructureAsset", back_populates="maintenance_zone")

class Road(Base):
    __tablename__ = "roads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    road_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(500))
    classification: Mapped[RoadClassification] = mapped_column(SQLEnum(RoadClassification, native_enum=False))
    ownership_confidence: Mapped[OwnershipConfidence] = mapped_column(SQLEnum(OwnershipConfidence, native_enum=False), default=OwnershipConfidence.ESTIMATED)
    
    agency_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agencies.id", ondelete="SET NULL"))
    jurisdiction_id: Mapped[Optional[int]] = mapped_column(ForeignKey("jurisdictions.id", ondelete="SET NULL"))
    maintenance_zone_id: Mapped[Optional[int]] = mapped_column(ForeignKey("maintenance_zones.id", ondelete="SET NULL"))
    
    speed_limit: Mapped[Optional[int]] = mapped_column(Integer)
    lane_count: Mapped[int] = mapped_column(Integer, default=2)
    surface_type: Mapped[Optional[str]] = mapped_column(String(100))
    is_divided: Mapped[bool] = mapped_column(Boolean, default=False)
    has_bike_lane: Mapped[bool] = mapped_column(Boolean, default=False)
    has_sidewalk: Mapped[bool] = mapped_column(Boolean, default=False)
    condition_index: Mapped[float] = mapped_column(Float, default=75.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    agency: Mapped[Optional["Agency"]] = relationship("Agency")
    jurisdiction: Mapped[Optional["Jurisdiction"]] = relationship("Jurisdiction", back_populates="roads")
    maintenance_zone: Mapped[Optional["MaintenanceZone"]] = relationship("MaintenanceZone", back_populates="roads")
    segments: Mapped[List["RoadSegment"]] = relationship("RoadSegment", back_populates="road")
    assets: Mapped[List["InfrastructureAsset"]] = relationship("InfrastructureAsset", back_populates="road")
    
    @property
    def agency_name(self) -> Optional[str]:
        return self.agency.name if self.agency else None

    @property
    def jurisdiction_name(self) -> Optional[str]:
        return self.jurisdiction.name if self.jurisdiction else None

    @property
    def maintenance_zone_name(self) -> Optional[str]:
        return self.maintenance_zone.name if self.maintenance_zone else None

    @property
    def segment_count(self) -> int:
        return len(self.segments) if self.segments is not None else 0

class RoadSegment(Base):
    __tablename__ = "road_segments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    segment_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    road_id: Mapped[int] = mapped_column(ForeignKey("roads.id", ondelete="CASCADE"), index=True)
    
    start_address: Mapped[Optional[str]] = mapped_column(String(255))
    end_address: Mapped[Optional[str]] = mapped_column(String(255))
    start_lat: Mapped[Optional[float]] = mapped_column(Float)
    start_lng: Mapped[Optional[float]] = mapped_column(Float)
    end_lat: Mapped[Optional[float]] = mapped_column(Float)
    end_lng: Mapped[Optional[float]] = mapped_column(Float)
    length_meters: Mapped[Optional[float]] = mapped_column(Float)
    condition_index: Mapped[float] = mapped_column(Float, default=75.0)
    
    last_inspected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_maintained_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    incident_count_90d: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    segment_geojson: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    road: Mapped["Road"] = relationship("Road", back_populates="segments")

class InfrastructureAsset(Base):
    __tablename__ = "infrastructure_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    asset_type: Mapped[AssetType] = mapped_column(SQLEnum(AssetType, native_enum=False))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    road_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roads.id", ondelete="SET NULL"))
    maintenance_zone_id: Mapped[Optional[int]] = mapped_column(ForeignKey("maintenance_zones.id", ondelete="SET NULL"))
    jurisdiction_id: Mapped[Optional[int]] = mapped_column(ForeignKey("jurisdictions.id", ondelete="SET NULL"))
    agency_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agencies.id", ondelete="SET NULL"))
    
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    address: Mapped[Optional[str]] = mapped_column(String(255))
    
    condition: Mapped[AssetCondition] = mapped_column(SQLEnum(AssetCondition, native_enum=False), default=AssetCondition.GOOD)
    status: Mapped[AssetStatus] = mapped_column(SQLEnum(AssetStatus, native_enum=False), default=AssetStatus.ACTIVE)
    condition_score: Mapped[float] = mapped_column(Float, default=75.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    installation_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_inspected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_maintained_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    maintenance_history: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255))
    model_number: Mapped[Optional[str]] = mapped_column(String(255))
    warranty_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    road: Mapped[Optional["Road"]] = relationship("Road", back_populates="assets")
    maintenance_zone: Mapped[Optional["MaintenanceZone"]] = relationship("MaintenanceZone", back_populates="assets")
    jurisdiction: Mapped[Optional["Jurisdiction"]] = relationship("Jurisdiction")
    agency: Mapped[Optional["Agency"]] = relationship("Agency")
