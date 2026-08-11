"""CivicFix Geospatial Module

Provides reverse and forward geocoding with caching and DBSCAN spatial hotspot clustering.
"""

from app.geospatial.geocoding import ReverseGeocoder, get_geocoder
from app.geospatial.hotspot_detection import HotspotCluster, HotspotDetector

__all__ = [
    "ReverseGeocoder",
    "get_geocoder",
    "HotspotDetector",
    "HotspotCluster",
]
