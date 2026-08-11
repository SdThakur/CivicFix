"""Pydantic v2 schemas for Search operations."""

from typing import List, Optional
from pydantic import BaseModel
from app.schemas.report import ReportResponse
from app.schemas.issue import IssueResponse
from app.schemas.work_order import WorkOrderResponse


class SearchQuery(BaseModel):
    """Global search request parameters."""

    q: str
    category: Optional[str] = None
    neighborhood: Optional[str] = None
    limit: int = 20


class SearchResult(BaseModel):
    """Aggregated global search result DTO."""

    query: str
    reports: List[ReportResponse]
    issues: List[IssueResponse]
    work_orders: List[WorkOrderResponse]
    total_matches: int
