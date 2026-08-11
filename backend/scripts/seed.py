"""Clean Database Seed Script for CivicFix Platform.

By default, initializes clean municipal departments, default SLA rules, and core user accounts (Admin, Manager, Inspector, Worker, Citizen) with 0 mock reports.
Pass --mock flag to generate dummy reports for stress testing.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import random
import sys
import os
import argparse

# Add parent dir to path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.report import Report, ReportCategory, ReportStatus, PriorityLevel
from app.models.issue import Issue, IssueStatus
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.notification import Notification, NotificationType
from app.models.crew import Crew, CrewMember, CrewStatus
from app.services.sla_service import SLAService


async def seed_data(generate_mock: bool = False):
    """Main database seeding function."""
    print(f"Starting CivicFix Database Initialization (generate_mock={generate_mock})...")

    async with engine.begin() as conn:
        print("Resetting database schema...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Create 5 Departments
        print("Seeding 5 Municipal Departments...")
        depts_data = [
            ("Department of Public Works", "DPW", "Potholes, streetlights, traffic signals and road maintenance", "dpw@civicfix.gov", "555-0101"),
            ("Department of Water & Sewer", "DWS", "Water main repairs, sewer backup, hydrants, leak management", "dws@civicfix.gov", "555-0102"),
            ("Department of Parks & Recreation", "DPR", "Park facilities, trees, trails, playground equipment, graffiti cleanup", "dpr@civicfix.gov", "555-0103"),
            ("Department of Sanitation & Waste Management", "DSW", "Public trash bins, illegal dumping removal, waste collection", "dsw@civicfix.gov", "555-0104"),
            ("General City Services", "GCS", "General municipal infrastructure, signage, sidewalk repairs", "gcs@civicfix.gov", "555-0105"),
        ]

        departments = []
        dept_map = {}
        for name, code, desc, email, phone in depts_data:
            d = Department(
                name=name, code=code, description=desc, contact_email=email, phone=phone
            )
            session.add(d)
            dept_map[code] = d
            departments.append(d)
        await session.flush()

        # 2. Create Core User Accounts
        print("Seeding Core User Accounts...")
        pwd = get_password_hash("password123")
        admin_pwd = get_password_hash("admin123")
        manager_pwd = get_password_hash("manager123")
        inspector_pwd = get_password_hash("inspector123")
        worker_pwd = get_password_hash("worker123")
        citizen_pwd = get_password_hash("citizen123")

        users = [
            User(email="admin@civicfix.gov", hashed_password=admin_pwd, full_name="Alice Admin", role=UserRole.ADMIN, is_active=True, department_id=dept_map["DPW"].id),
            User(email="manager@civicfix.gov", hashed_password=manager_pwd, full_name="Manager DPW", role=UserRole.MANAGER, is_active=True, department_id=dept_map["DPW"].id),
            User(email="inspector@civicfix.gov", hashed_password=inspector_pwd, full_name="Inspector DPW", role=UserRole.INSPECTOR, is_active=True, department_id=dept_map["DPW"].id),
            User(email="worker@civicfix.gov", hashed_password=worker_pwd, full_name="Field Technician", role=UserRole.FIELD_WORKER, is_active=True, department_id=dept_map["DPW"].id),
            User(email="citizen@civicfix.gov", hashed_password=citizen_pwd, full_name="Citizen Demo", role=UserRole.CITIZEN, is_active=True),
        ]

        for u in users:
            session.add(u)
        await session.flush()

        # 3. Create 1-Person Rapid Response Crew
        print("Seeding 1-Person Rapid Response Crew & Member...")
        crew = Crew(
            name="Alpha Rapid Response Crew",
            crew_code="CREW-ALPHA-01",
            department_id=dept_map["DPW"].id,
            supervisor_id=users[0].id,
            status=CrewStatus.ACTIVE,
            max_concurrent_jobs=3,
            notes="Primary 1-person rapid response repair crew",
        )
        session.add(crew)
        await session.flush()

        crew_member = CrewMember(
            crew_id=crew.id,
            user_id=users[3].id,  # Field Technician (worker@civicfix.gov)
            is_lead=True,
            is_active=True,
        )
        session.add(crew_member)
        await session.flush()

        # 4. Seed Initial Sample Citizen Report & Issue
        print("Seeding Initial Citizen Infrastructure Report...")
        sample_report = Report(
            tracking_number="REP-20260811-1063",
            title="Sagging Overhead Utility Line",
            category=ReportCategory.OTHER,
            description="An overhead utility line, likely a communication or secondary service line, is observed to be significantly sagging or detached from its intended pathway. This condition indicates a failure in its tensioning or anchoring.",
            status=ReportStatus.SUBMITTED,
            priority=PriorityLevel.MEDIUM,
            ai_score=50.0,
            latitude=39.0837,
            longitude=-76.7022,
            address="Odenton Road, Odenton, MD",
            neighborhood="Odenton",
            user_id=users[4].id,  # Citizen Demo
        )
        session.add(sample_report)
        await session.flush()

        # 5. Seed Default SLA Rules
        print("Seeding Default SLA Rules...")
        await SLAService.seed_default_rules(session)

        await session.commit()

    print("✅ Clean Database Initialization Complete! (1-person crew & sample report seeded)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Generate mock reports for stress testing")
    args = parser.parse_args()
    asyncio.run(seed_data(generate_mock=args.mock))
