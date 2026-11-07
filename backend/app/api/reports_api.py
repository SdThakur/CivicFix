"""Reports API forwarder for app package structure."""
import sys
from pathlib import Path

# Add backend directory to path if needed
backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from reports_api import router, AsyncReportCreate, AsyncReportResponse, ReportDetailResponse

__all__ = ["router", "AsyncReportCreate", "AsyncReportResponse", "ReportDetailResponse"]

