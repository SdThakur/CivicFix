from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

class CaseHistoryService:
    async def get_case_history(self, db: AsyncSession, issue_id: int) -> List[Dict[str, Any]]:
        return []
        
    async def get_case_history_for_sr(self, db: AsyncSession, service_request_id: int) -> List[Dict[str, Any]]:
        return []

case_history_service = CaseHistoryService()
