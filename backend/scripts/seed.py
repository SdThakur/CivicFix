"""Comprehensive Database Seed Script for CivicFix Platform.

Generates:
- 5 Municipal Departments
- 20 Municipal Employees & Admin staff
- 10 Citizen accounts
- 500 Citizen Reports across 5 realistic neighborhood spatial clusters
- 100 Aggregated Issues
- Work Orders & Field Crew Dispatches
- User System Notifications
"""

import asyncio
from datetime import datetime, timedelta, timezone
import random
import sys
import os

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

# Department mapping by category
CATEGORY_DEPARTMENT_MAP = {
    ReportCategory.POTHOLE: "DPW",
    ReportCategory.TRAFFIC_SIGNAL: "DPW",
    ReportCategory.STREETLIGHT: "DPW",
    ReportCategory.WATER_LEAK: "DWS",
    ReportCategory.GRAFFITI: "DPR",
    ReportCategory.PARK_DAMAGE: "DPR",
    ReportCategory.TRASH: "DSW",
    ReportCategory.OTHER: "GCS",
}

# Realistic Neighborhood Geographic Clusters
NEIGHBORHOOD_CLUSTERS = [
    {
        "name": "Downtown",
        "base_lat": 37.7749,
        "base_lon": -122.4194,
        "streets": ["Market St", "Mission St", "Howard St", "1st St", "5th St"],
    },
    {
        "name": "North End",
        "base_lat": 37.7950,
        "base_lon": -122.4080,
        "streets": ["Columbus Ave", "Broadway", "Lombard St", "Greenwich St"],
    },
    {
        "name": "Westside",
        "base_lat": 37.7600,
        "base_lon": -122.4700,
        "streets": ["Geary Blvd", "Balboa St", "Fulton St", "19th Ave"],
    },
    {
        "name": "East Bay",
        "base_lat": 37.7800,
        "base_lon": -122.3900,
        "streets": ["Embarcadero", "Folsom St", "Harrison St", "Spear St"],
    },
    {
        "name": "South Hill",
        "base_lat": 37.7400,
        "base_lon": -122.4200,
        "streets": ["Mission St", "Cortland Ave", "Valencia St", "24th St"],
    },
]

REPORT_TEMPLATES = {
    ReportCategory.POTHOLE: [
        ("Deep pothole in right lane", "Large 6-inch deep pothole causing severe tire damage to passing vehicles."),
        ("Cracked asphalt and pothole cluster", "Multiple consecutive potholes opening up near the bus stop."),
        ("Sunken road trench", "Recent utility digging left a severe bump and pothole across the lane."),
    ],
    ReportCategory.STREETLIGHT: [
        ("Flickering streetlight fixture", "Streetlight on corner flickers constantly at night causing dark spots."),
        ("Completely dark lamp post", "Lamp post #402 is completely unlit, creating a safety hazard for pedestrians."),
        ("Damaged light pole base", "Vehicle scraped pole base, wires slightly exposed near bottom panel."),
    ],
    ReportCategory.WATER_LEAK: [
        ("Water leaking from main valve", "Clean water pooling rapidly on sidewalk from underground pipe seam."),
        ("Hydrant slow leak", "Fire hydrant caps leaking water onto curb continuously."),
        ("Water main break stream", "Pressurized water bubbling up through cracks in asphalt road."),
    ],
    ReportCategory.GRAFFITI: [
        ("Vandalism on public building wall", "Spray paint tag spanning 10 feet on public library exterior wall."),
        ("Graffiti on traffic sign", "Stop sign vandalized with black paint, obscuring readability."),
        ("Bridge pillar spray paint", "Overpass concrete pillar marked with fresh graffiti."),
    ],
    ReportCategory.TRASH: [
        ("Overflowing public trash can", "Public bin stuffed with household waste and litter spilling onto sidewalk."),
        ("Illegal dumping of mattress and furniture", "Old mattress, sofa, and electronics dumped in alleyway."),
        ("Debris cluttering storm drain", "Cardboard boxes and plastic bags completely blocking storm drain intake."),
    ],
    ReportCategory.PARK_DAMAGE: [
        ("Broken wooden park bench", "Support slat broken on bench near playground area."),
        ("Damaged playground swing set", "Chain snapped on child swing set in main park lawn."),
        ("Fallen tree branch on walking path", "Large oak tree branch blocking pedestrian walking trail."),
    ],
    ReportCategory.TRAFFIC_SIGNAL: [
        ("Traffic light stuck on red", "Northbound traffic signal remains stuck on red for over 15 minutes."),
        ("Pedestrian push button broken", "Crosswalk button unattached and dangling by wire."),
        ("Traffic signal light bulb out", "Green light bulb burned out on main arterial intersection."),
    ],
    ReportCategory.OTHER: [
        ("Damaged sidewalk curb", "Curbing shattered near driveway apron."),
        ("Missing storm drain grate", "Metal grate missing, creating open drop hazard on bike lane."),
        ("Obscured street sign", "Overgrown tree branches obscuring street name sign."),
    ],
}


