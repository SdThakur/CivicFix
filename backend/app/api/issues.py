"""Issue API Router."""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.models.issue import IssueStatus
from app.models.report import ReportCategory, PriorityLevel
from app.schemas.issue import IssueCreate, IssueUpdate, IssueResponse
from app.services.issue_service import issue_service
from app.repositories.report_repo import report_repo

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
async def create_issue(
    issue_in: Optional[IssueCreate] = None,
    initial_report_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)
    ),
) -> IssueResponse:
    """Create a new aggregated Issue (Staff/Manager/Admin)."""
    if issue_in is None:
        if not initial_report_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either issue request body or initial_report_id query parameter is required."
            )
        report = await report_repo.get_by_id(db, initial_report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_444_NOT_FOUND if hasattr(status, 'HTTP_444_NOT_FOUND') else 404,
                detail=f"Report with id {initial_report_id} not found."
            )
        issue_in = IssueCreate(
            title=report.title,
            category=report.category,
            description=report.description,
            priority=report.priority,
            latitude=report.latitude,
            longitude=report.longitude,
            address=report.address or "",
            neighborhood=report.neighborhood or "",
        )

    issue = await issue_service.create_issue(
        db=db, issue_in=issue_in, initial_report_id=initial_report_id
    )
    return IssueResponse.model_validate(issue)


def parse_enum_or_none(enum_cls: Any, raw_val: Optional[str]) -> Any:
    if not raw_val or not isinstance(raw_val, str):
        return None
    cleaned = raw_val.strip().upper().replace(" ", "_").replace("-", "_")

    for member in enum_cls:
        if member.value == cleaned or member.name == cleaned:
            return member

    if enum_cls == ReportCategory:
        if "ROAD" in cleaned or "SIDEWALK" in cleaned or "PAVEMENT" in cleaned:
            return ReportCategory.POTHOLE
        if "WATER" in cleaned or "DRAIN" in cleaned or "SEWER" in cleaned:
            return ReportCategory.WATER_LEAK
        if "LIGHT" in cleaned or "LAMP" in cleaned:
            return ReportCategory.STREETLIGHT
        if "SIGNAL" in cleaned or "TRAFFIC" in cleaned:
            return ReportCategory.TRAFFIC_SIGNAL
        if "GARBAGE" in cleaned or "WASTE" in cleaned:
            return ReportCategory.TRASH
        return ReportCategory.OTHER

    if enum_cls == IssueStatus:
        if cleaned in ("SUBMITTED", "PENDING", "NEW", "REVIEW", "UNDER_REVIEW"):
            return IssueStatus.OPEN
        if cleaned in ("VERIFICATION", "IN_PROGRESS", "ASSIGNED", "WORKING"):
            return IssueStatus.IN_PROGRESS
        if cleaned in ("RESOLVED", "COMPLETED", "FIXED"):
            return IssueStatus.RESOLVED
        if cleaned in ("CLOSED", "REJECTED", "CANCELLED"):
            return IssueStatus.CLOSED
        return None

    if enum_cls == PriorityLevel:
        if cleaned in ("URGENT", "CRITICAL", "EMERGENCY"):
            return PriorityLevel.URGENT
        if cleaned in ("HIGH", "SEVERE"):
            return PriorityLevel.HIGH
        if cleaned in ("MEDIUM", "MODERATE", "NORMAL"):
            return PriorityLevel.MEDIUM
        if cleaned in ("LOW", "MINOR"):
            return PriorityLevel.LOW

    return None


@router.get("/", response_model=List[IssueResponse])
async def list_issues(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    department_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> List[IssueResponse]:
    """List issues with optional flexible string filters."""
    parsed_status = parse_enum_or_none(IssueStatus, status)
    parsed_category = parse_enum_or_none(ReportCategory, category)
    parsed_priority = parse_enum_or_none(PriorityLevel, priority)

    issues, _ = await issue_service.get_issues(
        db=db,
        status=parsed_status,
        category=parsed_category,
        priority=parsed_priority,
        department_id=department_id,
        skip=skip,
        limit=limit,
    )
    return [IssueResponse.model_validate(i) for i in issues]


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: int, db: AsyncSession = Depends(get_db)
) -> IssueResponse:
    """Get issue by ID."""
    issue = await issue_service.get_issue(db=db, issue_id=issue_id)
    return IssueResponse.model_validate(issue)


@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    update_in: IssueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)
    ),
) -> IssueResponse:
    """Update issue details (Staff/Manager/Admin)."""
    issue = await issue_service.update_issue(
        db=db, issue_id=issue_id, update_in=update_in
    )
    return IssueResponse.model_validate(issue)


@router.patch("/{issue_id}/status", response_model=IssueResponse)
async def update_issue_status(
    issue_id: int,
    status_val: IssueStatus = Query(..., alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)
    ),
) -> IssueResponse:
    """Update issue status (Staff/Manager/Admin). Cascades resolution to linked reports."""
    issue = await issue_service.update_issue_status(
        db=db, issue_id=issue_id, new_status=status_val
    )
    return IssueResponse.model_validate(issue)


@router.post("/{issue_id}/merge-report/{report_id}", response_model=IssueResponse)
async def merge_report_into_issue(
    issue_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)
    ),
) -> IssueResponse:
    """Merge an additional report into an issue."""
    issue = await issue_service.merge_report_into_issue(
        db=db, issue_id=issue_id, report_id=report_id
    )
    return IssueResponse.model_validate(issue)
