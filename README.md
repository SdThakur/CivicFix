<div align="center">

# 🏛️ CivicFix

### AI-Powered City Infrastructure Reporting & Operations Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Frontend-Next.js%2014-black?logo=next.js)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)

**CivicFix** connects citizens directly to municipal infrastructure operations. Citizens photograph hazards — potholes, broken streetlights, trash overflow, sidewalk damage — and the platform instantly classifies the issue with AI vision, deduplicates reports, scores priority transparently, and routes it to the right municipal crew.

[**Live Demo**](#quick-start-local) · [**API Docs**](http://localhost:8000/api/v1/docs) · [**Report an Issue**](https://github.com/SdThakur/CivicFix/issues)

</div>

---

## ✨ What Makes CivicFix Different

| Legacy 311 Systems | CivicFix |
|---|---|
| Manual photo review | 🤖 Gemini Vision auto-classifies in seconds |
| Duplicate reports pile up | 🔍 4-factor AI deduplication engine |
| Opaque prioritization | 📊 Transparent 5-factor scoring formula |
| Siloed department workflows | 🔗 Unified crew, SLA & dispatch platform |
| No spatial intelligence | 🗺️ DBSCAN spatial hotspot clustering |

---

## 🚀 Quick Start (Local)

### Prerequisites

- **Python 3.11+** and **Node.js 18+**
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/SdThakur/CivicFix.git
cd CivicFix
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # Edit .env to set GEMINI_API_KEY
python scripts/seed.py        # Initialize DB with demo data
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                   # Runs on http://localhost:3000
```

### Access

| Service | URL |
|---|---|
| **Frontend App** | http://localhost:3000 |
| **FastAPI Docs (Swagger)** | http://localhost:8000/api/v1/docs |
| **API Redoc** | http://localhost:8000/api/v1/redoc |

> **Note:** The backend uses SQLite by default for zero-config local dev. Switch to PostgreSQL + PostGIS in `.env` for production.

---

## 🐳 Quick Start (Docker)

```bash
# Clone repository
git clone https://github.com/SdThakur/CivicFix.git
cd CivicFix

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env — add your GEMINI_API_KEY

# Start all services (PostgreSQL + Redis + MinIO + Backend + Frontend)
docker compose up --build
```

| Service | URL |
|---|---|
| **Frontend** | http://localhost:3000 |
| **FastAPI Docs** | http://localhost:8000/api/v1/docs |
| **MinIO Console** | http://localhost:9001 |

---

## 🔐 Demo Accounts

All demo accounts use the password: **`password123`**

| Email | Role | Access |
|---|---|---|
| `admin@civicfix.gov` | **Admin** | Full platform access, user management |
| `manager@civicfix.gov` | **Manager** | Crew oversight, analytics, SLA management |
| `inspector@civicfix.gov` | **Inspector** | Site inspections, risk assessments |
| `worker@civicfix.gov` | **Field Worker** | Work orders, repair documentation |
| `citizen@civicfix.gov` | **Citizen** | Submit reports, track issue status |

---

## 🗺️ System Architecture

```
                         ┌───────────────┐
                         │    Citizen    │
                         └───────┬───────┘
                                 │  Photo Upload + GPS
                                 ↓
                         ┌───────────────┐
                         │   Next.js 14  │  TypeScript · Tailwind · Leaflet
                         │   Frontend    │
                         └───────┬───────┘
                                 │  REST API calls
                                 ↓
                         ┌───────────────┐
                         │    FastAPI    │  Python · Pydantic v2 · Async
                         │   REST API    │
                         └───────┬───────┘
                                 │
             ┌───────────────────┼───────────────────┐
             ↓                   ↓                   ↓
       PostgreSQL             Redis             MinIO / S3
        + PostGIS          (Task Broker)      (Media Storage)
             │                   │
             │            Celery Worker
             │                   │
             └───────────────────┼───────────────────┐
                                 ↓                   ↓
                           Gemini Vision       CLIP Embeddings
                           (2.5 Flash)        (clip-ViT-B-32)
                                 │                   │
                                 └─────────┬─────────┘
                                           ↓
                                    Duplicate Engine
                                    (4-Factor Score)
                                           │
                                           ↓
                                    Priority Engine
                                    (5-Factor Score)
                                           │
                                           ↓
                                  Department Routing
                                           │
                                           ↓
                                   Work Order System
                                           │
                                           ↓
                                  Municipal Dashboard
                               (Analytics · SLA · GIS)
```

---

## 🧠 Core AI Engines

### Computer Vision Pipeline

Each submitted photo is analyzed by **Gemini 2.5 Flash Vision**, returning:

- Issue category (pothole, streetlight, graffiti, etc.)
- Visual damage score (0–100)
- Confidence rating
- Detected objects
- Human review recommendation flag

### 4-Factor Duplicate Detection

Prevents duplicate work orders when multiple citizens report the same issue:

```
Duplicate Score = (0.45 × Location Similarity)
               + (0.35 × Image Cosine Similarity)
               + (0.10 × Category Match)
               + (0.10 × Time Decay)
```

| Factor | Weight | Method |
|---|---|---|
| **Location** | 45% | Haversine distance < 30m via PostGIS |
| **Image Similarity** | 35% | Cosine similarity on 512-dim CLIP embeddings |
| **Category Match** | 10% | Cross-category match matrix |
| **Time Decay** | 10% | Exponential decay over report window |

> If score ≥ 0.75, the report is linked to the existing issue — no duplicate work order is created.

### 5-Factor Priority Scoring (0–100)

```
Priority Score = Visual Damage        (30%)
               + Location Risk        (20%)
               + Infra Criticality    (20%)
               + Community Escalation (15%)
               + Traffic Importance   (15%)
```

Scores are shown to citizens **and** municipal staff — no black-box prioritization.

---

## 🏗️ Feature Overview

### 👤 Citizen Portal

- **Photo Reporting** — Drag-and-drop or mobile camera upload with EXIF GPS extraction
- **Interactive Map** — Leaflet map with draggable pin + Nominatim reverse geocoding
- **AI Progress Checklist** — Real-time step indicator: Upload → Classify → Deduplicate → Score → Route
- **Issue Tracking** — Live status updates from submission through resolution
- **Resolution Verification** — Citizens confirm repairs are complete, closing the feedback loop

### 🏛️ Municipal Operations Dashboard

- **311 Service Request Center** — Dispatch, filter, and manage citizen requests with SLA breach alerts
- **Work Order Management** — Accept, start, document, and close field repairs with before/after photos
- **Physical Inspection Scheduling** — Schedule site visits with safety risk ratings and area measurements
- **Crew Management** — Assign field crews, track availability and concurrent job limits
- **Equipment Tracking** — Asset registry with maintenance schedules
- **Intelligent Assignment Engine** — Skill-based crew-to-work-order matching

### 📊 Analytics & Intelligence

- **Recharts Dashboards** — KPIs, resolution trends, category breakdowns
- **Spatial Hotspot Clustering** — DBSCAN algorithm identifies recurring infrastructure problem zones
- **Predictive Risk Scoring** — District-level risk models for proactive maintenance
- **SLA Engine** — Configurable breach thresholds, escalation rules, and auto-notifications
- **GIS Layers** — Geospatial issue visualization overlaid on city maps
- **Public Transparency Portal** — Read-only public view of citywide issue statistics

### 🤖 AI Staff Assistant

- Natural language queries over the municipal database using **Gemini function calling**
- Example queries: *"How many open potholes in the north district?"*, *"Which crew has the most overdue work orders?"*

---

## 📁 Project Structure

```
CivicFix/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers (24 modules)
│   │   │   ├── auth.py           # JWT login/register
│   │   │   ├── reports.py        # Citizen report submission & tracking
│   │   │   ├── service_requests.py  # 311 dispatch center
│   │   │   ├── work_orders.py    # Field crew work orders
│   │   │   ├── inspections.py    # Physical site inspections
│   │   │   ├── crews.py          # Crew management
│   │   │   ├── analytics.py      # KPIs & dashboards
│   │   │   ├── gis.py            # Geospatial endpoints
│   │   │   ├── sla.py            # SLA rules & escalations
│   │   │   ├── ai_assistant.py   # Natural language queries
│   │   │   └── transparency.py   # Public portal API
│   │   ├── ai/               # Vision analyzer (Gemini + mock)
│   │   ├── core/             # Config, security, storage
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── repositories/     # Data access layer
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic layer
│   │   └── workers/          # Celery async task workers
│   ├── scripts/
│   │   └── seed.py           # Database seeding script
│   ├── tests/                # pytest test suite
│   ├── alembic/              # Database migration scripts
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── (auth)/       # Login page
│       │   ├── (citizen)/    # Citizen report portal
│       │   ├── (municipal)/  # Staff operations dashboard
│       │   └── dashboard/    # Role-based home dashboard
│       ├── components/       # Shared UI components
│       ├── lib/              # API client, utilities
│       └── types/            # TypeScript interfaces
├── docker-compose.yml
└── Makefile
```

---

## 🛠️ Technology Stack

### Frontend

| Technology | Purpose |
|---|---|
| Next.js 14 (App Router) | React framework with server components |
| TypeScript 5 | Type safety across the frontend |
| Tailwind CSS | Utility-first styling |
| Leaflet + React-Leaflet | Interactive map with GPS pin placement |
| Recharts | Analytics charts and KPI visualizations |
| Lucide Icons | Consistent icon system |

### Backend

| Technology | Purpose |
|---|---|
| FastAPI | Async REST API framework |
| Pydantic v2 | Request/response validation |
| SQLAlchemy 2.0 (async) | ORM with async session support |
| GeoAlchemy2 | PostGIS geospatial column types |
| Alembic | Database schema migrations |
| PyJWT + bcrypt | JWT auth with SHA-256 pre-hashing |

### AI & Data

| Technology | Purpose |
|---|---|
| Google Gemini 2.5 Flash | Computer vision classification |
| sentence-transformers CLIP | 512-dim image embedding generation |
| scikit-learn DBSCAN | Spatial hotspot clustering |
| PostGIS | Haversine distance queries |

### Infrastructure

| Technology | Purpose |
|---|---|
| PostgreSQL + PostGIS | Primary geospatial database |
| SQLite (default local) | Zero-config local development |
| Redis | Celery task broker & result backend |
| Celery | Async AI processing pipeline |
| MinIO / AWS S3 | Photo & media storage |
| Resend API | Transactional notification emails |

---

## 🧪 Testing

```bash
cd backend

# Run full test suite with coverage report
pytest -v --cov=app

# Run specific test modules
pytest tests/test_auth.py -v
pytest tests/test_reports.py -v
```

---

## 🚢 Production Deployment

1. **Configure environment** — Set `DATABASE_URL` (PostgreSQL + PostGIS), strong `SECRET_KEY`, `GEMINI_API_KEY`, and `RESEND_API_KEY` in `backend/.env`
2. **Run migrations** — `alembic upgrade head`
3. **Seed database** — `python scripts/seed.py`
4. **Set CORS** — Restrict `CORS_ORIGINS` to your municipal domain
5. **Reverse proxy** — Nginx or Traefik with TLS/SSL termination
6. **Orchestration** — Docker Compose (small deployments) or Kubernetes (scale)

---

## 🔮 Roadmap

- [ ] **PWA / Mobile App** — Offline-first image capture with background sync
- [ ] **ArcGIS / QGIS Integration** — Live municipal GIS layer overlays
- [ ] **ML Retraining Pipeline** — Continuous fine-tuning on resolved case history
- [ ] **Multi-Jurisdiction Support** — Multi-tenant architecture for county-wide deployment
- [ ] **SMS / Push Notifications** — Twilio integration for mobile status alerts
- [ ] **Accessibility Audit** — WCAG 2.1 AA compliance pass

---

## 📄 License

MIT License © 2026 [Satya Thakur](https://github.com/SdThakur)

<img width="10164" height="8567" alt="diagram" src="https://github.com/user-attachments/assets/d427d351-bd16-435c-8d18-926671ff0ac2" />


Designed for municipal governments and civic technology modernization initiatives.
