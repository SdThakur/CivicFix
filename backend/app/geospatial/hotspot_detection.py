"""DBSCAN spatial clustering module for identifying municipal issue hotspots."""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class HotspotCluster(BaseModel):
    """Structured representation of a geospatial infrastructure issue hotspot cluster."""

    cluster_id: int = Field(..., description="Unique integer ID of cluster")
    center_lat: float = Field(..., description="Latitude of cluster centroid")
    center_lon: float = Field(..., description="Longitude of cluster centroid")
    radius_km: float = Field(..., description="Radius of cluster bounding area in kilometers")
    point_count: int = Field(..., description="Number of reports/issues in cluster")
    issue_ids: List[str] = Field(default_factory=list, description="List of issue IDs contained in cluster")
    density_score: float = Field(..., description="Density score (issues per sq km)")
    risk_level: str = Field("MEDIUM", description="Qualitative risk classification: LOW, MEDIUM, HIGH, CRITICAL")
    categories: List[str] = Field(default_factory=list, description="Unique categories present in cluster")

    model_config = {
        "extra": "ignore",
    }


class HotspotDetector:
    """DBSCAN spatial hotspot clustering engine for municipal issue identification."""

    EARTH_RADIUS_KM = 6371.0088

    def detect_hotspots(
        self,
        points: List[Union[Dict[str, Any], Tuple[float, float]]],
        eps_km: float = 0.5,
        min_samples: int = 3,
    ) -> Dict[str, Any]:
        """Perform DBSCAN spatial clustering on issue coordinates.

        Args:
            points: List of dicts with 'id' (or 'issue_id'), 'latitude'/'lat', 'longitude'/'lon', 'category'
                    OR list of (lat, lon) coordinate tuples.
            eps_km: Distance threshold in kilometers for neighborhood search (default 0.5 km = 500m).
            min_samples: Minimum number of samples in a neighborhood to form a core point (default 3).

        Returns:
            Dict containing list of HotspotCluster dicts, noise points, total count summary.
        """
        if not points:
            return {
                "clusters": [],
                "noise_points": [],
                "total_clusters": 0,
                "clustered_points_count": 0,
                "unclustered_points_count": 0,
            }

        # Normalize point structures into standardized tuples
        parsed_points: List[Dict[str, Any]] = []
        for idx, pt in enumerate(points):
            if isinstance(pt, (tuple, list)) and len(pt) >= 2:
                parsed_points.append({
                    "id": f"point_{idx}",
                    "lat": float(pt[0]),
                    "lon": float(pt[1]),
                    "category": "unknown",
                    "raw": pt,
                })
            elif isinstance(pt, dict):
                lat = pt.get("latitude") if pt.get("latitude") is not None else pt.get("lat")
                lon = pt.get("longitude") if pt.get("longitude") is not None else pt.get("lon")
                if lat is not None and lon is not None:
                    parsed_points.append({
                        "id": str(pt.get("id") or pt.get("issue_id") or f"point_{idx}"),
                        "lat": float(lat),
                        "lon": float(lon),
                        "category": str(pt.get("category", "unknown")),
                        "raw": pt,
                    })

        if not parsed_points:
            return {
                "clusters": [],
                "noise_points": [],
                "total_clusters": 0,
                "clustered_points_count": 0,
                "unclustered_points_count": 0,
            }

        # Attempt to run scikit-learn DBSCAN with haversine metric
        cluster_labels = self._run_dbscan(parsed_points, eps_km, min_samples)

        # Aggregate points by cluster label
        clusters_map: Dict[int, List[Dict[str, Any]]] = {}
        noise_list: List[Dict[str, Any]] = []

        for pt, label in zip(parsed_points, cluster_labels):
            if label == -1:
                noise_list.append(pt["raw"])
            else:
                if label not in clusters_map:
                    clusters_map[label] = []
                clusters_map[label].append(pt)

        # Formulate HotspotCluster objects
        hotspots: List[HotspotCluster] = []
        for label, cluster_pts in clusters_map.items():
            lats = [p["lat"] for p in cluster_pts]
            lons = [p["lon"] for p in cluster_pts]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)

            # Compute radius (max distance from centroid to any cluster point)
            max_dist_km = max(self._haversine_km(center_lat, center_lon, p["lat"], p["lon"]) for p in cluster_pts)
            radius_km = max(0.05, round(max_dist_km, 3))  # At least 50 meters minimum radius display

            # Calculate density (points per sq km)
            area_sq_km = math.pi * (radius_km ** 2)
            density = round(len(cluster_pts) / area_sq_km, 2)

            risk_level = self._compute_risk_level(len(cluster_pts), density)
            categories = list(set(p["category"] for p in cluster_pts if p["category"] != "unknown"))
            issue_ids = [p["id"] for p in cluster_pts]

            hotspots.append(
                HotspotCluster(
                    cluster_id=label,
                    center_lat=round(center_lat, 6),
                    center_lon=round(center_lon, 6),
                    radius_km=radius_km,
                    point_count=len(cluster_pts),
                    issue_ids=issue_ids,
                    density_score=density,
                    risk_level=risk_level,
                    categories=categories,
                )
            )

        # Sort clusters by point count descending
        hotspots.sort(key=lambda h: h.point_count, reverse=True)

        clustered_count = sum(h.point_count for h in hotspots)
        return {
            "clusters": [h.model_dump() for h in hotspots],
            "noise_points": noise_list,
            "total_clusters": len(hotspots),
            "clustered_points_count": clustered_count,
            "unclustered_points_count": len(noise_list),
        }

    def _run_dbscan(self, points: List[Dict[str, Any]], eps_km: float, min_samples: int) -> List[int]:
        """Run DBSCAN using scikit-learn or fallback spatial grid clustering algorithm."""
        try:
            import numpy as np
            from sklearn.cluster import DBSCAN

            # Convert lat/lon coordinates to radians for haversine metric (np.float64)
            coords = np.array([[math.radians(p["lat"]), math.radians(p["lon"])] for p in points], dtype=np.float64)
            kms_per_radian = self.EARTH_RADIUS_KM
            epsilon = float(eps_km) / kms_per_radian

            db = DBSCAN(eps=epsilon, min_samples=min_samples, metric="haversine")
            labels = db.fit_predict(coords)
            return [int(lbl) for lbl in labels]

        except Exception as err:
            logger.warning("scikit-learn DBSCAN error/unavailable: %s. Using naive spatial radius fallback algorithm.", err)
            return self._fallback_spatial_clustering(points, eps_km, min_samples)

    def _fallback_spatial_clustering(self, points: List[Dict[str, Any]], eps_km: float, min_samples: int) -> List[int]:
        """Simple distance-based spatial clustering fallback algorithm when sklearn is not present."""
        labels = [-1] * len(points)
        cluster_id = 0
        visited = [False] * len(points)

        for i, pt_i in enumerate(points):
            if visited[i]:
                continue
            visited[i] = True

            # Find neighbors within eps_km
            neighbors = []
            for j, pt_j in enumerate(points):
                dist = self._haversine_km(pt_i["lat"], pt_i["lon"], pt_j["lat"], pt_j["lon"])
                if dist <= eps_km:
                    neighbors.append(j)

            if len(neighbors) >= min_samples:
                labels[i] = cluster_id
                k = 0
                while k < len(neighbors):
                    neighbor_idx = neighbors[k]
                    if not visited[neighbor_idx]:
                        visited[neighbor_idx] = True
                        sub_neighbors = []
                        for m, pt_m in enumerate(points):
                            dist = self._haversine_km(points[neighbor_idx]["lat"], points[neighbor_idx]["lon"], pt_m["lat"], pt_m["lon"])
                            if dist <= eps_km:
                                sub_neighbors.append(m)
                        if len(sub_neighbors) >= min_samples:
                            neighbors.extend([n for n in sub_neighbors if n not in neighbors])
                    if labels[neighbor_idx] == -1:
                        labels[neighbor_idx] = cluster_id
                    k += 1
                cluster_id += 1

        return labels

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance in kilometers between two lat/lon coordinates."""
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return self.EARTH_RADIUS_KM * c

    @staticmethod
    def _compute_risk_level(point_count: int, density: float) -> str:
        """Determine hotspot cluster qualitative risk level."""
        if point_count >= 10 or density >= 20.0:
            return "CRITICAL"
        elif point_count >= 6 or density >= 10.0:
            return "HIGH"
        elif point_count >= 3:
            return "MEDIUM"
        else:
            return "LOW"
