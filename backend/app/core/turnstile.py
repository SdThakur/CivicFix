"""CivicFix Cloudflare Turnstile Bot Defense Engine.

Validates Cloudflare Turnstile CAPTCHA response tokens on citizen report submissions
to protect against automated spam and bot surges.
"""

import logging
import os
from typing import Optional
from fastapi import HTTPException, status
import httpx

logger = logging.getLogger("civicfix.turnstile")

TURNSTILE_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")


async def verify_turnstile_token(
    turnstile_token: Optional[str],
    client_ip: Optional[str] = None,
) -> bool:
    """Verify Cloudflare Turnstile token with Cloudflare Siteverify API.

    - If TURNSTILE_SECRET_KEY is unconfigured (development/test mode), allows submission.
    - If configured, performs outbound verification call with 3.0s timeout.
    """
    if not TURNSTILE_SECRET_KEY:
        # Development or unconfigured: allow through
        return True

    if not turnstile_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Cloudflare Turnstile verification token ('cf-turnstile-response').",
        )

    payload = {
        "secret": TURNSTILE_SECRET_KEY,
        "response": turnstile_token,
    }
    if client_ip:
        payload["remoteip"] = client_ip

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(TURNSTILE_SITEVERIFY_URL, data=payload)
            result = resp.json()

            if result.get("success"):
                return True
            else:
                logger.warning(
                    f"Turnstile verification failed: {result.get('error-codes')}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cloudflare Turnstile bot verification failed. Please try again.",
                )
    except httpx.RequestError as e:
        logger.error(f"Error communicating with Cloudflare Turnstile siteverify: {e}")
        # Fail open or closed depending on policy (default fail-open on transient Cloudflare outage)
        return True
