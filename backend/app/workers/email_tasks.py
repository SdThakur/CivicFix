"""Email notification background tasks using Resend API with mock fallback."""

import logging
import os
from typing import Any, Dict, Optional
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.email_tasks.send_email_notification", bind=True, max_retries=3, default_retry_delay=5)
def send_email_notification(
    self_or_to_email: Any,
    to_email_or_subject: Any = None,
    subject_or_html: Any = None,
    html_content: Optional[str] = None,
    text_content: Optional[str] = None,
    from_email: str = "CivicFix Notifications <notifications@civicfix.gov>",
) -> Dict[str, Any]:
    """Send transactional email via Resend API with graceful mock fallback."""
    # Disambiguate bind=True vs direct call arguments
    if isinstance(self_or_to_email, str):
        to_email = self_or_to_email
        subject = str(to_email_or_subject or "")
        html = str(subject_or_html or "")
        text = html_content
    else:
        to_email = str(to_email_or_subject)
        subject = str(subject_or_html or "")
        html = str(html_content or "")
        text = text_content

    resend_api_key = os.getenv("RESEND_API_KEY")

    if resend_api_key:
        try:
            import resend
            resend.api_key = resend_api_key

            params: Dict[str, Any] = {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
            if text:
                params["text"] = text

            response = resend.Emails.send(params)
            logger.info("Email successfully sent via Resend API to %s (ID: %s)", to_email, response.get("id"))
            return {
                "status": "sent",
                "to": to_email,
                "subject": subject,
                "resend_id": response.get("id"),
            }
        except Exception as exc:
            logger.error("Failed to send email via Resend API to %s: %s", to_email, exc)
            if hasattr(self_or_to_email, "retry"):
                raise self_or_to_email.retry(exc=exc)
            raise exc

    # Fallback log mode when RESEND_API_KEY is omitted or offline
    logger.info("[Mock Email Dispatch] To: %s | Subject: %s", to_email, subject)
    logger.debug("[Mock Email Body]\n%s", text or html)

    return {
        "status": "mock_sent",
        "to": to_email,
        "subject": subject,
        "note": "RESEND_API_KEY not configured. Email logged to console.",
    }


@celery_app.task(name="app.workers.email_tasks.send_report_received_email")
def send_report_received_email(
    user_email: str,
    report_id: str,
    issue_title: str,
    tracking_code: str,
) -> Dict[str, Any]:
    """Send confirmation email to citizen upon receiving their infrastructure report."""
    subject = f"Report Received: {issue_title} [{tracking_code}]"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <h2 style="color: #1a56db;">CivicFix Platform - Report Confirmation</h2>
        <p>Thank you for submitting a civic infrastructure report!</p>
        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 6px; margin: 15px 0;">
            <p><strong>Tracking Code:</strong> <span style="font-size: 1.2em; color: #111827; font-weight: bold;">{tracking_code}</span></p>
            <p><strong>Issue Title:</strong> {issue_title}</p>
            <p><strong>Report ID:</strong> {report_id}</p>
        </div>
        <p>Our automated AI pipeline and dispatch team have received your report and routed it to the responsible municipal department for inspection.</p>
        <p style="color: #6b7280; font-size: 0.85em;">You will receive real-time updates as work progresses on this issue.</p>
    </div>
    """

    text = f"""
    CivicFix Platform - Report Confirmation
    
    Thank you for submitting a civic infrastructure report!
    
    Tracking Code: {tracking_code}
    Issue Title: {issue_title}
    Report ID: {report_id}
    
    Our AI pipeline has analyzed your report and routed it to the responsible municipal department.
    """

    return send_email_notification(user_email, subject, html, text)


@celery_app.task(name="app.workers.email_tasks.send_issue_status_update_email")
def send_issue_status_update_email(
    user_email: str,
    issue_id: str,
    old_status: str,
    new_status: str,
    resolution_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Send notification email when an issue status changes (e.g. IN_PROGRESS, RESOLVED)."""
    subject = f"CivicFix Update: Issue {issue_id} is now {new_status}"

    notes_section = f"<p><strong>Resolution Notes:</strong> {resolution_notes}</p>" if resolution_notes else ""

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <h2 style="color: #1a56db;">CivicFix Issue Status Update</h2>
        <p>The status of reported issue <strong>{issue_id}</strong> has been updated.</p>
        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 6px; margin: 15px 0;">
            <p><strong>Previous Status:</strong> {old_status}</p>
            <p><strong>New Status:</strong> <span style="color: #059669; font-weight: bold;">{new_status}</span></p>
            {notes_section}
        </div>
        <p>Thank you for helping improve civic infrastructure in our community!</p>
    </div>
    """

    text = f"""
    CivicFix Issue Status Update
    
    Issue ID: {issue_id}
    Previous Status: {old_status}
    New Status: {new_status}
    {f'Resolution Notes: {resolution_notes}' if resolution_notes else ''}
    
    Thank you for helping improve civic infrastructure!
    """

    return send_email_notification(user_email, subject, html, text)


@celery_app.task(name="app.workers.email_tasks.send_department_assignment_email")
def send_department_assignment_email(
    department_email: str,
    issue_id: str,
    title: str,
    priority: str,
    location_address: str,
) -> Dict[str, Any]:
    """Send dispatch alert email to municipal department when a new issue is assigned."""
    subject = f"[{priority} PRIORITY] New Dispatch Assignment: Issue {issue_id}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <h2 style="color: #dc2626;">Municipal Dispatch Notification</h2>
        <p>A new civic issue has been automatically assigned to your department.</p>
        <div style="background-color: #fee2e2; padding: 15px; border-radius: 6px; margin: 15px 0;">
            <p><strong>Priority Level:</strong> <span style="color: #b91c1c; font-weight: bold;">{priority}</span></p>
            <p><strong>Issue ID:</strong> {issue_id}</p>
            <p><strong>Title:</strong> {title}</p>
            <p><strong>Location Address:</strong> {location_address}</p>
        </div>
        <p>Please log in to the CivicFix Staff Portal to view details and assign repair crews.</p>
    </div>
    """

    text = f"""
    Municipal Dispatch Notification
    
    Priority Level: {priority}
    Issue ID: {issue_id}
    Title: {title}
    Location: {location_address}
    
    Please log in to CivicFix Staff Portal for crew assignment.
    """

    return send_email_notification(department_email, subject, html, text)
