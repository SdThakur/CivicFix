"""Priority calculation engine for civic infrastructure issues."""

import logging
import math
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class PriorityEngine:
    """Calculates multi-factor priority score (0-100) for municipal infrastructure issues.

    Factors & Weights:
    - Visual Damage Severity: 30%
    - Location Risk / Proximity Factor: 20%
    - Infrastructure Type Criticality: 20%
    - Citizen Community Escalation (Report Count): 15%
    - Traffic / Arterial Importance: 15%
    """

    WEIGHT_VISUAL_DAMAGE = 0.30
    WEIGHT_LOCATION_RISK = 0.20
    WEIGHT_INFRASTRUCTURE_TYPE = 0.20
    WEIGHT_REPORT_COUNT = 0.15
    WEIGHT_TRAFFIC_IMPORTANCE = 0.15

    # Criticality baseline map for common municipal infrastructure assets (0.0 to 1.0)
    INFRASTRUCTURE_CRITICALITY_MAP = {
        "bridge": 1.00,
        "bridge_damage": 1.00,
        "power_outage": 0.95,
        "exposed_wiring": 0.95,
        "pipe_burst": 0.90,
        "water_leak": 0.85,
        "traffic_signal": 0.85,
        "traffic_signal_fault": 0.85,
        "sewer_overflow": 0.80,
        "pothole_major": 0.75,
        "pothole": 0.70,
        "fallen_tree": 0.65,
        "traffic_sign": 0.60,
        "damaged_traffic_sign": 0.60,
        "sidewalk_crack": 0.45,
        "sidewalk_damage": 0.45,
        "street_light": 0.40,
        "streetlight_failure": 0.40,
        "illegal_dumping": 0.35,
        "garbage": 0.30,
        "graffiti": 0.20,
    }

    # Road / area traffic importance levels
    TRAFFIC_IMPORTANCE_MAP = {
        "highway": 1.00,
        "expressway": 1.00,
        "arterial": 0.85,
        "collector": 0.65,
        "residential": 0.40,
        "alley": 0.20,
        "pedestrian_walkway": 0.30,
    }

    def calculate_priority(
        self,
        visual_damage_score: float,
        location_risk: float = 0.5,
        infrastructure_type: str = "pothole",
        report_count: int = 1,
        traffic_importance: float = 0.5,
        safety_hazard: bool = False,
    ) -> Dict[str, Any]:
        """Calculate issue priority score (0-100) and breakdown dict.

        Args:
            visual_damage_score: Float between 0.0 and 1.0 (or 0-10, will be normalized).
            location_risk: Float between 0.0 and 1.0 (e.g. proximity to school, hospital, flood zone).
            infrastructure_type: Key/category name of the infrastructure component.
            report_count: Total citizen reports filed for this issue.
            traffic_importance: Float 0.0 to 1.0 or road classification string.
            safety_hazard: Boolean override bump if marked as immediate hazard.

        Returns:
            Dict containing total score (0.0 to 100.0), priority_level, and factor breakdown.
        """
        # Normalize visual damage score to [0.0, 1.0] if passed as 0-10
        norm_damage = min(1.0, max(0.0, visual_damage_score / 10.0 if visual_damage_score > 1.0 else visual_damage_score))

        # Clamp location risk
        norm_loc_risk = min(1.0, max(0.0, location_risk))

        # Resolve infrastructure criticality score
        infra_key = str(infrastructure_type).lower().replace(" ", "_")
        infra_score = self.INFRASTRUCTURE_CRITICALITY_MAP.get(infra_key, 0.50)

        # Scale report count logarithmically: 1 report -> 0.0, 5 reports -> 0.65, 15+ reports -> 1.0
        count = max(1, report_count)
        norm_report_count = min(1.0, math.log2(count + 1) / 4.0)

        # Resolve traffic importance score
        if isinstance(traffic_importance, str):
            norm_traffic = self.TRAFFIC_IMPORTANCE_MAP.get(traffic_importance.lower(), 0.50)
        else:
            norm_traffic = min(1.0, max(0.0, float(traffic_importance)))

        # Weighted calculation (0.0 to 1.0)
        weighted_score = (
            (norm_damage * self.WEIGHT_VISUAL_DAMAGE)
            + (norm_loc_risk * self.WEIGHT_LOCATION_RISK)
            + (infra_score * self.WEIGHT_INFRASTRUCTURE_TYPE)
            + (norm_report_count * self.WEIGHT_REPORT_COUNT)
            + (norm_traffic * self.WEIGHT_TRAFFIC_IMPORTANCE)
        )

        # Apply hazard bump if critical safety risk
        if safety_hazard:
            weighted_score = min(1.0, weighted_score * 1.15)

        # Convert to 0-100 score
        total_score = round(weighted_score * 100.0, 1)

        # Determine qualitative level
        priority_level = self._get_priority_level(total_score)

        return {
            "priority_score": total_score,
            "priority_level": priority_level,
            "safety_hazard_override": safety_hazard,
            "breakdown": {
                "visual_damage": {
                    "raw_score": round(norm_damage, 3),
                    "weight": self.WEIGHT_VISUAL_DAMAGE,
                    "weighted_score": round(norm_damage * self.WEIGHT_VISUAL_DAMAGE * 100, 1),
                },
                "location_risk": {
                    "raw_score": round(norm_loc_risk, 3),
                    "weight": self.WEIGHT_LOCATION_RISK,
                    "weighted_score": round(norm_loc_risk * self.WEIGHT_LOCATION_RISK * 100, 1),
                },
                "infrastructure_type": {
                    "type": infra_key,
                    "raw_score": round(infra_score, 3),
                    "weight": self.WEIGHT_INFRASTRUCTURE_TYPE,
                    "weighted_score": round(infra_score * self.WEIGHT_INFRASTRUCTURE_TYPE * 100, 1),
                },
                "report_count": {
                    "count": count,
                    "raw_score": round(norm_report_count, 3),
                    "weight": self.WEIGHT_REPORT_COUNT,
                    "weighted_score": round(norm_report_count * self.WEIGHT_REPORT_COUNT * 100, 1),
                },
                "traffic_importance": {
                    "raw_score": round(norm_traffic, 3),
                    "weight": self.WEIGHT_TRAFFIC_IMPORTANCE,
                    "weighted_score": round(norm_traffic * self.WEIGHT_TRAFFIC_IMPORTANCE * 100, 1),
                },
            },
        }

    @staticmethod
    def _get_priority_level(score: float) -> str:
        """Map score 0-100 to qualitative priority designation."""
        if score >= 80.0:
            return "CRITICAL"
        elif score >= 60.0:
            return "HIGH"
        elif score >= 35.0:
            return "MEDIUM"
        else:
            return "LOW"
