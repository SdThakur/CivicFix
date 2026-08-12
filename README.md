# CivicFix — AI-Powered City Infrastructure Reporting & Operations Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg)](https://nextjs.org)
[![PostGIS](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20PostGIS-blue.svg)](https://postgis.net)

**CivicFix** is an end-to-end civic-tech platform that connects citizens directly to municipal infrastructure operations. Citizens upload photos of infrastructure hazards (potholes, broken streetlights, trash overflow, sidewalk damage). The platform automatically classifies issues using computer vision, reverse geocodes GPS coordinates, calculates transparent priority scores, detects duplicate reports, and routes issues to municipal crews.

---

## Architecture Diagram

```text
                         ┌───────────────┐
                         │    Citizen    │
                         └───────┬───────┘
                                 │
                                 ↓
                         ┌───────────────┐
                         │   Next.js 14  │
                         │   Frontend    │
                         └───────┬───────┘
                                 │
                                 ↓
                         ┌───────────────┐
                         │    FastAPI    │
                         │   REST API    │
                         └───────┬───────┘
                                 │
             ┌───────────────────┼───────────────────┐
             ↓                   ↓                   ↓
       PostgreSQL             Redis             MinIO (S3)
        + PostGIS                 │
             │              Celery Worker
             │                   │
             └───────────────────┼───────────────────┐
                                 ↓                   ↓
                           Gemini Vision     CLIP Embeddings
                                 │                   │
                                 └─────────┬─────────┘
                                           ↓
                                    Duplicate Engine
                                           │
                                           ↓
                                    Priority Engine
                                           │
                                           ↓
                                  Department Routing
                                           │
                                           ↓
                                   Work Order System
                                           │
                                           ↓
                                  Municipal Dashboard
```

---

## Key Features

### 1. Citizen Experience
- **Instant Photo Reporting**: Drag-and-drop or mobile camera upload.
- **Visual AI Progress Checklist**: Step-by-step indicator showing upload, classification, duplicate check, and priority scoring.
- **Interactive Leaflet Map**: Drag markers to adjust GPS locations with Nominatim reverse geocoding.
- **Resolution Verification Loop**: Citizens receive notification when repairs are completed and confirm if fixed.

### 2. Computer Vision Pipeline (Gemini 2.5 Vision)
- Abstracted `VisionAnalyzer` class supporting `GeminiVisionAnalyzer` (`gemini-2.5-flash`).
- Returns structured JSON: category, confidence, damage score, detected objects, and human review recommendation.

### 3. 4-Factor Duplicate Detection Algorithm
Avoids duplicate work orders when multiple citizens report the same issue using a weighted similarity score:

$$\text{Duplicate Score} = (0.45 \times \text{Location Similarity}) + (0.35 \times \text{Image Cosine Similarity}) + (0.10 \times \text{Category Match}) + (0.10 \times \text{Time Decay})$$

- **Location**: Haversine distance via PostGIS (`< 30 meters`).
- **Image**: Cosine similarity on 512-dimensional CLIP (`clip-ViT-B-32`) image embeddings.
- **Category**: Match matrix across categories.
- **Time**: Exponential decay over report window.

### 4. Transparent Multi-Factor Priority Scoring (0 - 100)
$$\text{Priority Score} = \text{Visual Damage} (30\%) + \text{Location Risk} (20\%) + \text{Infra Criticality} (20\%) + \text{Community Escalation} (15\%) + \text{Traffic Importance} (15\%)$$

### 5. Municipal Operations & 311 Service Request Center
- **311 Service Request Center**: Dispatch, track, and manage citizen requests with interactive 3-dot action menus, status logs, and SLA breach escalations.
- **Physical Inspection Scheduling**: Schedule inspector site visits (`+ Schedule Inspection`) and complete findings with safety risk ratings & area measurements.
- **Work Order Management**: Accept, start, add repair notes, upload before/after photos, and mark blocked dispatches.
- **Analytics & Spatial Hotspots**: Interactive Recharts graphs, DBSCAN spatial clustering, and predictive district risk scores.
- **AI Staff Assistant**: Natural language database querying with Gemini function calling.

---

## Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Leaflet, Recharts, Lucide Icons.
- **Backend**: Python 3.11/3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), GeoAlchemy2, PostGIS.
- **AI & ML**: Google Gemini 2.5 Flash Vision API, `sentence-transformers` CLIP, `scikit-learn` DBSCAN.
- **Background Worker**: Celery, Redis, Resend API for notification emails.
- **Storage**: MinIO / AWS S3 compatible storage with local fallback.

---

## Quick Start (Docker)

```bash
# 1. Clone repository & enter workspace
git clone https://github.com/SdThakur/CivicFix.git
cd CivicFix

# 2. Configure environment variables
cp backend/.env.example backend/.env

# 3. Start all services via Docker Compose
docker compose up --build
```

Access the applications:
- **Frontend App**: http://localhost:3000
- **FastAPI OpenAPI Docs**: http://localhost:8000/docs
- **MinIO Storage Console**: http://localhost:9001

---

## Testing

```bash
# Run backend pytest suite (unit + API + pipeline integration)
cd backend
pytest -v --cov=app
```

---

## License

MIT License. Copyright (c) 2026 Satya Thakur. Designed for municipal governments and civic technology standardizations.
