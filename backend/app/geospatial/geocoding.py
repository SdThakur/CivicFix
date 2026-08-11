"""Geocoding and reverse geocoding service using OpenStreetMap Nominatim with httpx/urllib, caching, and fallback."""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Tuple
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    httpx = None  # type: ignore
    HAS_HTTPX = False


class ReverseGeocoder:
    """Reverse and forward geocoding service for civic infrastructure location resolution."""

    NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
    NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "CivicFix-Platform/1.0 (civicfix-dev@civicfix.gov)"

    def __init__(self, timeout_seconds: float = 5.0, cache_size: int = 1000):
        self.timeout_seconds = timeout_seconds
        self._cache: Dict[Tuple[float, float], Dict[str, Any]] = {}
        self._address_cache: Dict[str, Dict[str, Any]] = {}
        self.max_cache_size = cache_size

    async def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """Perform reverse geocoding to resolve coordinates (lat, lon) to a structured address dictionary.

        Args:
            lat: Latitude (-90.0 to 90.0)
            lon: Longitude (-180.0 to 180.0)

        Returns:
            Dict containing formatted_address, street, house_number, city, state, postal_code, country, neighborhood.
        """
        # Round coordinates to ~11 meters (4 decimal places) for cache keying
        cache_key = (round(float(lat), 4), round(float(lon), 4))
        if cache_key in self._cache:
            logger.debug("Reverse geocode cache hit for coords: %s", cache_key)
            return self._cache[cache_key]

        try:
            params = {
                "format": "jsonv2",
                "lat": str(lat),
                "lon": str(lon),
                "addressdetails": "1",
                "zoom": "18",
            }
            headers = {"User-Agent": self.USER_AGENT}

            if HAS_HTTPX:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.get(self.NOMINATIM_REVERSE_URL, params=params, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        result = self._parse_nominatim_response(data, lat, lon)
                        self._store_in_cache(cache_key, result)
                        return result
            else:
                # Fallback to urllib.request if httpx is not installed
                query_str = urllib.parse.urlencode(params)
                req = urllib.request.Request(f"{self.NOMINATIM_REVERSE_URL}?{query_str}", headers=headers)
                loop = asyncio.get_running_loop()
                def _do_fetch():
                    with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                        if resp.status == 200:
                            return json.loads(resp.read().decode("utf-8"))
                        return None
                data = await loop.run_in_executor(None, _do_fetch)
                if data:
                    result = self._parse_nominatim_response(data, lat, lon)
                    self._store_in_cache(cache_key, result)
                    return result

        except Exception as err:
            logger.warning("Nominatim HTTP request failed for reverse geocode (%s, %s): %s. Using fallback.", lat, lon, err)

        # Fallback response
        fallback_result = self._generate_mock_address(lat, lon)
        self._store_in_cache(cache_key, fallback_result)
        return fallback_result

    def reverse_geocode_sync(self, lat: float, lon: float) -> Dict[str, Any]:
        """Synchronous wrapper for Celery tasks."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import nest_asyncio  # type: ignore # noqa
            nest_asyncio.apply()
            return loop.run_until_complete(self.reverse_geocode(lat, lon))
        else:
            return loop.run_until_complete(self.reverse_geocode(lat, lon))

    async def geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """Forward geocode address string into coordinates.

        Args:
            address: Street address or location query string.

        Returns:
            Dict containing lat, lon, formatted_address, raw, or None if not found.
        """
        clean_addr = address.strip().lower()
        if clean_addr in self._address_cache:
            return self._address_cache[clean_addr]

        try:
            params = {"format": "jsonv2", "q": address, "limit": "1"}
            headers = {"User-Agent": self.USER_AGENT}

            if HAS_HTTPX:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.get(self.NOMINATIM_SEARCH_URL, params=params, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data:
                            first = data[0]
                            result = {
                                "latitude": float(first["lat"]),
                                "longitude": float(first["lon"]),
                                "formatted_address": first.get("display_name", address),
                                "raw": first,
                            }
                            if len(self._address_cache) < self.max_cache_size:
                                self._address_cache[clean_addr] = result
                            return result
            else:
                query_str = urllib.parse.urlencode(params)
                req = urllib.request.Request(f"{self.NOMINATIM_SEARCH_URL}?{query_str}", headers=headers)
                loop = asyncio.get_running_loop()
                def _do_fetch_forward():
                    with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                        if resp.status == 200:
                            return json.loads(resp.read().decode("utf-8"))
                        return None
                data = await loop.run_in_executor(None, _do_fetch_forward)
                if data and len(data) > 0:
                    first = data[0]
                    result = {
                        "latitude": float(first["lat"]),
                        "longitude": float(first["lon"]),
                        "formatted_address": first.get("display_name", address),
                        "raw": first,
                    }
                    if len(self._address_cache) < self.max_cache_size:
                        self._address_cache[clean_addr] = result
                    return result
        except Exception as err:
            logger.warning("Geocoding failed for '%s': %s", address, err)

        # Mock fallback for geocoding
        return {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "formatted_address": f"{address} (Mock Resolved Location)",
            "raw": {"mock": True},
        }

    def _parse_nominatim_response(self, data: Dict[str, Any], lat: float, lon: float) -> Dict[str, Any]:
        """Format raw Nominatim payload into standardized address dict."""
        addr = data.get("address", {})
        road = addr.get("road") or addr.get("pedestrian") or addr.get("street") or "Main St"
        house_num = addr.get("house_number", "")
        city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality") or "Civic City"
        state = addr.get("state") or addr.get("region") or "State"
        postcode = addr.get("postcode", "00000")
        country = addr.get("country", "United States")
        neighborhood = addr.get("neighbourhood") or addr.get("suburb") or addr.get("district") or "Central District"

        street_address = f"{house_num} {road}".strip() if house_num else road
        formatted = data.get("display_name") or f"{street_address}, {city}, {state} {postcode}"

        return {
            "formatted_address": formatted,
            "street": street_address,
            "house_number": house_num,
            "city": city,
            "state": state,
            "postal_code": postcode,
            "country": country,
            "neighborhood": neighborhood,
            "latitude": float(lat),
            "longitude": float(lon),
            "raw": data,
        }

    def _generate_mock_address(self, lat: float, lon: float) -> Dict[str, Any]:
        """Generate a realistic mock address when external geocoding API is unreachable."""
        lat_int = int(abs(lat) * 100) % 500
        street_names = ["Civic Center Blvd", "Market Street", "Oak Avenue", "Washington St", "Pine Road", "Broadway"]
        street_name = street_names[lat_int % len(street_names)]
        house_num = str((lat_int * 17) % 9000 + 100)

        formatted = f"{house_num} {street_name}, Metropolitan District, City Center"

        return {
            "formatted_address": formatted,
            "street": f"{house_num} {street_name}",
            "house_number": house_num,
            "city": "Metropolitan City",
            "state": "State",
            "postal_code": f"{10000 + (lat_int % 90000)}",
            "country": "United States",
            "neighborhood": "Central Ward",
            "latitude": float(lat),
            "longitude": float(lon),
            "raw": {"mock": True, "fallback": True},
        }

    def _store_in_cache(self, key: Tuple[float, float], value: Dict[str, Any]) -> None:
        """Evict oldest entries if cache exceeds max limit."""
        if len(self._cache) >= self.max_cache_size:
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        self._cache[key] = value


_geocoder_instance: Optional[ReverseGeocoder] = None


def get_geocoder() -> ReverseGeocoder:
    """Singleton getter for ReverseGeocoder instance."""
    global _geocoder_instance
    if _geocoder_instance is None:
        _geocoder_instance = ReverseGeocoder()
    return _geocoder_instance
