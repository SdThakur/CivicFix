"""Asynchronous Celery background tasks for report processing, AI analysis, geospatial routing, and duplicate merging."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.core.instrumentation import PipelineTimer

from app.ai.department_routing import DepartmentRouter
from app.ai.duplicate_detection import DuplicateDetector
from app.ai.embeddings import ImageEmbedder
from app.ai.priority import PriorityEngine
from app.ai.vision import get_vision_analyzer
from app.geospatial.geocoding import get_geocoder
from app.geospatial.hotspot_detection import HotspotDetector
from app.workers.celery_app import celery_app
from app.workers.email_tasks import send_department_assignment_email, send_report_received_email

logger = logging.getLogger(__name__)

# Singletons for memory efficiency inside worker processes
_embedder = ImageEmbedder()
_priority_engine = PriorityEngine()
_duplicate_detector = DuplicateDetector(embedder=_embedder)
_department_router = DepartmentRouter()
_hotspot_detector = HotspotDetector()


@celery_app.task(name="app.workers.tasks.process_report_task", bind=True, max_retries=3, default_retry_delay=10)
def process_report_task(
    self_or_report_id: Any,
    report_id_or_data: Any = None,
    report_data_or_existing: Any = None,
    existing_issues: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Execute complete async pipeline for incoming citizen infrastructure report.

    Supports both Celery bound task invocation (self, report_id, report_data, ...)
    and direct function call (report_id, report_data, ...).
    """
    # Disambiguate arguments whether called as bound Celery task or direct function
    if isinstance(self_or_report_id, str):
        report_id = self_or_report_id
        report_data = report_data_or_existing if isinstance(report_data_or_existing, dict) else (report_id_or_data or {})
        existing = existing_issues
    else:
        # Bound Celery task where first arg is self
        report_id = str(report_id_or_data)
        report_data = report_data_or_existing or {}
        existing = existing_issues

    logger.info("Starting background processing for Report ID: %s", report_id)

    try:
        # Extract basic fields
        lat = float(report_data.get("latitude") or report_data.get("lat") or 0.0)
        lon = float(report_data.get("longitude") or report_data.get("lon") or 0.0)
        image_input = report_data.get("image_bytes") or report_data.get("image_url") or report_data.get("image_base64") or b"mock_img"
        user_notes = report_data.get("description") or report_data.get("notes") or ""
        user_email = report_data.get("user_email") or report_data.get("reporter_email")
        tracking_code = report_data.get("tracking_code") or f"TRK-{report_id[:8].upper()}"

        with PipelineTimer("process_report") as timer:
            # ----------------------------------------------------
            # Step 1: Vision Analysis
            # ----------------------------------------------------
            with timer.step("vision_analysis"):
                vision_analyzer = get_vision_analyzer()
                vision_result = vision_analyzer.analyze_image_sync(image_input, prompt_context=user_notes)
            logger.info("Vision analysis completed for %s: Category=%s, Severity=%.1f", report_id, vision_result.category, vision_result.severity_score)

            # ----------------------------------------------------
            # Step 2: Image Embedding
            # ----------------------------------------------------
            with timer.step("clip_embedding"):
                embedding = _embedder.generate_embedding(image_input)

            # ----------------------------------------------------
            # Step 3: Reverse Geocoding
            # ----------------------------------------------------
            with timer.step("reverse_geocoding"):
                geocoder = get_geocoder()
                geo_result = geocoder.reverse_geocode_sync(lat, lon)
            address_str = geo_result.get("formatted_address", "Unknown Address")

            # Prepare normalized report dictionary for duplicate comparison
            normalized_report = {
                "id": report_id,
                "latitude": lat,
                "longitude": lon,
                "category": vision_result.category,
                "image_embedding": embedding,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "address": address_str,
                "description": user_notes,
            }

            # ----------------------------------------------------
            # Step 4: Duplicate Detection
            # ----------------------------------------------------
            with timer.step("duplicate_detection"):
                duplicates = []
                if existing:
                    duplicates = _duplicate_detector.find_duplicates(normalized_report, existing, threshold=0.75)

            # ----------------------------------------------------
            # Step 5: Department Routing
            # ----------------------------------------------------
            with timer.step("department_routing"):
                routing_info = _department_router.route_category(
                    category=vision_result.category,
                    description=vision_result.description,
                    tags=vision_result.tags,
                )

            # ----------------------------------------------------
            # Step 6: Decision - Merge into Duplicate vs Create New Issue
            # ----------------------------------------------------
            with timer.step("priority_scoring"):
                if duplicates:
                    best_match = duplicates[0]
                    existing_issue_id = best_match["issue_id"]
                    existing_issue = best_match["issue_data"]
                    current_count = int(existing_issue.get("report_count", 1)) + 1

                    # Recalculate updated priority score with escalated report count
                    updated_priority = _priority_engine.calculate_priority(
                        visual_damage_score=vision_result.visual_damage_score,
                        location_risk=existing_issue.get("location_risk", 0.5),
                        infrastructure_type=vision_result.category,
                        report_count=current_count,
                        traffic_importance=existing_issue.get("traffic_importance", 0.5),
                        safety_hazard=vision_result.safety_hazard,
                    )
                else:
                    new_issue_id = f"ISSUE-{uuid.uuid4().hex[:10].upper()}"
                    priority_result = _priority_engine.calculate_priority(
                        visual_damage_score=vision_result.visual_damage_score,
                        location_risk=0.50,  # Default moderate location risk
                        infrastructure_type=vision_result.category,
                        report_count=1,
                        traffic_importance=0.50,
                        safety_hazard=vision_result.safety_hazard,
                    )

        # Capture timing report after the pipeline exits
        timing_report = timer.report()
        timing_payload = timing_report.as_dict()

        # ----------------------------------------------------
        # Assemble final result with embedded timing data
        # ----------------------------------------------------
        if duplicates:
            result_summary = {
                "status": "merged",
                "action": "merged_into_existing_issue",
                "report_id": report_id,
                "merged_into_issue_id": existing_issue_id,
                "similarity_score": best_match["similarity_score"],
                "updated_report_count": current_count,
                "updated_priority": updated_priority,
                "vision_analysis": vision_result.model_dump(),
                "geocoding": geo_result,
                "routing": routing_info,
                "timing_ms": timing_payload,
            }
            logger.info("Report %s merged into existing Issue %s (Similarity: %.2f)", report_id, existing_issue_id, best_match["similarity_score"])
        else:
            result_summary = {
                "status": "created_issue",
                "action": "created_new_issue",
                "report_id": report_id,
                "issue_id": new_issue_id,
                "title": vision_result.title,
                "description": vision_result.description,
                "category": vision_result.category,
                "severity_score": vision_result.severity_score,
                "priority": priority_result,
                "routing": routing_info,
                "geocoding": geo_result,
                "vision_analysis": vision_result.model_dump(),
                "embedding_dim": len(embedding),
                "tracking_code": tracking_code,
                "timing_ms": timing_payload,
            }
            logger.info("Created new Issue %s for Report %s. Assigned to %s", new_issue_id, report_id, routing_info["department_name"])

            # Send email to department dispatch
            send_department_assignment_email.delay(
                department_email=routing_info["contact_email"],
                issue_id=new_issue_id,
                title=vision_result.title,
                priority=priority_result["priority_level"],
                location_address=address_str,
            )

        # ----------------------------------------------------
        # Step 7: Send confirmation email to reporting citizen
        # ----------------------------------------------------
        if user_email:
            send_report_received_email.delay(
                user_email=user_email,
                report_id=report_id,
                issue_title=vision_result.title,
                tracking_code=tracking_code,
            )

        return result_summary

    except Exception as exc:
        logger.error("Error executing process_report_task for %s: %s", report_id, exc, exc_info=True)
        if hasattr(self_or_report_id, "retry"):
            raise self_or_report_id.retry(exc=exc)
        raise exc


@celery_app.task(name="app.workers.tasks.run_hotspot_detection_task")
def run_hotspot_detection_task(
    points: List[Dict[str, Any]],
    eps_km: float = 0.5,
    min_samples: int = 3,
) -> Dict[str, Any]:
    """Asynchronously execute DBSCAN spatial clustering over active issue coordinates."""
    logger.info("Executing hotspot detection task over %d issue points...", len(points))
    results = _hotspot_detector.detect_hotspots(points, eps_km=eps_km, min_samples=min_samples)
    logger.info("Hotspot detection complete: Identified %d clusters.", results["total_clusters"])
    return results


@celery_app.task(name="app.workers.tasks.batch_process_reports_task")
def batch_process_reports_task(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process a batch of citizen infrastructure reports asynchronously."""
    processed_count = 0
    results = []
    for report in reports:
        report_id = str(report.get("id") or report.get("report_id") or uuid.uuid4())
        res = process_report_task.delay(report_id, report)
        results.append({"report_id": report_id, "task_id": getattr(res, "id", "mock_id")})
        processed_count += 1

    return {"total_queued": processed_count, "tasks": results}
