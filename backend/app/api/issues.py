"""Issue API Router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.models.issue import IssueStatus
from app.models.report import ReportCategory, PriorityLevel
from app.schemas.issue import IssueCreate, IssueUpdate, IssueResponse
from app.services.issue_service import issue_service

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
async def create_issue(
    issue_in: IssueCreate,
    initial_report_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)
    ),
) -> IssueResponse:
    """Create a new aggregated Issue (Staff/Manager/Admin)."""
    issue = await issue_service.create_issue(
        db=db, issue_in=issue_in, initial_report_id=initial_report_id
    )
    return IssueResponse.model_validate(issue)


@router.get("/", response_model=List[IssueResponse])
async def list_issues(
    status_filter: Optional[IssueStatus] = Query(None, alias="status"),
    category: Optional[ReportCategory] = None,
    priority: Optional[PriorityLevel] = None,
    department_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> List[IssueResponse]:
    """List issues with optional filters."""
    issues, _ = await issue_service.get_issues(
        db=db,
        status=status_filter,
        category=category,
        priority=priority,
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
