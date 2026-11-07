<div align="center">

# 🏛️ CivicFix

### Next-Generation AI & Spatial Operations Platform for Civic Infrastructure

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Supabase](https://img.shields.io/badge/Database-Supabase%20PostGIS-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Frontend-Next.js%2014%20App%20Router-black?logo=next.js)](https://nextjs.org)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![TypeScript 5](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Gemini Vision](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![PostGIS](https://img.shields.io/badge/GIS-PostGIS%20Spatial-blue?logo=postgresql&logoColor=white)](https://postgis.net)

**CivicFix** connects citizens directly to municipal public works operations. Citizens capture infrastructure hazards—potholes, streetlamp failures, downed signs, illegal dumping, water main leaks—and the platform instantly initiates an asynchronous AI triage pipeline: extracting EXIF GPS coordinates, compressing imagery client-side, running Gemini Vision classification, checking 100-meter PostGIS spatial deduplication, calculating transparent multi-factor priority scores, and routing work orders to the appropriate municipal department.

[**Features**](#-key-capabilities) · [**System Architecture (UML)**](#-system-architecture--uml) · [**Database Schema (ER Diagram)**](#-database-schema--er-diagram) · [**Async Ingestion Pipeline**](#-asynchronous-report-pipeline) · [**Quick Start**](#-quick-start) · [**Testing**](#-testing--verification)

</div>

---

## 🌟 Key Capabilities

| Capability | Legacy 311 Systems | CivicFix Modernization |
| :--- | :--- | :--- |
| **Ingestion Pipeline** | Synchronous HTTP POST blocking on photo upload & review | **202 Accepted Async Pipeline** with IndexedDB offline queue & Supabase Realtime status feeds |
| **Hazard Triage** | Manual operator categorization taking 2–5 days | **Gemini 2.5 Flash Vision** classification & damage severity scoring in under 5 seconds |
| **Deduplication** | Duplicate tickets overwhelm call centers & field crews | **Automated 100-Meter PostGIS Spatial Deduplication** (`ST_DWithin`) with instant upvoting |
| **Prioritization** | Opaque, politically influenced, first-come-first-served | **Transparent 5-Factor Algorithmic Score (0–100)** with interactive formula explanation |
| **Closeout Integrity** | Unverified status changes closed out via text note | **Verified Closeout Photo Proofs** with cryptographic trigger guard before status `RESOLVED` |
| **Spatial Visualization** | Static pins or unclustered heavy database queries | **Viewport Bounding Box RPC (`issues_in_bounds`)** with Google Maps clustering & WCAG sheet |
| **Data Protection** | Open access or perimeter firewalls without tenant controls | **PostgreSQL Row-Level Security (RLS)** & strict non-admin role escalation prevention triggers |

---

## 🗺️ System Architecture & UML

### 1. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer ["Citizen & Municipal Frontend (Next.js 14 App Router)"]
        UI["Citizen Camera Capture & Map UI"]
        OfflineQ["IndexedDB Offline Queue & exifr GPS Extraction"]
        SupabaseClient["Supabase Browser Client & Auth (useAuth)"]
    end

    subgraph EdgeStorage ["Edge & Storage Layer (Supabase Cloud)"]
        StorageReports["Storage Bucket: reports (Public Read, Tenant Isolated Upload)"]
        StorageProofs["Storage Bucket: proofs (Private Read, Staff Upload Only)"]
        RealtimeBus["Supabase Realtime (WebSocket Publications)"]
    end

    subgraph BackendAPI ["FastAPI REST Microservice & Workers"]
        FastAPIApp["FastAPI Ingestion Engine (/api/v1/reports)"]
        RateLimiter["IP / User Rate Limiter (10 req/min)"]
        CeleryWorker["Celery / Background Triage Task"]
        SweeperCron["Stale Job Sweeper (Recovers PENDING > 10m)"]
    end

    subgraph AIEngines ["AI & Vision Intelligence"]
        GeminiVision["Gemini 2.5 Flash Vision API"]
        CLIPEmbedder["CLIP ViT-B-32 Image Embeddings"]
    end

    subgraph DatabaseLayer ["Supabase PostgreSQL + PostGIS (Port 6543 Pooler)"]
        ReportsTable[("public.reports (Async Intake)")]
        IssuesTable[("public.issues (PostGIS Point 4326)")]
        AuditLog[("public.audit_log (Append-Only)")]
        MatViews[("Materialized Views: public_stats")]
    end

    UI -->|"1. Extract GPS & WebP Compress"| OfflineQ
    OfflineQ -->|"2. Direct Multipart Upload"| StorageReports
    OfflineQ -->|"3. POST /reports (202 Accepted)"| FastAPIApp
    FastAPIApp --> RateLimiter
    FastAPIApp -->|"Insert PENDING"| ReportsTable
    FastAPIApp -->|"Enqueue Triage"| CeleryWorker

    CeleryWorker -->|"Fetch Image & Classify"| GeminiVision
    CeleryWorker -->|"100m Spatial Query ST_DWithin"| IssuesTable
    CeleryWorker -->|"Update Status: DONE / DUPLICATE"| ReportsTable
    ReportsTable -->|"Postgres Changes Trigger"| RealtimeBus
    RealtimeBus -->|"Live Status Toast & Progress Updates"| SupabaseClient

    SweeperCron -.->|"Auto-recovers stale jobs"| ReportsTable
    FastAPIApp -->|"Resolve Issue with Proof"| StorageProofs
    IssuesTable -->|"Status Change Trigger"| AuditLog
    AuditLog -.->|"Refresh Every 15m"| MatViews
```

---

### 2. Sequence Diagram: Asynchronous Ingestion & Triage Pipeline

The diagram below details the non-blocking 202 submission lifecycle, tenant boundary verification, AI vision classification, spatial deduplication, and real-time state streaming:

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen (Mobile/Web)
    participant Client as Next.js 14 Frontend
    participant SupaStorage as Supabase Storage ('reports')
    participant API as FastAPI Ingestion API
    participant Worker as Background Triage Worker
    participant Gemini as Gemini 2.5 Flash
    participant DB as PostGIS Database
    participant Realtime as Supabase Realtime

    Citizen->>Client: Snap photo & tap "Submit Hazard"
    Client->>Client: Extract EXIF GPS coordinates via dynamic exifr
    Client->>Client: Compress to WebP (~1600px, 82% quality)
    Client->>SupaStorage: Upload WebP to 'reports/{userId}/{uuid}.webp'
    SupaStorage-->>Client: 200 OK (storage path confirmed)

    Client->>API: POST /api/v1/reports {image_path, lat, lng, description}
    API->>API: Verify user tenant prefix matching auth.uid()
    API->>DB: INSERT INTO reports (status='PENDING', lat, lng, image_path)
    DB-->>API: Report UUID generated
    API-->>Client: HTTP 202 Accepted {report_id, status: "PENDING"}

    Client->>Realtime: Subscribe to reports:id=eq.{report_id}
    Client-->>Citizen: Show animated stage tracker (Pending → Processing)

    API->>Worker: Enqueue background triage task
    Worker->>DB: UPDATE reports SET status='PROCESSING'
    DB-->>Realtime: Broadcast 'PROCESSING'
    Realtime-->>Client: Update UI status indicator

    Worker->>Gemini: Analyze image (detect hazard, damage severity 0-100)
    Gemini-->>Worker: {category: "POTHOLE", confidence: 0.94, severity: 85}

    Worker->>DB: Execute ST_DWithin(location, report_location, 100m)
    alt Existing Issue within 100m found
        Worker->>DB: Increment issue upvotes & mark report 'DUPLICATE'
        Worker->>DB: UPDATE reports SET status='DUPLICATE', issue_id=...
    else New Hazard Confirmed
        Worker->>DB: INSERT INTO issues (tracking_number, category, priority_score, location)
        Worker->>DB: UPDATE reports SET status='DONE', issue_id=...
    end

    DB-->>Realtime: Broadcast 'DONE' with issue tracking number
    Realtime-->>Client: Render live issue card with milestone timeline
    Client-->>Citizen: Haptic feedback & confirmation view
```

---

### 3. State Machine Diagrams

#### Citizen Report Intake Lifecycle

```mermaid
stateDiagram-v2
    [*] --> DRAFT: Camera Snap / File Selection
    DRAFT --> QUEUED_OFFLINE: Network Offline (IndexedDB)
    QUEUED_OFFLINE --> PENDING: Online Event Triggered
    DRAFT --> PENDING: Direct Supabase Storage Upload
    
    PENDING --> PROCESSING: Worker Picks Up Job
    PROCESSING --> DONE: Gemini Classification + New Issue Created
    PROCESSING --> DUPLICATE: Matched Existing Issue within 100m
    PROCESSING --> FAILED: Image Unreadable / Gemini Error
    
    FAILED --> PROCESSING: User Taps "Retry Triage"
    PROCESSING --> PENDING: Sweeper Recovers Stale Job (>10m)
    
    DONE --> [*]
    DUPLICATE --> [*]
```

#### Municipal Issue Resolution Lifecycle

```mermaid
stateDiagram-v2
    [*] --> SUBMITTED: Created from Citizen Report
    SUBMITTED --> IN_PROGRESS: Department Dispatched & Crew Assigned
    IN_PROGRESS --> RESOLVED: Closeout Photo Uploaded + Guard Trigger Verified
    RESOLVED --> CLOSED: Citizen Confirmed or 72h Auto-Close
    
    IN_PROGRESS --> CANCELLED: Duplicate or Not City Property
    SUBMITTED --> CANCELLED: Spam / Invalid Submission
    
    RESOLVED --> IN_PROGRESS: Citizen Disputes Resolution
    CLOSED --> [*]
    CANCELLED --> [*]
```

---

## 🗄️ Database Schema & ER Diagram

The database runs on **Supabase PostgreSQL 15+** with **PostGIS extensions**. It employs strict Row-Level Security (RLS), generated spatial geometry points, append-only immutable audit logging, and legacy ORM synchronization triggers.

```mermaid
erDiagram
    PROFILES ||--o{ REPORTS : "submits"
    PROFILES ||--o{ ISSUE_UPVOTES : "casts"
    PROFILES ||--o{ ISSUE_PROOFS : "uploads closeout"
    PROFILES ||--o{ AUDIT_LOG : "records actions"
    ISSUES ||--o{ REPORTS : "consolidates"
    ISSUES ||--o{ ISSUE_UPVOTES : "receives"
    ISSUES ||--o{ ISSUE_PROOFS : "verifies repair"
    ISSUES ||--o{ AUDIT_LOG : "audits state"
    ISSUES ||--o{ WORK_ORDERS : "dispatches"
    DEPARTMENTS ||--o{ ISSUES : "manages"
    DEPARTMENTS ||--o{ CREWS : "directs"
    CREWS ||--o{ WORK_ORDERS : "executes"

    PROFILES {
        uuid id PK "references auth.users"
        text email
        text full_name
        text role "CITIZEN | STAFF | MANAGER | ADMIN | INSPECTOR"
        text avatar_url
        timestamptz created_at
        timestamptz updated_at
    }

    REPORTS {
        uuid id PK "gen_random_uuid()"
        uuid user_id FK "references auth.users"
        uuid issue_id FK "references issues(id)"
        text image_path "Storage path in reports bucket"
        double_precision lat "Latitude [-90, 90]"
        double_precision lng "Longitude [-180, 180]"
        geometry location "Point 4326 (Generated Stored)"
        text category "POTHOLE | STREETLIGHT | GRAFFITI | etc"
        numeric ai_confidence "0.00 - 1.00"
        text status "PENDING | PROCESSING | DONE | FAILED | DUPLICATE"
        text error_message
        boolean is_duplicate
        uuid duplicate_of_id FK
        text tracking_number "Compat RPT-XXXXXXXX"
        text neighborhood "Downtown, North, West, etc"
        timestamptz created_at
        timestamptz updated_at
    }

    ISSUES {
        uuid id PK "gen_random_uuid()"
        text tracking_number UK "ISS-YYYY-XXXXX"
        text title
        text category
        text description
        text status "SUBMITTED | IN_PROGRESS | RESOLVED | CLOSED"
        text priority_level "LOW | MEDIUM | HIGH | URGENT"
        numeric priority_score "0.00 - 100.00"
        jsonb score_factors "Breakdown factors"
        double_precision lat
        double_precision lng
        geometry location "Point 4326 (Generated Stored)"
        text address
        text neighborhood
        text department_code "DPW | DOT | DOH | DEP"
        integer upvotes "Count >= 0"
        integer duplicate_count "Count >= 0"
        text before_photo_path
        text after_photo_path
        timestamptz created_at
        timestamptz updated_at
        timestamptz resolved_at
    }

    ISSUE_UPVOTES {
        uuid id PK
        uuid issue_id FK "references issues(id)"
        uuid user_id FK "references auth.users"
        timestamptz created_at
    }

    ISSUE_PROOFS {
        uuid id PK
        uuid issue_id FK "references issues(id)"
        uuid uploaded_by FK "references auth.users"
        text proof_photo_path "Private bucket path"
        text notes
        timestamptz created_at
    }

    AUDIT_LOG {
        uuid id PK
        uuid issue_id FK "references issues(id)"
        text old_status
        text new_status
        uuid changed_by FK "references auth.users"
        text reason
        timestamptz created_at
    }

    WORK_ORDERS {
        integer id PK
        integer issue_id FK
        integer crew_id FK
        text status "PENDING | IN_PROGRESS | COMPLETED"
        timestamptz scheduled_date
        double_precision estimated_cost
        double_precision actual_cost
    }

    DEPARTMENTS {
        integer id PK
        text name
        text code "DPW | DOT | DEP"
        text email
    }

    CREWS {
        integer id PK
        text name
        integer department_id FK
        integer max_concurrent_jobs
        boolean is_available
    }
```

---

## ⚡ Asynchronous Report Pipeline

The platform uses an asynchronous 202 submission architecture:

1. **Pre-Compression EXIF Extraction**:
   Using dynamic imports of `exifr`, citizen device GPS coordinates and orientation tags are read directly in the browser before image compression.
2. **Client-Side Canvas WebP Compression**:
   Photos are scaled to maximum dimension of 1600px and converted to WebP with an 82% quality factor in an offscreen canvas. This reduces payload size from ~12MB down to ~350KB.
3. **Offline Queue Persistence**:
   Submissions are persisted to an IndexedDB queue (`civicfix_report_drafts`). If the citizen is in a transit dead zone or loses network connectivity, uploads pause and auto-flush on the `online` window event.
4. **202 Accepted Handshake**:
   The FastAPI server acknowledges receipt in milliseconds, verifies the Supabase storage path belongs to the calling user (`reports/<userId>/<reportId>.webp`), and writes a `PENDING` record to PostgreSQL.
5. **Real-time Status Streaming**:
   The frontend connects directly to Supabase Realtime using WebSocket publications (`postgres_changes` on `public.reports`). The citizen watches the live state transition from `PENDING` ➔ `PROCESSING` ➔ `DONE`.
6. **Self-Healing Sweeper**:
   A periodic background recovery task identifies any report stranded in `PROCESSING` for more than 10 minutes and resets it to `PENDING` for automated triage re-run.

---

## ⚖️ Transparent 5-Factor Priority Scoring Formula

CivicFix avoids arbitrary ticket prioritization. Every issue receives a transparent score between **0.00 and 100.00**:

$$\text{Priority Score} = 0.30 \times D + 0.20 \times R + 0.20 \times C + 0.15 \times E + 0.15 \times T$$

Where:
- **$D$ — Visual Damage Severity (30%)**: Evaluated by Gemini Vision (0–100) based on hazard depth, fracture severity, and structural deterioration.
- **$R$ — Location Risk Factor (20%)**: Proximity to schools, elderly centers, hospitals, bike corridors, and high-pedestrian zones.
- **$C$ — Infrastructure Criticality (20%)**: Primary arterial vs. residential alleyway; high-pressure water mains vs. secondary branch lines.
- **$E$ — Community Escalation (15%)**: Logarithmic scaling of community upvotes and 100m duplicate submissions ($15 \times \min(1, \frac{\log(1 + \text{upvotes})}{\log(20)})$).
- **$T$ — Traffic Importance (15%)**: Average daily traffic (ADT) volume of the municipal street segment.

> **Citizen Transparency**: The citizen dashboard includes an expandable *"Why this score?"* card detailing the exact contribution of each factor. Red status badges are reserved exclusively for **Urgent** priority tickets to maintain sensory clarity.

---

## 🔒 Security & PostGIS Integrity

### Row-Level Security (RLS) Model
All database tables enforce PostgreSQL Row-Level Security:
- **`reports`**: Citizens can only insert reports under their own `auth.uid()` path, and can only select their own submissions. Staff and managers have read-only oversight.
- **`issues`**: Publicly readable through sanitized view `public_issues` (hiding citizen PII and internal staff notes). Updates are restricted to staff roles.
- **`issue_proofs`**: Stored in a private Supabase Storage bucket. Non-staff citizens cannot view raw proofs directly; they access time-limited signed URLs (15-minute TTL) generated only after an issue is officially marked `RESOLVED`.
- **Role Escalation Guard**: The `trg_profile_role_guard` trigger blocks non-admin users from altering their role in `public.profiles`.

### Cryptographic Resolve Guard Trigger
An issue cannot transition to `RESOLVED` status via an SQL update unless at least one verified closeout proof photo is attached in `public.issue_proofs`. Attempting to resolve without attached proof raises an SQL exception:
```sql
RAISE EXCEPTION 'Constraint Violation: An issue cannot transition to RESOLVED without verified closeout photo proof.';
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- Supabase Project or local Docker setup

### 1. Clone & Environment Setup

```bash
git clone https://github.com/SdThakur/CivicFix.git
cd CivicFix
```

#### Frontend Setup (`frontend/.env.local`)
```ini
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Supabase Credentials
NEXT_PUBLIC_SUPABASE_URL=https://tywmyjecafmpufdfxbus.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_dSoVH6SAgzYJ7dWeo_drOg_UCcqNmuw

# Feature Flags
NEXT_PUBLIC_ASYNC_REPORTS=true
```

#### Backend Setup (`backend/.env`)
```ini
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=civicfix_super_secret_jwt_key_2026_change_in_production

# Supabase Connection Pooler (Port 6543 Tx mode, Port 5432 Session mode)
DATABASE_URL=postgresql+asyncpg://postgres.tywmyjecafmpufdfxbus:[PASSWORD]@aws-1-ca-central-1.pooler.supabase.com:6543/postgres
SYNC_DATABASE_URL=postgresql://postgres.tywmyjecafmpufdfxbus:[PASSWORD]@aws-1-ca-central-1.pooler.supabase.com:5432/postgres

# Supabase Platform Credentials
SUPABASE_URL=https://tywmyjecafmpufdfxbus.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_dSoVH6SAgzYJ7dWeo_drOg_UCcqNmuw
SUPABASE_SECRET_KEY=your_service_role_key_here

# Pipeline Controls
NEXT_PUBLIC_ASYNC_REPORTS=true
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Apply Database Migrations

Run the automated live migration runner script:

```bash
cd backend
python scripts/migrate_supabase.py
```

This deploys:
1. `supabase/migrations/0001_civicfix_init.sql` (PostGIS schema, RLS policies, RPCs, views, buckets)
2. `supabase/migrations/0002_compatibility_views.sql` (Legacy SQLAlchemy ORM compatibility columns & sync triggers)

### 3. Run Backend & Frontend

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

Visit **http://localhost:3000** for the application, and **http://localhost:8000/api/v1/docs** for the FastAPI Swagger documentation.

---

## 🧪 Testing & Verification

The codebase includes comprehensive test suites across both backend and database layers:

```bash
# 1. Run Python async report pipeline tests (8/8 passing in 0.12s)
cd backend
python -m pytest tests/api/test_async_reports.py -v

# 2. Run TypeScript strict type verification
cd ../frontend
npx tsc --noEmit

# 3. Compile Next.js production build (19/19 routes compiled cleanly)
npm run build
```

---

## 📄 License & Attribution

CivicFix is open-source software licensed under the **[MIT License](LICENSE)**.  
Designed for municipal governments, public works departments, and civic technology initiatives.
