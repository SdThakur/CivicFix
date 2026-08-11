import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from app.db.session import AsyncSessionLocal
from app.repositories.issue_repo import issue_repo
from app.repositories.report_repo import report_repo
from app.repositories.work_order_repo import work_order_repo
from app.repositories.user_repo import user_repo
from app.services.analytics_service import analytics_service

async def verify():
    async with AsyncSessionLocal() as db:
        issues, issue_count = await issue_repo.get_multi(db)
        print(f"✅ Issues Query OK: {issue_count} issues found")
        
        reports, report_count = await report_repo.get_multi(db)
        print(f"✅ Reports Query OK: {report_count} reports found")
        
        orders, order_count = await work_order_repo.get_multi(db)
        print(f"✅ Work Orders Query OK: {order_count} work orders found")
        
        users = await user_repo.get_multi(db)
        print(f"✅ Users Query OK: {len(users)} users found")
        
        stats = await analytics_service.get_dashboard_stats(db)
        print(f"✅ Analytics Dashboard Stats OK: total_reports={stats.total_reports}")

if __name__ == "__main__":
    asyncio.run(verify())
