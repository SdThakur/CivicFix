from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class RoadOwnershipResult:
    road_name: str
    road_classification: str
    owner_agency: str
    jurisdiction: str
    maintenance_zone: Optional[str]
    responsible_department: str
    confidence: str  # VERIFIED, ESTIMATED, UNKNOWN
    data_source: str
    notes: Optional[str] = None

@dataclass  
class GeocodingResult:
    address: str
    lat: float
    lng: float
    city: str
    state: str
    postal_code: str
    confidence: float  # 0-1

class RoadNetworkProvider(ABC):
    @abstractmethod
    async def get_road_ownership(self, lat: float, lng: float) -> RoadOwnershipResult: ...
    @abstractmethod
    async def get_nearby_roads(self, lat: float, lng: float, radius_m: float) -> list[dict]: ...

class GeocodingProvider(ABC):
    @abstractmethod
    async def reverse_geocode(self, lat: float, lng: float) -> GeocodingResult: ...
    @abstractmethod
    async def geocode_address(self, address: str) -> GeocodingResult: ...

class JurisdictionBoundaryProvider(ABC):
    @abstractmethod
    async def get_jurisdiction_at_point(self, lat: float, lng: float) -> dict: ...

class CriticalInfrastructureProvider(ABC):
    @abstractmethod
    async def get_critical_facilities_near(self, lat: float, lng: float, radius_m: float) -> list[dict]: ...
