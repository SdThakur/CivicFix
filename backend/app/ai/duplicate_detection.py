"""Duplicate report detection engine combining geospatial proximity, visual embedding similarity, category, and temporal proximity."""

from datetime import datetime, timezone
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
from app.ai.embeddings import ImageEmbedder

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Detects duplicate civic infrastructure reports using multi-modal similarity metrics.

    Weights:
    - Location Proximity: 45% (0.45)
    - Image Visual Embedding Cosine Similarity: 35% (0.35)
    - Category Match: 10% (0.10)
    - Time Proximity: 10% (0.10)
    """

    WEIGHT_LOCATION = 0.45
    WEIGHT_IMAGE_EMBEDDING = 0.35
    WEIGHT_CATEGORY = 0.10
    WEIGHT_TIME = 0.10

    DEFAULT_DUPLICATE_THRESHOLD = 0.75
    MAX_LOCATION_RADIUS_METERS = 150.0  # 150 meters maximum similarity cutoff
    MAX_TIME_WINDOW_DAYS = 14.0  # 14 days time decay window

    def __init__(self, embedder: Optional[ImageEmbedder] = None):
        self.embedder = embedder or ImageEmbedder()

    def calculate_similarity(
        self,
        report_a: Dict[str, Any],
        report_b: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute composite duplicate similarity score between two reports or report & existing issue.

        Args:
            report_a: Dict with keys: lat/latitude, lon/longitude, category, image_embedding, created_at/timestamp
            report_b: Dict with matching keys

        Returns:
            Dict containing overall_similarity (0.0 to 1.0), is_duplicate (bool), and breakdown.
        """
        # 1. Location similarity (Haversine distance)
        lat_a = self._extract_float(report_a, ["lat", "latitude"])
        lon_a = self._extract_float(report_a, ["lon", "lng", "longitude"])
        lat_b = self._extract_float(report_b, ["lat", "latitude"])
        lon_b = self._extract_float(report_b, ["lon", "lng", "longitude"])

        if lat_a is not None and lon_a is not None and lat_b is not None and lon_b is not None:
            dist_meters = self.haversine_distance(lat_a, lon_a, lat_b, lon_b)
            # Linear decay from 1.0 at 0m to 0.0 at MAX_LOCATION_RADIUS_METERS
            loc_sim = max(0.0, 1.0 - (dist_meters / self.MAX_LOCATION_RADIUS_METERS))
        else:
            dist_meters = None
            loc_sim = 0.0

        # 2. Image Embedding Cosine Similarity
        emb_a = report_a.get("image_embedding") or report_a.get("embedding")
        emb_b = report_b.get("image_embedding") or report_b.get("embedding")

        if isinstance(emb_a, list) and isinstance(emb_b, list) and len(emb_a) > 0 and len(emb_b) > 0:
            cosine_sim = self.embedder.cosine_similarity(emb_a, emb_b)
            # Map cosine sim from [-1.0, 1.0] to [0.0, 1.0]
            img_sim = max(0.0, (cosine_sim + 1.0) / 2.0) if cosine_sim < 0 else cosine_sim
        else:
            cosine_sim = None
            img_sim = 0.0

        # 3. Category Match
        cat_a = str(report_a.get("category", "")).strip().lower()
        cat_b = str(report_b.get("category", "")).strip().lower()

        if cat_a and cat_b:
            if cat_a == cat_b:
                cat_sim = 1.0
            elif cat_a in cat_b or cat_b in cat_a:
                cat_sim = 0.70
            else:
                cat_sim = 0.0
        else:
            cat_sim = 0.50  # Neutral if category is missing

        # 4. Time Proximity
        dt_a = self._extract_datetime(report_a)
        dt_b = self._extract_datetime(report_b)

        if dt_a and dt_b:
            hours_diff = abs((dt_a - dt_b).total_seconds()) / 3600.0
            days_diff = hours_diff / 24.0
            time_sim = max(0.0, 1.0 - (days_diff / self.MAX_TIME_WINDOW_DAYS))
        else:
            hours_diff = None
            time_sim = 0.50

        # Dynamic weight adjustment if embedding or location missing
        effective_w_loc = self.WEIGHT_LOCATION if dist_meters is not None else 0.0
        effective_w_img = self.WEIGHT_IMAGE_EMBEDDING if cosine_sim is not None else 0.0
        effective_w_cat = self.WEIGHT_CATEGORY
        effective_w_time = self.WEIGHT_TIME

        weight_sum = effective_w_loc + effective_w_img + effective_w_cat + effective_w_time
        if weight_sum > 0:
            overall_score = (
                (loc_sim * effective_w_loc)
                + (img_sim * effective_w_img)
                + (cat_sim * effective_w_cat)
                + (time_sim * effective_w_time)
            ) / weight_sum
        else:
            overall_score = 0.0

        overall_score = round(overall_score, 4)
        is_duplicate = overall_score >= self.DEFAULT_DUPLICATE_THRESHOLD

        return {
            "overall_similarity": overall_score,
            "is_duplicate": is_duplicate,
            "breakdown": {
                "location": {
                    "distance_meters": round(dist_meters, 1) if dist_meters is not None else None,
                    "similarity": round(loc_sim, 4),
                    "weight": self.WEIGHT_LOCATION,
                },
                "image_embedding": {
                    "cosine_similarity": round(cosine_sim, 4) if cosine_sim is not None else None,
                    "similarity": round(img_sim, 4),
                    "weight": self.WEIGHT_IMAGE_EMBEDDING,
                },
                "category": {
                    "cat_a": cat_a,
                    "cat_b": cat_b,
                    "similarity": round(cat_sim, 4),
                    "weight": self.WEIGHT_CATEGORY,
                },
                "time": {
                    "hours_difference": round(hours_diff, 1) if hours_diff is not None else None,
                    "similarity": round(time_sim, 4),
                    "weight": self.WEIGHT_TIME,
                },
            },
        }

    def find_duplicates(
        self,
        new_report: Dict[str, Any],
        existing_issues: List[Dict[str, Any]],
        threshold: float = DEFAULT_DUPLICATE_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        """Find matching existing issues above duplicate similarity threshold, ordered by similarity.

        Args:
            new_report: Incoming candidate report payload.
            existing_issues: List of active candidate issues/reports from database.
            threshold: Minimum score threshold (default 0.75).

        Returns:
            List of matching issue dicts augmented with similarity results, sorted highest score first.
        """
        matches = []
        for existing in existing_issues:
            sim_result = self.calculate_similarity(new_report, existing)
            if sim_result["overall_similarity"] >= threshold:
                matches.append({
                    "issue_id": existing.get("id") or existing.get("issue_id"),
                    "issue_data": existing,
                    "similarity_score": sim_result["overall_similarity"],
                    "similarity_details": sim_result,
                })

        # Sort descending by similarity score
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points on Earth in meters."""
        R = 6371000.0  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    @staticmethod
    def _extract_float(data: Dict[str, Any], keys: List[str]) -> Optional[float]:
        """Utility to extract float from dict trying alternative key names."""
        for key in keys:
            val = data.get(key)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    continue
        return None

    @staticmethod
    def _extract_datetime(data: Dict[str, Any]) -> Optional[datetime]:
        """Utility to extract datetime object from dict."""
        for key in ["created_at", "timestamp", "reported_at"]:
            val = data.get(key)
            if isinstance(val, datetime):
                return val
            elif isinstance(val, str):
                try:
                    # Clean ISO format
                    clean_str = val.replace("Z", "+00:00")
                    return datetime.fromisoformat(clean_str)
                except Exception:
                    continue
        return None
