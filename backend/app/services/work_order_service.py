"""WorkOrder Service handling work order dispatch, status updates, and auto-completion cascades."""

from datetime import datetime, timezone
import random
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.issue import Issue, IssueStatus
from app.repositories.work_order_repo import work_order_repo
from app.repositories.issue_repo import issue_repo
from app.schemas.work_order import WorkOrderCreate, WorkOrderUpdate
from app.services.notification_service import notification_service
from app.models.notification import NotificationType


class WorkOrderService:
    """Business logic for Work Orders dispatches."""

    async def create_work_order(
        self, db: AsyncSession, obj_in: WorkOrderCreate
    ) -> WorkOrder:
        """Create a new work order for an issue."""
        issue = await issue_repo.get_by_id(db, obj_in.issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Linked Issue not found."
            )

        wo_number = f"WO-{datetime.now(timezone.utc).strftime('%Y%m')}-{random.randint(1000, 9999)}"

        wo = await work_order_repo.create(db=db, obj_in=obj_in, work_order_number=wo_number)

        # Update Issue status to IN_PROGRESS if OPEN
        if issue.status == IssueStatus.OPEN:
            issue.status = IssueStatus.IN_PROGRESS
            await db.flush()

        # Notify assigned user if present
        if wo.assigned_to_id:
            await notification_service.send_notification(
                db=db,
                user_id=wo.assigned_to_id,
                title="New Work Order Assigned",
                message=f"You have been assigned Work Order '{wo.title}' ({wo_number}).",
                notification_type=NotificationType.WORK_ORDER,
                reference_id=wo.id,
                reference_type="work_order",
            )

        return wo

    async def get_work_order(self, db: AsyncSession, work_order_id: int) -> WorkOrder:
        """Fetch work order by ID or 404."""
        wo = await work_order_repo.get_by_id(db, work_order_id)
        if not wo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Work Order not found."
            )
        return wo

    async def get_work_orders(
        self,
        db: AsyncSession,
        issue_id: Optional[int] = None,
        status: Optional[WorkOrderStatus] = None,
        assigned_to_id: Optional[int] = None,
        department_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WorkOrder], int]:
        """Get paginated work orders."""
        return await work_order_repo.get_multi(
            db=db,
            issue_id=issue_id,
            status=status,
            assigned_to_id=assigned_to_id,
            department_id=department_id,
            skip=skip,
            limit=limit,
        )

    async def update_work_order(
        self, db: AsyncSession, work_order_id: int, update_in: WorkOrderUpdate
    ) -> WorkOrder:
        """Update work order and process state transitions."""
        wo = await self.get_work_order(db, work_order_id)

        if update_in.status and update_in.status != wo.status:
            await self.update_status(db, work_order_id, update_in.status)
            update_in.status = None

        return await work_order_repo.update(db=db, db_obj=wo, obj_in=update_in)

    async def update_status(
        self, db: AsyncSession, work_order_id: int, new_status: WorkOrderStatus
    ) -> WorkOrder:
        """Update work order status, track execution times, and complete linked issue if all work orders are completed."""
        wo = await self.get_work_order(db, work_order_id)
        now = datetime.now(timezone.utc)

        wo.status = new_status
        if new_status == WorkOrderStatus.IN_PROGRESS and not wo.actual_start:
            wo.actual_start = now
        elif new_status == WorkOrderStatus.COMPLETED:
            if not wo.actual_start:
                wo.actual_start = now
            wo.actual_end = now

        await db.flush()

        # Check if all work orders for issue are complete
        if new_status == WorkOrderStatus.COMPLETED:
            res = await db.execute(
                select(WorkOrder).where(WorkOrder.issue_id == wo.issue_id)
            )
            all_wos = list(res.scalars().all())
            if all(w.status == WorkOrderStatus.COMPLETED for w in all_wos):
                # Trigger Issue RESOLVED cascade via issue_service
                from app.services.issue_service import issue_service

                await issue_service.update_issue_status(
                    db=db, issue_id=wo.issue_id, new_status=IssueStatus.RESOLVED
                )

        return wo


work_order_service = WorkOrderService()
