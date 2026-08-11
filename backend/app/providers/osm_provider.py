import httpx
from app.providers.gis_provider import RoadNetworkProvider, GeocodingProvider, JurisdictionBoundaryProvider, RoadOwnershipResult, GeocodingResult

class OSMRoadNetworkProvider(RoadNetworkProvider):
    """OpenStreetMap Nominatim-based road network provider.
    NOTE: Uses estimated ownership based on road classification.
    This is ESTIMATED data, not verified government GIS data."""
    
    BASE_URL = "https://nominatim.openstreetmap.org"
    HEADERS = {"User-Agent": "CivicFix/1.0 civic-infrastructure-management"}
    
    async def get_road_ownership(self, lat: float, lng: float) -> RoadOwnershipResult:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/reverse", params={"lat": lat, "lon": lng, "format": "json", "zoom": 16}, headers=self.HEADERS, timeout=10)
            data = resp.json()
        # Parse OSM highway tag to estimate classification
        highway = data.get("extratags", {}).get("highway", "unknown")
        # Map highway type to classification
        classification_map = {"motorway": "INTERSTATE", "trunk": "US_ROUTE", "primary": "STATE_ROUTE", "secondary": "COUNTY_ROAD", "residential": "MUNICIPAL_STREET", "service": "PRIVATE_ROAD"}
        classification = classification_map.get(highway, "UNKNOWN")
        return RoadOwnershipResult(
            road_name=data.get("display_name", "Unknown Road").split(",")[0],
            road_classification=classification,
            owner_agency="Unknown (Estimated from OSM)",
            jurisdiction=data.get("address", {}).get("city", data.get("address", {}).get("county", "Unknown")),
            maintenance_zone=None,
            responsible_department="Public Works (Estimated)",
            confidence="ESTIMATED",
            data_source="OpenStreetMap Nominatim",
            notes="This is estimated data from OpenStreetMap. Not verified government GIS data."
        )
    
    async def get_nearby_roads(self, lat: float, lng: float, radius_m: float) -> list[dict]:
        return []  # Overpass API integration point

class NominatimGeocodingProvider(GeocodingProvider):
    BASE_URL = "https://nominatim.openstreetmap.org"
    HEADERS = {"User-Agent": "CivicFix/1.0 civic-infrastructure-management"}
    
    async def reverse_geocode(self, lat: float, lng: float) -> GeocodingResult:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/reverse", params={"lat": lat, "lon": lng, "format": "json"}, headers=self.HEADERS, timeout=10)
            data = resp.json()
        addr = data.get("address", {})
        return GeocodingResult(
            address=data.get("display_name", ""),
            lat=lat, lng=lng,
            city=addr.get("city", addr.get("town", "")),
            state=addr.get("state", ""),
            postal_code=addr.get("postcode", ""),
            confidence=0.85
        )
    
    async def geocode_address(self, address: str) -> GeocodingResult:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/search", params={"q": address, "format": "json", "limit": 1}, headers=self.HEADERS, timeout=10)
            results = resp.json()
        if not results:
            raise ValueError(f"Address not found: {address}")
        r = results[0]
        return GeocodingResult(address=r.get("display_name", ""), lat=float(r["lat"]), lng=float(r["lon"]), city="", state="", postal_code="", confidence=float(r.get("importance", 0.5)))
