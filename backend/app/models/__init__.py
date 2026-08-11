"""Models package exposing all SQLAlchemy ORM models."""

from app.db.base import Base

# ─── Core Models ──────────────────────────────────────────────────────────────
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.report import Report, ReportStatus, ReportPriority, ReportCategory, PriorityLevel
from app.models.issue import Issue, IssueStatus, IssuePriority
from app.models.work_order import WorkOrder, WorkOrderStatus, WorkOrderPriority
from app.models.notification import Notification, NotificationType

# ─── Asset & Road Network Models ──────────────────────────────────────────────
from app.models.asset import (
    Agency,
    Jurisdiction,
    MaintenanceZone,
    Road,
    RoadSegment,
    InfrastructureAsset,
    RoadClassification,
    OwnershipConfidence,
    AssetType,
    AssetCondition,
    AssetStatus,
)

# ─── 311 Service Request & Inspection Models ──────────────────────────────────
from app.models.service_request import (
    ServiceRequest,
    ServiceRequestStatus,
    ServiceRequestStatusHistory,
)
from app.models.inspection import (
    Inspection,
    InspectionStatus,
    SafetyRiskLevel,
    RepairRecommendation,
)

# ─── SLA Models ───────────────────────────────────────────────────────────────
from app.models.sla import SLARule, SLAEscalationLog

# ─── Crew & Equipment Models ──────────────────────────────────────────────────
from app.models.crew import Crew, CrewMember, Skill, EmployeeSkill, CrewStatus
from app.models.equipment import Equipment, EquipmentType, EquipmentAssignment, EquipmentStatus

# ─── Preventive Maintenance Models ────────────────────────────────────────────
from app.models.preventive_maintenance import (
    MaintenanceRecommendation,
    MaintenanceRecommendationStatus,
    MaintenanceType,
)


__all__ = [
    "Base",
    # Core
    "User", "UserRole",
    "Department",
    "Report", "ReportStatus", "ReportPriority", "ReportCategory", "PriorityLevel",
    "Issue", "IssueStatus", "IssuePriority",
    "WorkOrder", "WorkOrderStatus", "WorkOrderPriority",
    "Notification", "NotificationType",
    # Asset & Road
    "Agency", "Jurisdiction", "MaintenanceZone", "Road", "RoadSegment", "InfrastructureAsset",
    "RoadClassification", "OwnershipConfidence", "AssetType", "AssetCondition", "AssetStatus",
    # Service Request & Inspection
    "ServiceRequest", "ServiceRequestStatus", "ServiceRequestStatusHistory",
    "Inspection", "InspectionStatus", "SafetyRiskLevel", "RepairRecommendation",
    # SLA
    "SLARule", "SLAEscalationLog",
    # Crew & Equipment
    "Crew", "CrewMember", "Skill", "EmployeeSkill", "CrewStatus",
    "Equipment", "EquipmentType", "EquipmentAssignment", "EquipmentStatus",
    # Preventive Maintenance
    "MaintenanceRecommendation", "MaintenanceRecommendationStatus", "MaintenanceType",
]
