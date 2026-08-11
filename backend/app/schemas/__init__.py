"""Schemas package exposing all Pydantic v2 schemas."""

from app.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse, UserLogin, Token
from app.schemas.department import (
    DepartmentBase,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
)
from app.schemas.report import (
    LocationCreate,
    LocationResponse,
    ReportBase,
    ReportCreate,
    ReportUpdate,
    ReportFilter,
    ReportResponse,
    PriorityScoreBreakdown,
)
from app.schemas.issue import IssueBase, IssueCreate, IssueUpdate, IssueResponse
from app.schemas.work_order import (
    WorkOrderBase,
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderResponse,
)
from app.schemas.notification import (
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
)
from app.schemas.analytics import (
    CategoryCount,
    StatusCount,
    DashboardStats,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "LocationCreate",
    "LocationResponse",
    "ReportBase",
    "ReportCreate",
    "ReportUpdate",
    "ReportFilter",
    "ReportResponse",
    "PriorityScoreBreakdown",
    "IssueBase",
    "IssueCreate",
    "IssueUpdate",
    "IssueResponse",
    "WorkOrderBase",
    "WorkOrderCreate",
    "WorkOrderUpdate",
    "WorkOrderResponse",
    "NotificationBase",
    "NotificationCreate",
    "NotificationResponse",
    "CategoryCount",
    "StatusCount",
    "DashboardStats",
]
