import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Form, File, UploadFile, Body, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_user, get_optional_current_user, require_roles
from app.core.storage import get_storage_provider
from app.models.user import User, UserRole
from app.models.report import ReportCategory, ReportStatus, PriorityLevel
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportFilter,
)
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    title: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    address: Optional[str] = Form(""),
    neighborhood: Optional[str] = Form(""),
    priority: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    report_in: Optional[ReportCreate] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_optional_current_user),
) -> ReportResponse:
    """Submit a new citizen infrastructure report, supporting JSON & Form/File uploads."""
    if report_in is None:
        if not title or latitude is None or longitude is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Missing required fields: title, latitude, longitude"
            )

        image_urls = []
        if image:
            try:
                storage = get_storage_provider()
                file_bytes = await image.read()
                filename = f"reports/{uuid.uuid4()}_{image.filename}"
                file_url = await storage.upload_file(
                    file_bytes=file_bytes,
                    destination_filename=filename,
                    content_type=image.content_type or "image/jpeg"
                )
                image_urls.append(file_url)
            except Exception:
                image_urls.append("/placeholder_report.jpg")

        report_in = ReportCreate(
            title=title,
            category=category or "OTHER",
            description=description or f"Report for {title}",
            latitude=latitude,
            longitude=longitude,
            address=address or "",
            neighborhood=neighborhood or "",
            image_urls=image_urls,
        )

    report = await report_service.submit_report(
        db=db, report_in=report_in, user_id=current_user.id
    )
    return ReportResponse.model_validate(report)


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    status_filter: Optional[ReportStatus] = Query(None, alias="status"),
    category: Optional[ReportCategory] = None,
    priority: Optional[PriorityLevel] = None,
    neighborhood: Optional[str] = None,
    user_id: Optional[int] = None,
    is_duplicate: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> List[ReportResponse]:
    """Retrieve paginated citizen reports with optional filters."""
    filters = ReportFilter(
        status=status_filter,
        category=category,
        priority=priority,
        neighborhood=neighborhood,
        user_id=user_id,
        is_duplicate=is_duplicate,
        skip=skip,
        limit=limit,
    )
    reports, _ = await report_service.get_reports(db=db, filters=filters)
    return [ReportResponse.model_validate(r) for r in reports]


@router.get("/nearby", response_model=List[ReportResponse])
async def get_nearby_reports(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(2.0, gt=0, le=50.0),
    category: Optional[ReportCategory] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[ReportResponse]:
    """Get reports within a spatial radius of specified coordinates."""
    from app.repositories.report_repo import report_repo

    reports = await report_repo.get_nearby(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        category=category,
        limit=limit,
    )
    return [ReportResponse.model_validate(r) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int, db: AsyncSession = Depends(get_db)
) -> ReportResponse:
    """Get specific report by ID."""
    report = await report_service.get_report(db=db, report_id=report_id)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(
    report_id: int,
    status_val: ReportStatus = Query(..., alias="status"),
    issue_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)
    ),
) -> ReportResponse:
    """Update report status (Staff/Manager/Admin only)."""
    report = await report_service.update_report_status(
        db=db, report_id=report_id, new_status=status_val, issue_id=issue_id
    )
    return ReportResponse.model_validate(report)


@router.post("/{report_id}/upvote", response_model=ReportResponse)
async def upvote_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReportResponse:
    """Upvote a report to increase its priority ranking."""
    report = await report_service.upvote_report(db=db, report_id=report_id)
    return ReportResponse.model_validate(report)
