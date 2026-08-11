from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.asset import RoadClassification, OwnershipConfidence, AssetType, AssetCondition, AssetStatus

class AgencyBase(BaseModel):
    name: str
    agency_code: str
    agency_type: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    jurisdiction_level: str

class AgencyCreate(AgencyBase):
    pass

class AgencyUpdate(AgencyBase):
    name: Optional[str] = None
    agency_code: Optional[str] = None
    agency_type: Optional[str] = None
    jurisdiction_level: Optional[str] = None

class AgencyRead(AgencyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class JurisdictionBase(BaseModel):
    name: str
    jurisdiction_code: str
    jurisdiction_type: str
    agency_id: Optional[int] = None
    parent_id: Optional[int] = None
    latitude_center: Optional[float] = None
    longitude_center: Optional[float] = None
    boundary_geojson: Optional[Dict[str, Any]] = None

class JurisdictionCreate(JurisdictionBase):
    pass

class JurisdictionUpdate(JurisdictionBase):
    name: Optional[str] = None
    jurisdiction_code: Optional[str] = None
    jurisdiction_type: Optional[str] = None

class JurisdictionRead(JurisdictionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MaintenanceZoneBase(BaseModel):
    name: str
    zone_code: str
    jurisdiction_id: Optional[int] = None
    department_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    latitude_center: Optional[float] = None
    longitude_center: Optional[float] = None
    boundary_geojson: Optional[Dict[str, Any]] = None
    is_active: bool = True

class MaintenanceZoneCreate(MaintenanceZoneBase):
    pass

class MaintenanceZoneUpdate(MaintenanceZoneBase):
    name: Optional[str] = None
    zone_code: Optional[str] = None

class MaintenanceZoneRead(MaintenanceZoneBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RoadSegmentBase(BaseModel):
    segment_code: str
    start_address: Optional[str] = None
    end_address: Optional[str] = None
    start_lat: Optional[float] = None
    start_lng: Optional[float] = None
    end_lat: Optional[float] = None
    end_lng: Optional[float] = None
    length_meters: Optional[float] = None
    condition_index: float = 75.0
    last_inspected_at: Optional[datetime] = None
    last_maintained_at: Optional[datetime] = None
    incident_count_90d: int = 0
    risk_score: float = 0.0
    segment_geojson: Optional[Dict[str, Any]] = None

class RoadSegmentCreate(RoadSegmentBase):
    road_id: int

class RoadSegmentUpdate(RoadSegmentBase):
    segment_code: Optional[str] = None

class RoadSegmentRead(RoadSegmentBase):
    id: int
    road_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RoadBase(BaseModel):
    road_code: str
    name: str
    full_name: Optional[str] = None
    classification: RoadClassification
    ownership_confidence: OwnershipConfidence = OwnershipConfidence.ESTIMATED
    agency_id: Optional[int] = None
    jurisdiction_id: Optional[int] = None
    maintenance_zone_id: Optional[int] = None
    speed_limit: Optional[int] = None
    lane_count: int = 2
    surface_type: Optional[str] = None
    is_divided: bool = False
    has_bike_lane: bool = False
    has_sidewalk: bool = False
    condition_index: float = 75.0
    risk_score: float = 0.0

class RoadCreate(RoadBase):
    pass

class RoadUpdate(RoadBase):
    road_code: Optional[str] = None
    name: Optional[str] = None
    classification: Optional[RoadClassification] = None

class RoadRead(RoadBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    agency_name: Optional[str] = None
    jurisdiction_name: Optional[str] = None
    maintenance_zone_name: Optional[str] = None
    segment_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class InfrastructureAssetBase(BaseModel):
    asset_id_code: str
    asset_type: AssetType
    name: Optional[str] = None
    description: Optional[str] = None
    road_id: Optional[int] = None
    maintenance_zone_id: Optional[int] = None
    jurisdiction_id: Optional[int] = None
    agency_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    condition: AssetCondition = AssetCondition.GOOD
    status: AssetStatus = AssetStatus.ACTIVE
    condition_score: float = 75.0
    risk_score: float = 0.0
    installation_date: Optional[datetime] = None
    last_inspected_at: Optional[datetime] = None
    last_maintained_at: Optional[datetime] = None
    maintenance_history: Optional[List[Dict[str, Any]]] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    warranty_expires_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None

class InfrastructureAssetCreate(InfrastructureAssetBase):
    pass

class InfrastructureAssetUpdate(InfrastructureAssetBase):
    asset_id_code: Optional[str] = None
    asset_type: Optional[AssetType] = None

class InfrastructureAssetRead(InfrastructureAssetBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
