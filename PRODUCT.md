# Product

## Platform

web

## Users

1. **Citizens**: Everyday residents reporting local hazards (potholes, streetlights, overflowing trash, damaged sidewalks, fallen trees, vandalism) from mobile web browsers or desktop, seeking fast, transparent progress updates.
2. **Municipal Dispatchers & Operations Supervisors**: Public works coordinators triaging tickets, monitoring citywide geographic clusters, reviewing duplicate merges, and assigning field crews with SLA targets.
3. **Field Crew Workers & Inspectors**: Municipal crews viewing mobile route work orders, performing on-site repairs, and submitting verified resolution evidence ("after" photos).

## Product Purpose

CivicFix bridges the gap between citizens and municipal infrastructure operations. It eliminates the black hole of traditional 311 systems by automatically classifying civic hazards with computer vision, deduplicating repetitive reports, calculating transparent priority scores, and routing issues directly to work crews for rapid resolution.

## Positioning

Unlike opaque municipal 311 hotlines and ticketing forms where reports disappear without feedback, CivicFix provides an end-to-end transparent loop: 4-factor automated deduplication, open 5-factor priority formula (no political favoritism), AI vision verification, and photo-proven resolution tracking.

## Operating Context

- **Citizen submission**: Often outdoors, on mobile devices, under varying sunlight, snapping photos with quick geolocation.
- **Municipal dispatch**: High-density desktop dashboards with live geospatial maps, work queues, crew rosters, and incident metrics.
- **Field crew execution**: Tablet or phone in municipal trucks or worksites checking queue items and snapping resolution photos.

## Capabilities and Constraints

- **Capabilities**:
  - Hazard reporting with photo upload, EXIF GPS extraction, and interactive Leaflet map reverse geocoding.
  - AI classification with Gemini Flash Vision (hazard category, visual damage intensity 0-100).
  - 4-factor AI duplicate detection algorithm (< 30m distance + CLIP visual embeddings + category + time decay).
  - Transparent 5-factor priority scoring (Visual damage 30%, Location risk 20%, Criticality 20%, Community escalation 15%, Traffic 15%).
  - Role-based workflows: Citizen, Field Worker, Inspector, Dispatcher/Admin.
  - Interactive map with DBSCAN cluster hotspots, public transparency analytics, AI natural language assistant.
- **Constraints**:
  - Web only: Next.js 14 App Router, React 18, TypeScript, Tailwind CSS.
  - Do not modify backend API contracts, routes, business logic, or data models.
  - Dark and light theme support required via CSS custom properties and design tokens; no hardcoded hex colors.
  - Performance: Mid-range mobile 60fps; limit active backdrop-filter layers; touch targets minimum 44px.

## Brand Commitments

- **Name**: CivicFix.
- **Voice**: Objective, dependable, transparent, modern civic utility.
- **Tone**: Professional municipal infrastructure control meets effortless citizen convenience. Avoid sci-fi gaming jargon ("Mission Control Ops", neon lasers) and generic AI-slop (purple-blue glow gradients everywhere).

## Evidence on Hand

- Complete running Next.js 14 frontend with full App Router tree (`/(citizen)`, `/(municipal)`, `/map`, `/transparency`).
- Complete FastAPI backend with database models, seed script, Gemini vision integration, and live API endpoints.
- Real domain data models: Reports, Work Orders, Crews, Inspections, Assets, Analytics (`frontend/src/types/index.ts`, `frontend/src/lib/api.ts`).

## Product Principles

1. **Clear Division of Layers**: The interface strictly separates floating control chrome (translucent glass) from primary content and operational data (solid, readable surfaces).
2. **Civic Transparency by Default**: Every score, status transition, and routing decision is explainable and visible to citizens and city operators alike.
3. **Accessibility Without Compromise**: High-contrast legibility in direct sunlight or dark mode; solid fallbacks for reduced-transparency and reduced-motion preferences.
4. **Purpose-Driven Utility**: Avoid decorative clutter; elevate the photographic evidence, spatial map, and action triage.

## Accessibility & Inclusion

- WCAG 2.1 AA contrast compliance across all text and controls over light, dark, and image backgrounds.
- High-contrast and solid fallbacks for `prefers-reduced-transparency`, `prefers-contrast`, and `prefers-reduced-motion`.
- Minimum 44x44px touch target sizes for all interactive elements.
- User-selectable translucency level (Clear / Regular / Frosted).

