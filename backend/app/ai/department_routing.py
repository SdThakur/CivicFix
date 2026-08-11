"""Department routing engine mapping issue categories and tags to municipal departments."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DepartmentRouter:
    """Automated department router for assigning civic infrastructure reports to appropriate municipal entities."""

    DEPARTMENTS = {
        "DPW": {
            "name": "Department of Public Works",
            "code": "DPW",
            "contact_email": "dpw-dispatch@civicfix.gov",
            "default_sla_hours": 48,
            "auto_assign_team": "Road Maintenance Crew Alpha",
            "categories": [
                "pothole",
                "road_damage",
                "asphalt_crack",
                "sidewalk_damage",
                "sidewalk_crack",
                "bridge_damage",
                "curb_repair",
                "pavement",
            ],
        },
        "DOT": {
            "name": "Department of Transportation",
            "code": "DOT",
            "contact_email": "dot-signals@civicfix.gov",
            "default_sla_hours": 24,
            "auto_assign_team": "Traffic Signal & Sign Techs",
            "categories": [
                "traffic_signal",
                "traffic_signal_fault",
                "traffic_sign",
                "damaged_traffic_sign",
                "street_light",
                "streetlight_failure",
                "road_marking",
                "crosswalk_paint",
                "speed_bump",
            ],
        },
        "WSA": {
            "name": "Water & Sewer Authority",
            "code": "WSA",
            "contact_email": "wsa-emergency@civicfix.gov",
            "default_sla_hours": 12,
            "auto_assign_team": "Hydraulic Emergency Response",
            "categories": [
                "water_leak",
                "pipe_burst",
                "sewer_overflow",
                "drainage_block",
                "storm_drain",
                "manhole_cover",
                "water_main",
                "flooding",
            ],
        },
        "EPS": {
            "name": "Environmental Protection & Sanitation",
            "code": "EPS",
            "contact_email": "sanitation-dispatch@civicfix.gov",
            "default_sla_hours": 72,
            "auto_assign_team": "Sanitation Rapid Response",
            "categories": [
                "illegal_dumping",
                "garbage",
                "hazardous_waste",
                "litter",
                "overflowing_bin",
                "dead_animal",
                "chemical_spill",
            ],
        },
        "PRD": {
            "name": "Parks & Recreation Department",
            "code": "PRD",
            "contact_email": "parks-grounds@civicfix.gov",
            "default_sla_hours": 96,
            "auto_assign_team": "Urban Forestry & Grounds Crew",
            "categories": [
                "fallen_tree",
                "fallen_tree_branch",
                "overgrown_vegetation",
                "park_damage",
                "playground_equipment",
                "tree_hazard",
            ],
        },
        "BEE": {
            "name": "Bureau of Electricity & Energy",
            "code": "BEE",
            "contact_email": "electrical-grid@civicfix.gov",
            "default_sla_hours": 24,
            "auto_assign_team": "Electrical Distribution Squad",
            "categories": [
                "power_outage",
                "exposed_wiring",
                "transformer_fault",
                "utility_pole_damage",
            ],
        },
        "PSCE": {
            "name": "Public Safety & Code Enforcement",
            "code": "PSCE",
            "contact_email": "code-enforcement@civicfix.gov",
            "default_sla_hours": 72,
            "auto_assign_team": "Code Enforcement Inspectors",
            "categories": [
                "graffiti",
                "vandalism",
                "building_code_violation",
                "abandoned_vehicle",
                "noise_complaint",
                "public_safety",
            ],
        },
    }

    # Default fallback department if category is unrecognized
    DEFAULT_DEPARTMENT_CODE = "DPW"

    def route_category(
        self,
        category: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Route an issue to the best-matching municipal department.

        Args:
            category: Primary issue category string.
            description: Technical text description for keyword matching.
            tags: List of issue tags.

        Returns:
            Dict containing department details, code, SLA, assigned team, and confidence.
        """
        clean_cat = str(category).strip().lower().replace(" ", "_")

        # 1. Exact or partial match on defined department categories
        for code, dept in self.DEPARTMENTS.items():
            if clean_cat in dept["categories"]:
                return {
                    "department_code": dept["code"],
                    "department_name": dept["name"],
                    "contact_email": dept["contact_email"],
                    "sla_hours": dept["default_sla_hours"],
                    "auto_assign_team": dept["auto_assign_team"],
                    "routing_method": "exact_category_match",
                    "confidence": 0.98,
                }

        # 2. Match based on keywords in description or tags
        combined_text = f"{clean_cat} {description or ''} {' '.join(tags or [])}".lower()

        keyword_scores: Dict[str, int] = {code: 0 for code in self.DEPARTMENTS}

        for code, dept in self.DEPARTMENTS.items():
            for kw in dept["categories"]:
                kw_clean = kw.replace("_", " ")
                if kw_clean in combined_text:
                    keyword_scores[code] += 2
                elif any(word in combined_text for word in kw_clean.split()):
                    keyword_scores[code] += 1

        best_code = max(keyword_scores, key=keyword_scores.get)  # type: ignore
        best_score = keyword_scores[best_code]

        if best_score > 0:
            dept = self.DEPARTMENTS[best_code]
            return {
                "department_code": dept["code"],
                "department_name": dept["name"],
                "contact_email": dept["contact_email"],
                "sla_hours": dept["default_sla_hours"],
                "auto_assign_team": dept["auto_assign_team"],
                "routing_method": "keyword_heuristics",
                "confidence": min(0.85, 0.50 + (best_score * 0.1)),
            }

        # 3. Default fallback
        fallback_dept = self.DEPARTMENTS[self.DEFAULT_DEPARTMENT_CODE]
        return {
            "department_code": fallback_dept["code"],
            "department_name": fallback_dept["name"],
            "contact_email": fallback_dept["contact_email"],
            "sla_hours": fallback_dept["default_sla_hours"],
            "auto_assign_team": fallback_dept["auto_assign_team"],
            "routing_method": "default_fallback",
            "confidence": 0.40,
        }

    def get_all_departments(self) -> List[Dict[str, Any]]:
        """Return roster of all municipal departments and SLA specifications."""
        return list(self.DEPARTMENTS.values())
