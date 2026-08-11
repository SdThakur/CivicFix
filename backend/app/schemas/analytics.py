"""Pydantic v2 schemas for Analytics and Dashboard Metrics."""

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class CategoryCount(BaseModel):
    """Category breakdown count."""

    category: str
    count: int
    percentage: float = 0.0


class StatusCount(BaseModel):
    """Status breakdown count."""

    status: str
    count: int


class NeighborhoodStats(BaseModel):
    """Neighborhood aggregate metric."""

    neighborhood: str
    total_reports: int
    resolved_reports: int
    open_issues: int


class ResolutionTimeStats(BaseModel):
    """Average resolution time metrics in hours."""

    category: str
    avg_resolution_hours: float
    total_resolved: int


class HeatmapPoint(BaseModel):
    """Geospatial heatmap point data."""

    latitude: float
    longitude: float
    weight: float
    category: str
    status: str
    title: str


class DashboardStats(BaseModel):
    """Comprehensive executive dashboard metrics."""

    total_reports: int
    active_issues: int
    pending_work_orders: int
    resolved_reports_this_month: int
    resolved_reports_total: int = 0
    resolution_rate_pct: float = 0.0
    avg_resolution_time_days: float
    status_breakdown: List[StatusCount]
    category_breakdown: List[CategoryCount]
    top_neighborhoods: List[NeighborhoodStats]


class DepartmentPerformance(BaseModel):
    """Department performance metrics schema."""

    department_id: str
    department_name: str
    total_issues: int
    resolved_issues: int
    avg_resolution_hours: float
    work_orders_completed: int


DashboardAnalytics = DashboardStats
