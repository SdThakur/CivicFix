# CivicFix Production Service Level Objectives (SLOs)

Operational reliability and performance contracts for the CivicFix infrastructure:

---

## 1. Public Read Latency SLO
- **Target**: **$p95 < 50\text{ ms}$**
- **Scope**: All public map viewport queries (`/public/map`, `/api/v1/public/map`) and transparency stats (`/public/stats`).
- **Enforcement**: Powered by `snap_bounds()` bounding box quantization and edge Nginx + Redis micro-caching (TTL 15–30s).
- **PromQL Sli**:
  ```promql
  histogram_quantile(
    0.95,
    sum(rate(civicfix_http_request_duration_seconds_bucket{route=~".*/public/.*"}[5m])) by (le)
  ) < 0.05
  ```

---

## 2. Ingestion Submission Latency SLO
- **Target**: **$p95 < 200\text{ ms}$**
- **Scope**: Citizen asynchronous report submission (`POST /api/v1/reports`).
- **Enforcement**: Immediate `HTTP 202 Accepted` return with durable ARQ queue producer decoupling (`enqueue_report()`).
- **PromQL Sli**:
  ```promql
  histogram_quantile(
    0.95,
    sum(rate(civicfix_http_request_duration_seconds_bucket{route="/api/v1/reports",method="POST"}[5m])) by (le)
  ) < 0.20
  ```

---

## 3. Queue-to-Processed Latency SLO
- **Target**: **$p99 < 10\text{ seconds}$**
- **Scope**: Total duration from when a report is enqueued to when AI vision triage and 100m spatial deduplication are completed.
- **Enforcement**: Dedicated ARQ worker replicas with distributed concurrency semaphore (`acquire_global_gemini_slot`).
- **PromQL Sli**:
  ```promql
  histogram_quantile(
    0.99,
    sum(rate(civicfix_queue_job_latency_seconds_bucket[5m])) by (le)
  ) < 10.0
  ```

---

## 4. Availability & Error Budget
- **Target**: **$\ge 99.9\%$ Success Rate**
- **Scope**: Ratio of successful non-5xx HTTP responses over rolling 30-day window.
- **PromQL Sli**:
  ```promql
  (
    sum(rate(civicfix_http_requests_total{status_code!~"5.."}[30d]))
    /
    sum(rate(civicfix_http_requests_total[30d]))
  ) >= 0.999
  ```

