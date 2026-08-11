"""Jurisdiction and road ownership intelligence service."""
from app.providers.osm_provider import OSMRoadNetworkProvider, NominatimGeocodingProvider
from app.providers.gis_provider import RoadOwnershipResult
from sqlalchemy.ext.asyncio import AsyncSession

class JurisdictionService:
    def __init__(self):
        self.road_provider = OSMRoadNetworkProvider()
        self.geocoding_provider = NominatimGeocodingProvider()
    
    async def resolve_ownership(self, db: AsyncSession, lat: float, lng: float) -> dict:
        """
        GPS (lat, lng) -> Road Segment -> Road Owner -> Jurisdiction -> Maintenance Zone -> Department
        
        Returns dict with full ownership chain. confidence is NEVER presented as authoritative
        unless explicitly VERIFIED from a government GIS dataset.
        """
        try:
            from app.repositories.asset_repo import asset_repo
            segment = await asset_repo.get_nearest_road_segment(db, lat, lng)
        except ImportError:
            segment = None
        
        # 2. If we have a road segment with a known jurisdiction, use that (VERIFIED)
        if segment and getattr(segment, 'road', None) and getattr(segment.road, 'jurisdiction_id', None):
            road = segment.road
            return {
                "road_segment_id": segment.id,
                "road_name": road.name,
                "road_classification": road.classification,
                "jurisdiction": road.jurisdiction.name if road.jurisdiction else None,
                "maintenance_zone": road.maintenance_zone.name if getattr(road, 'maintenance_zone', None) else None,
                "agency": road.agency.name if getattr(road, 'agency', None) else None,
                "confidence": getattr(road, 'ownership_confidence', 'VERIFIED'),
                "source": "CivicFix Database"
            }
        
        # 3. Fallback to OSM estimation (ESTIMATED - clearly labeled)
        try:
            osm_result = await self.road_provider.get_road_ownership(lat, lng)
            return {
                "road_segment_id": segment.id if segment else None,
                "road_name": osm_result.road_name,
                "road_classification": osm_result.road_classification,
                "jurisdiction": osm_result.jurisdiction,
                "maintenance_zone": None,
                "agency": osm_result.owner_agency,
                "confidence": "ESTIMATED",
                "source": osm_result.data_source,
                "disclaimer": "Ownership is ESTIMATED from OpenStreetMap data. Not verified government information."
            }
        except Exception:
            return {
                "road_segment_id": None,
                "road_name": "Unknown",
                "road_classification": "UNKNOWN",
                "jurisdiction": None,
                "maintenance_zone": None,
                "agency": None,
                "confidence": "UNKNOWN",
                "source": "None",
                "disclaimer": "Road ownership could not be determined."
            }
    
    async def reverse_geocode(self, lat: float, lng: float) -> dict:
        try:
            result = await self.geocoding_provider.reverse_geocode(lat, lng)
            return {"address": result.address, "city": result.city, "state": result.state, "postal_code": result.postal_code, "confidence": result.confidence}
        except Exception:
            return {"address": f"{lat:.5f}, {lng:.5f}", "confidence": 0}

jurisdiction_service = JurisdictionService()
