"""CivicFix Locust Read-Scale Load Test Suite.

Simulates 10x expected peak public read traffic against:
- /api/v1/public/map (Quantized viewport queries with snap_bounds)
- /api/v1/public/stats (Public overview KPIs & performance metrics)
- /api/v1/public/stats/categories (Public category distribution)
"""

import random
from locust import HttpUser, task, between


class CivicFixPublicReaderUser(HttpUser):
    """Simulates a citizen browsing the CivicFix public map and transparency portal."""

    wait_time = between(0.1, 0.5)

    @task(6)
    def view_map_viewport(self):
        """Simulate citizen panning and zooming on the incident map.

        Generates viewport bounds around Annapolis / Maryland coordinates.
        Due to snap_bounds(), multiple users in the same sector hit the micro-cache.
        """
        base_lat = 38.9784 + (random.uniform(-0.01, 0.01))
        base_lng = -76.4922 + (random.uniform(-0.01, 0.01))
        delta = 0.008

        min_lat = round(base_lat - delta, 5)
        max_lat = round(base_lat + delta, 5)
        min_lng = round(base_lng - delta, 5)
        max_lng = round(base_lng + delta, 5)
        zoom = random.choice([13, 14, 14, 15])

        self.client.get(
            f"/api/v1/public/map?min_lat={min_lat}&max_lat={max_lat}&min_lng={min_lng}&max_lng={max_lng}&zoom={zoom}",
            name="/api/v1/public/map",
        )

    @task(3)
    def view_public_stats(self):
        """Simulate citizen viewing the civic transparency overview KPIs."""
        self.client.get("/api/v1/public/stats", name="/api/v1/public/stats")

    @task(1)
    def view_category_breakdown(self):
        """Simulate citizen viewing category distributions."""
        self.client.get("/api/v1/public/stats/categories", name="/api/v1/public/stats/categories")

