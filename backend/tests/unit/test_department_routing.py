"""Unit tests for Department Routing Logic."""

from app.models.report import ReportCategory
from app.services.report_service import report_service


def test_department_routing_mapping():
    """Verify correct department codes are returned by report categories."""
    assert report_service.route_department_code(ReportCategory.POTHOLE) == "DPW"
    assert report_service.route_department_code(ReportCategory.TRAFFIC_SIGNAL) == "DPW"
    assert report_service.route_department_code(ReportCategory.STREETLIGHT) == "DPW"

    assert report_service.route_department_code(ReportCategory.WATER_LEAK) == "DWS"

    assert report_service.route_department_code(ReportCategory.GRAFFITI) == "DPR"
    assert report_service.route_department_code(ReportCategory.PARK_DAMAGE) == "DPR"

    assert report_service.route_department_code(ReportCategory.TRASH) == "DSW"

    assert report_service.route_department_code(ReportCategory.OTHER) == "GCS"
