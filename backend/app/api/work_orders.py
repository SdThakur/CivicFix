"""WorkOrder API Router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.models.work_order import WorkOrderStatus
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderResponse,
    WorkOrderReportBlocked
)
from app.services.work_order_service import work_order_service
from fastapi import UploadFile, File, Form
from app.models.work_order import WorkOrder
from sqlalchemy import select
from app.services.notification_service import notification_service
from datetime import datetime, timezone
import os
import shutil

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])


@router.post("/", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    work_order_in: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)
    ),
) -> WorkOrderResponse:
    """Create a field crew Work Order (Staff/Manager/Admin)."""
    wo = await work_order_service.create_work_order(
        db=db, obj_in=work_order_in
    )
    return WorkOrderResponse.model_validate(wo)


@router.get("/", response_model=List[WorkOrderResponse])
async def list_work_orders(
    issue_id: Optional[int] = None,
    status_filter: Optional[WorkOrderStatus] = Query(None, alias="status"),
    assigned_to_id: Optional[int] = None,
    department_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> List[WorkOrderResponse]:
    """List work orders with optional filters."""
    orders, _ = await work_order_service.get_work_orders(
        db=db,
        issue_id=issue_id,
        status=status_filter,
        assigned_to_id=assigned_to_id,
        department_id=department_id,
        skip=skip,
        limit=limit,
    )
    return [WorkOrderResponse.model_validate(w) for w in orders]


@router.get("/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(
    work_order_id: int, db: AsyncSession = Depends(get_db)
) -> WorkOrderResponse:
    """Get work order details by ID."""
    wo = await work_order_service.get_work_order(db=db, work_order_id=work_order_id)
    return WorkOrderResponse.model_validate(wo)


@router.patch("/{work_order_id}", response_model=WorkOrderResponse)
async def update_work_order(
    work_order_id: int,
    update_in: WorkOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)
    ),
) -> WorkOrderResponse:
    """Update work order fields (Staff/Manager/Admin)."""
    wo = await work_order_service.update_work_order(
        db=db, work_order_id=work_order_id, update_in=update_in
    )
    return WorkOrderResponse.model_validate(wo)


@router.patch("/{work_order_id}/status", response_model=WorkOrderResponse)
async def update_work_order_status(
    work_order_id: int,
    status_val: WorkOrderStatus = Query(..., alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)
    ),
) -> WorkOrderResponse:
    """Update work order status."""
    wo = await work_order_service.update_status(
        db=db, work_order_id=work_order_id, new_status=status_val
    )
    return WorkOrderResponse.model_validate(wo)


@router.post("/{work_order_id}/before-photo", response_model=WorkOrderResponse)
async def upload_before_photo(
    work_order_id: int,
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload before photo for work order."""
    wo = await work_order_service.get_work_order(db=db, work_order_id=work_order_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
        
    if image:
        os.makedirs("uploads", exist_ok=True)
        file_path = f"uploads/before_{wo.id}_{image.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        wo.before_photo_url = f"/{file_path}"
    elif image_url:
        wo.before_photo_url = image_url
        
    await db.commit()
    await db.refresh(wo)
    return WorkOrderResponse.model_validate(wo)


@router.post("/{work_order_id}/after-photo", response_model=WorkOrderResponse)
async def upload_after_photo(
    work_order_id: int,
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload after photo for work order."""
    wo = await work_order_service.get_work_order(db=db, work_order_id=work_order_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
        
    if image:
        os.makedirs("uploads", exist_ok=True)
        file_path = f"uploads/after_{wo.id}_{image.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        wo.after_photo_url = f"/{file_path}"
    elif image_url:
        wo.after_photo_url = image_url
        
    await db.commit()
    await db.refresh(wo)
    return WorkOrderResponse.model_validate(wo)


@router.post("/{work_order_id}/report-blocked", response_model=WorkOrderResponse)
async def report_blocked(
    work_order_id: int,
    body: WorkOrderReportBlocked,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Report a work order as blocked."""
    wo = await work_order_service.get_work_order(db=db, work_order_id=work_order_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
        
    wo.status = WorkOrderStatus.BLOCKED
    wo.blocked_reason = body.reason
    wo.blocked_notes = body.notes
    
    # Notify department manager
    # Here assuming user_id 1 is a default manager or we would look it up by department
    manager_id = 1
    await notification_service.send_notification(
        db=db,
        user_id=manager_id,
        title=f"Work Order Blocked: {wo.work_order_number}",
        message=f"Work order blocked due to: {body.reason}",
    )
    
    await db.commit()
    await db.refresh(wo)
    return WorkOrderResponse.model_validate(wo)

