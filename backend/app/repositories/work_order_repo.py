"""WorkOrder repository handling data access layer for field work orders."""

from typing import List, Optional, Union, Dict, Any, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.schemas.work_order import WorkOrderCreate, WorkOrderUpdate


class WorkOrderRepository:
    """Async repository for WorkOrder database operations."""

    async def get_by_id(self, db: AsyncSession, work_order_id: int) -> Optional[WorkOrder]:
        """Fetch work order by ID."""
        result = await db.execute(
            select(WorkOrder).where(WorkOrder.id == work_order_id)
        )
        return result.scalars().first()

    async def get_by_number(
        self, db: AsyncSession, work_order_number: str
    ) -> Optional[WorkOrder]:
        """Fetch work order by unique work order number."""
        result = await db.execute(
            select(WorkOrder).where(WorkOrder.work_order_number == work_order_number)
        )
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        issue_id: Optional[int] = None,
        status: Optional[WorkOrderStatus] = None,
        assigned_to_id: Optional[int] = None,
        department_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WorkOrder], int]:
        """Get paginated work orders with optional filtering."""
        query = select(WorkOrder)
        count_query = select(func.count(WorkOrder.id))
        conditions = []

        if issue_id:
            conditions.append(WorkOrder.issue_id == issue_id)
        if status:
            conditions.append(WorkOrder.status == status)
        if assigned_to_id:
            conditions.append(WorkOrder.assigned_to_id == assigned_to_id)
        if department_id:
            conditions.append(WorkOrder.assigned_department_id == department_id)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        count_res = await db.execute(count_query)
        total = count_res.scalar() or 0

        query = query.order_by(WorkOrder.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        orders = list(result.scalars().all())
        return orders, total

    async def create(
        self, db: AsyncSession, obj_in: WorkOrderCreate, work_order_number: str
    ) -> WorkOrder:
        """Create a new Work Order record."""
        db_obj = WorkOrder(
            work_order_number=work_order_number,
            issue_id=obj_in.issue_id,
            title=obj_in.title,
            description=obj_in.description,
            status=WorkOrderStatus.PENDING,
            priority=obj_in.priority,
            assigned_department_id=obj_in.assigned_department_id,
            assigned_to_id=obj_in.assigned_to_id,
            scheduled_start=obj_in.scheduled_start,
            scheduled_end=obj_in.scheduled_end,
            estimated_hours=obj_in.estimated_hours or 0.0,
            notes=obj_in.notes,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: WorkOrder,
        obj_in: Union[WorkOrderUpdate, Dict[str, Any]],
    ) -> WorkOrder:
        """Update existing work order record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


work_order_repo = WorkOrderRepository()
