"""API integration tests for Report endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_report(client: AsyncClient, citizen_token_headers: dict):
    """Test report submission by authenticated citizen."""
    payload = {
        "title": "Severe Pothole on Market St",
        "category": "POTHOLE",
        "description": "Large pothole causing vehicle damage near 5th St intersection.",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "address": "500 Market St",
        "neighborhood": "Downtown",
        "image_urls": ["https://example.com/pothole.jpg"],
    }
    response = await client.post(
        "/reports/", json=payload, headers=citizen_token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["category"] == "POTHOLE"
    assert data["status"] == "SUBMITTED"
    assert "tracking_number" in data


@pytest.mark.asyncio
async def test_list_reports(client: AsyncClient, citizen_token_headers: dict):
    """Test retrieving list of reports."""
    # Create two reports
    for i in range(2):
        await client.post(
            "/reports/",
            json={
                "title": f"Report {i+1}",
                "category": "STREETLIGHT",
                "description": "Flickering light fixture",
                "latitude": 37.7750 + i * 0.001,
                "longitude": -122.4190,
                "address": f"{i+1} Light St",
                "neighborhood": "Downtown",
            },
            headers=citizen_token_headers,
        )

    response = await client.get("/reports/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_upvote_report(client: AsyncClient, citizen_token_headers: dict):
    """Test upvoting a report."""
    rep_res = await client.post(
        "/reports/",
        json={
            "title": "Broken Park Bench",
            "category": "PARK_DAMAGE",
            "description": "Bench slat snapped",
            "latitude": 37.7600,
            "longitude": -122.4700,
            "address": "Golden Gate Park",
            "neighborhood": "Westside",
        },
        headers=citizen_token_headers,
    )
    report_id = rep_res.json()["id"]

    upvote_res = await client.post(
        f"/reports/{report_id}/upvote", headers=citizen_token_headers
    )
    assert upvote_res.status_code == 200
    assert upvote_res.json()["upvotes"] == 1


@pytest.mark.asyncio
async def test_staff_update_report_status(
    client: AsyncClient, citizen_token_headers: dict, staff_token_headers: dict
):
    """Test staff updating report status from SUBMITTED to UNDER_REVIEW."""
    rep_res = await client.post(
        "/reports/",
        json={
            "title": "Water Main Leak",
            "category": "WATER_LEAK",
            "description": "Water leaking rapidly",
            "latitude": 37.7800,
            "longitude": -122.3900,
            "address": "100 Folsom St",
            "neighborhood": "East Bay",
        },
        headers=citizen_token_headers,
    )
    report_id = rep_res.json()["id"]

    update_res = await client.patch(
        f"/reports/{report_id}/status?status=UNDER_REVIEW",
        headers=staff_token_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "UNDER_REVIEW"


@pytest.mark.asyncio
async def test_get_nearby_reports(client: AsyncClient, citizen_token_headers: dict):
    """Test fetching reports within a spatial radius of specified coordinates."""
    # Create a report at specific lat/lon
    lat, lon = 39.0785, -76.7047
    await client.post(
        "/reports/",
        json={
            "title": "Nearby Test Pothole",
            "category": "POTHOLE",
            "description": "Pothole for nearby spatial radius test",
            "latitude": lat,
            "longitude": lon,
            "address": "123 Main St",
            "neighborhood": "Central",
        },
        headers=citizen_token_headers,
    )

    response = await client.get(
        f"/reports/nearby?latitude={lat}&longitude={lon}&radius_km=0.5"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(r["title"] == "Nearby Test Pothole" for r in data)
