"""Integration test verifying end-to-end report pipeline."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_end_to_end_report_lifecycle_pipeline(
    client: AsyncClient,
    citizen_token_headers: dict,
    staff_token_headers: dict,
    sample_department,
):
    """Verify complete flow: Report submission -> Review -> Issue creation -> Work Order dispatch -> Completion cascade."""

    # 1. Citizen submits a report
    report_payload = {
        "title": "Major Water Main Leak",
        "category": "WATER_LEAK",
        "description": "High pressure water leaking onto sidewalk near Mission St.",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "address": "1200 Mission St",
        "neighborhood": "Downtown",
    }
    rep_res = await client.post(
        "/reports/", json=report_payload, headers=citizen_token_headers
    )
    assert rep_res.status_code == 201
    report_data = rep_res.json()
    report_id = report_data["id"]
    assert report_data["status"] == "SUBMITTED"
    assert report_data["priority"] in ["MEDIUM", "HIGH", "URGENT"]

    # 2. Municipal Staff reviews report
    review_res = await client.patch(
        f"/reports/{report_id}/status?status=UNDER_REVIEW",
        headers=staff_token_headers,
    )
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "UNDER_REVIEW"

    # 3. Staff creates an Issue and links the initial report
    issue_payload = {
        "title": "Mission St Water Main Failure",
        "category": "WATER_LEAK",
        "description": "Water main pipe crack requiring field excavation.",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "address": "1200 Mission St",
        "neighborhood": "Downtown",
        "department_id": sample_department.id,
        "estimated_cost": 2500.0,
    }
    issue_res = await client.post(
        f"/issues/?initial_report_id={report_id}",
        json=issue_payload,
        headers=staff_token_headers,
    )
    assert issue_res.status_code == 201
    issue_data = issue_res.json()
    issue_id = issue_data["id"]
    assert issue_data["status"] == "OPEN"

    # Verify report status moved to APPROVED upon linking
    rep_check = await client.get(f"/reports/{report_id}")
    assert rep_check.json()["status"] == "APPROVED"

    # 4. Create Work Order for field crew
    wo_payload = {
        "issue_id": issue_id,
        "title": "Replace broken pipe section",
        "description": "Excavate sidewalk and replace 2-inch pipe coupling.",
        "priority": "HIGH",
        "assigned_department_id": sample_department.id,
        "estimated_hours": 6.0,
    }
    wo_res = await client.post(
        "/work-orders/", json=wo_payload, headers=staff_token_headers
    )
    assert wo_res.status_code == 201
    wo_data = wo_res.json()
    wo_id = wo_data["id"]
    assert wo_data["status"] == "PENDING"

    # Verify Issue status automatically moved to IN_PROGRESS upon WO creation
    iss_check = await client.get(f"/issues/{issue_id}")
    assert iss_check.json()["status"] == "IN_PROGRESS"

    # 5. Field Crew completes Work Order
    wo_complete_res = await client.patch(
        f"/work-orders/{wo_id}/status?status=COMPLETED",
        headers=staff_token_headers,
    )
    assert wo_complete_res.status_code == 200
    assert wo_complete_res.json()["status"] == "COMPLETED"

    # 6. Verify Work Order completion cascaded Issue status to RESOLVED
    iss_final = await client.get(f"/issues/{issue_id}")
    assert iss_final.json()["status"] == "RESOLVED"

    # 7. Verify Issue resolution cascaded Report status to RESOLVED
    rep_final = await client.get(f"/reports/{report_id}")
    assert rep_final.json()["status"] == "RESOLVED"

    # 8. Verify citizen received notification
    notif_res = await client.get("/notifications/", headers=citizen_token_headers)
    assert notif_res.status_code == 200
    notifications = notif_res.json()
    assert len(notifications) > 0
    assert any("Resolved" in n["title"] or "Submitted" in n["title"] for n in notifications)