async def seed_data():
    """Main database seeding function."""
    print("Starting CivicFix Database Seeding...")

    async with engine.begin() as conn:
        print("Creating database tables...")
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
        for name, code, desc, email, phone in depts_data:
            d = Department(
                name=name, code=code, description=desc, contact_email=email, phone=phone
            )
            session.add(d)
            departments.append(d)
        await session.flush()
        dept_map = {d.code: d for d in departments}

        # 2. Create Users (20 Municipal Employees & Admin + 10 Citizens)
        print("Seeding 30 User accounts (Municipal Staff, Managers, Admins, Citizens)...")
        hashed_pwd = get_password_hash("password123")
        users = []

        # Admin user
        admin = User(
            email="admin@civicfix.gov",
            hashed_password=hashed_pwd,
            full_name="Alice Admin",
            role=UserRole.ADMIN,
            is_active=True,
            department_id=dept_map["DPW"].id,
        )
        session.add(admin)
        users.append(admin)

        # 5 Managers (1 per department)
        dept_codes = ["DPW", "DWS", "DPR", "DSW", "GCS"]
        managers = []
        for i, code in enumerate(dept_codes):
            m = User(
                email=f"manager.{code.lower()}@civicfix.gov",
                hashed_password=hashed_pwd,
                full_name=f"Manager {code}",
                role=UserRole.MANAGER,
                is_active=True,
                department_id=dept_map[code].id,
            )
            session.add(m)
            managers.append(m)
            users.append(m)

        # 14 Staff / Field Technicians
        staff_members = []
        for i in range(14):
            dept_code = dept_codes[i % len(dept_codes)]
            s = User(
                email=f"staff{i+1}.{dept_code.lower()}@civicfix.gov",
                hashed_password=hashed_pwd,
                full_name=f"Technician {i+1} ({dept_code})",
                role=UserRole.STAFF,
                is_active=True,
                department_id=dept_map[dept_code].id,
            )
            session.add(s)
            staff_members.append(s)
            users.append(s)

        # 10 Citizens
        citizens = []
        for i in range(10):
            c = User(
                email=f"citizen{i+1}@example.com",
                hashed_password=hashed_pwd,
                full_name=f"Citizen {i+1}",
                role=UserRole.CITIZEN,
                is_active=True,
            )
            session.add(c)
            citizens.append(c)
            users.append(c)

        await session.flush()

        # 3. Create 500 Citizen Reports across 5 Neighborhood Clusters
        print("Seeding 500 Citizen Reports across neighborhood spatial clusters...")
        reports = []
        categories = list(ReportCategory)
        statuses = [
            ReportStatus.SUBMITTED,
            ReportStatus.UNDER_REVIEW,
            ReportStatus.APPROVED,
            ReportStatus.IN_PROGRESS,
            ReportStatus.RESOLVED,
        ]
        priorities = list(PriorityLevel)

        now = datetime.now(timezone.utc)

        for i in range(500):
            cluster = random.choice(NEIGHBORHOOD_CLUSTERS)
            cat = random.choice(categories)
            title_tpl, desc_tpl = random.choice(REPORT_TEMPLATES[cat])

            lat = cluster["base_lat"] + random.uniform(-0.012, 0.012)
            lon = cluster["base_lon"] + random.uniform(-0.012, 0.012)
            street = random.choice(cluster["streets"])
            street_num = random.randint(100, 4999)
            address = f"{street_num} {street}, San Francisco, CA"

            created_days_ago = random.uniform(0.1, 60.0)
            created_dt = now - timedelta(days=created_days_ago)

            status_val = random.choice(statuses)
            priority_val = random.choice(priorities)
            upvotes_val = random.randint(0, 15)
            citizen_user = random.choice(citizens)

            rep = Report(
                tracking_number=f"REP-2026{i+1:04d}",
                title=f"{title_tpl} near {street}",
                category=cat,
                description=desc_tpl,
                status=status_val,
                priority=priority_val,
                user_id=citizen_user.id,
                latitude=round(lat, 6),
                longitude=round(lon, 6),
                address=address,
                neighborhood=cluster["name"],
                image_urls=[f"https://civicfix.storage/images/report_{i+1}.jpg"],
                ai_score=round(random.uniform(25.0, 95.0), 2),
                upvotes=upvotes_val,
                created_at=created_dt,
                updated_at=created_dt + timedelta(hours=random.uniform(1, 24)),
            )
            session.add(rep)
            reports.append(rep)

        await session.flush()

        for i in range(100, 150):
            target_original = reports[i - 50]
            rep = reports[i]
            rep.is_duplicate = True
            rep.duplicate_of_id = target_original.id
            rep.status = ReportStatus.DUPLICATE

        await session.flush()

        # 4. Create 100 Aggregated Issues
        print("Seeding 100 Aggregated Municipal Issues...")
        issues = []
        issue_statuses = list(IssueStatus)

        for i in range(100):
            sample_report = reports[i * 4]
            dept_code = CATEGORY_DEPARTMENT_MAP.get(sample_report.category, "GCS")
            target_dept = dept_map[dept_code]
            assigned_staff = random.choice(
                [s for s in staff_members if s.department_id == target_dept.id]
                or staff_members
            )

            iss = Issue(
                issue_code=f"ISS-2026-{i+1:04d}",
                title=f"{sample_report.category.value} Issue: {sample_report.neighborhood}",
                category=sample_report.category,
                description=f"Aggregated civic issue from citizen reports in {sample_report.neighborhood}.",
                status=random.choice(issue_statuses),
                priority=sample_report.priority,
                department_id=target_dept.id,
                assigned_to_id=assigned_staff.id,
                latitude=sample_report.latitude,
                longitude=sample_report.longitude,
                address=sample_report.address,
                neighborhood=sample_report.neighborhood,
                estimated_cost=round(random.uniform(150.0, 3500.0), 2),
                actual_cost=round(random.uniform(100.0, 3000.0), 2),
                total_reports_count=random.randint(1, 6),
                score=round(random.uniform(40.0, 95.0), 2),
                created_at=sample_report.created_at,
                updated_at=sample_report.updated_at,
            )
            session.add(iss)
            issues.append(iss)

        await session.flush()

        for i, rep in enumerate(reports):
            if not rep.is_duplicate:
                assigned_issue = issues[i % len(issues)]
                rep.issue_id = assigned_issue.id

        await session.flush()

        # 5. Create Work Orders
        print("Seeding Work Orders for active and completed dispatches...")
        work_orders = []
        wo_statuses = list(WorkOrderStatus)

        for i, issue_obj in enumerate(issues[:70]):
            dept_staff = [
                s for s in staff_members if s.department_id == issue_obj.department_id
            ]
            assigned_tech = random.choice(dept_staff) if dept_staff else staff_members[0]
            wo_status = random.choice(wo_statuses)

            wo = WorkOrder(
                work_order_number=f"WO-2026-{i+1:04d}",
                issue_id=issue_obj.id,
                title=f"Repair Work: {issue_obj.title}",
                description=f"Dispatch work order for field crew to resolve {issue_obj.title}.",
                status=wo_status,
                priority=issue_obj.priority,
                assigned_department_id=issue_obj.department_id,
                assigned_to_id=assigned_tech.id,
                scheduled_start=issue_obj.created_at + timedelta(days=1),
                scheduled_end=issue_obj.created_at + timedelta(days=3),
                estimated_hours=round(random.uniform(2.0, 16.0), 1),
                actual_hours=round(random.uniform(2.0, 18.0), 1) if wo_status == WorkOrderStatus.COMPLETED else 0.0,
                notes=f"Field crew dispatched to address site at {issue_obj.address}.",
            )
            session.add(wo)
            work_orders.append(wo)

        await session.flush()

        # 6. Create Notifications
        print("Seeding System and Status Notifications...")
        for i in range(100):
            citizen_u = random.choice(citizens)
            sample_rep = random.choice(reports)
            n = Notification(
                user_id=citizen_u.id,
                title="Report Status Update",
                message=f"Your report '{sample_rep.title}' ({sample_rep.tracking_number}) has been updated to {sample_rep.status.value}.",
                type=NotificationType.REPORT_STATUS,
                is_read=random.choice([True, False]),
                reference_id=sample_rep.id,
                reference_type="report",
                created_at=sample_rep.updated_at,
            )
            session.add(n)

        await session.commit()
        print("✅ CivicFix Database Seeding Completed Successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
