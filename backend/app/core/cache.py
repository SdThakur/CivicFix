"""CivicFix Caching & Viewport Quantization Engine.

Provides:
- snap_bounds: Snaps bounding box coordinates to discrete grid per zoom level.
- cached_json: Redis-backed JSON caching with CDN Cache-Control headers (s-maxage, stale-while-revalidate).
- Strict Authorization bypass: Requests containing Authorization headers are NEVER cached.
"""

import json
import logging
import math
from typing import Any, Callable, Coroutine, Dict, Optional, Tuple
from fastapi import Request, Response
from app.core.config import settings

logger = logging.getLogger("civicfix.cache")


def get_zoom_step(zoom: int) -> float:
    """Return grid snapping step in degrees based on map zoom level."""
    if zoom <= 8:
        return 0.05       # ~5.5 km grid
    elif zoom <= 11:
        return 0.01       # ~1.1 km grid
    elif zoom <= 14:
        return 0.002      # ~220 m grid
    else:
        return 0.0005     # ~55 m grid


def snap_bounds(
    min_lat: float,
    max_lat: float,
    min_lng: float,
    max_lng: float,
    zoom: int,
) -> Tuple[float, float, float, float]:
    """Snap viewport bounding box coordinates to a discrete grid based on zoom.

    Quantizing viewport coordinates ensures that multiple concurrent users panning
    in the same geographic neighborhood hit the exact same Redis & CDN cache keys.
    """
    step = get_zoom_step(zoom)
    snapped_min_lat = round(math.floor(min_lat / step) * step, 6)
    snapped_max_lat = round(math.ceil(max_lat / step) * step, 6)
    snapped_min_lng = round(math.floor(min_lng / step) * step, 6)
    snapped_max_lng = round(math.ceil(max_lng / step) * step, 6)

    return snapped_min_lat, snapped_max_lat, snapped_min_lng, snapped_max_lng


def build_cdn_cache_control(ttl_seconds: int, is_authenticated: bool = False) -> str:
    """Construct Cache-Control header with s-maxage and stale-while-revalidate.

    - Public unauthenticated responses: Cached by CDNs/browsers with graceful stale revalidation.
    - Authenticated responses: Strictly private and uncacheable.
    """
    if is_authenticated:
        return "private, no-cache, no-store, must-revalidate"
    
    max_age = min(15, ttl_seconds)
    stale_revalidate = max(60, ttl_seconds * 2)
    return f"public, max-age={max_age}, s-maxage={ttl_seconds}, stale-while-revalidate={stale_revalidate}"


async def cached_json(
    cache_key: str,
    ttl_seconds: int,
    request: Request,
    fetch_coroutine: Callable[[], Coroutine[Any, Any, Any]],
) -> Response:
    """Return cached JSON from Redis or compute and store it with CDN headers.

    Rules:
    1. NEVER cache anything with an Authorization header (bypasses cache read/write).
    2. Add Cache-Control s-maxage and stale-while-revalidate for CDN micro-caching.
    3. Return X-Cache header (HIT, MISS, or BYPASS).
    """
    # 1. Check for Authorization header -> Strict Cache Bypass
    auth_header = request.headers.get("authorization")
    if auth_header:
        data = await fetch_coroutine()
        json_str = json.dumps(data, default=str)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={
                "Cache-Control": build_cdn_cache_control(ttl_seconds, is_authenticated=True),
                "X-Cache": "BYPASS",
                "Vary": "Accept-Encoding, Authorization",
            },
        )

    # 2. Retrieve Redis client from app.state (or limiter)
    redis_client = getattr(request.app.state, "redis_cache", None)
    if redis_client is None:
        limiter = getattr(request.app.state, "limiter", None)
        if limiter and hasattr(limiter, "redis"):
            redis_client = limiter.redis

    # 3. If Redis client available, check cache for existing serialized JSON
    if redis_client:
        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data is not None:
                if isinstance(cached_data, bytes):
                    cached_data = cached_data.decode("utf-8")
                return Response(
                    content=cached_data,
                    media_type="application/json",
                    headers={
                        "Cache-Control": build_cdn_cache_control(ttl_seconds, is_authenticated=False),
                        "X-Cache": "HIT",
                        "X-Cache-Key": cache_key,
                        "Vary": "Accept-Encoding, Authorization",
                    },
                )
        except Exception as e:
            logger.warning(f"Cache lookup failed for {cache_key}: {e}")

    # 4. Cache MISS: compute data
    data = await fetch_coroutine()
    json_str = json.dumps(data, default=str)

    # 5. Store serialized data in Redis
    if redis_client:
        try:
            await redis_client.setex(cache_key, ttl_seconds, json_str)
        except Exception as e:
            logger.warning(f"Cache write failed for {cache_key}: {e}")

    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Cache-Control": build_cdn_cache_control(ttl_seconds, is_authenticated=False),
            "X-Cache": "MISS",
            "X-Cache-Key": cache_key,
            "Vary": "Accept-Encoding, Authorization",
        },
    )
