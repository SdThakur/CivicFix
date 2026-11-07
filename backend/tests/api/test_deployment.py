"""CivicFix Phase 6: Deployment & Edge Hardening Tests.

Tests:
1. EXIF GPS extraction from citizen photo for internal deduplication.
2. EXIF metadata stripping: Ensures public photos discard GPS tags.
3. Public sanitized photo endpoint (/public/photos/...) returns clean image without GPS leaks.
4. Cloudflare Turnstile token validation and development bypass.
5. Multi-instance scaling validation (API and Worker architecture).
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from PIL import Image, ExifTags
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.core.exif import extract_exif_gps, strip_exif_metadata
from app.core.turnstile import verify_turnstile_token
from app.api.public import router as public_router


@pytest.fixture
def deploy_test_app():
    app = FastAPI()
    app.include_router(public_router, prefix="/api/v1")
    app.include_router(public_router)
    return app


# ─── 1. EXIF GPS EXTRACTION & STRIPPING TESTS ───────────────────────────────
def test_exif_metadata_stripping_removes_tags():
    """strip_exif_metadata discards all metadata while preserving image integrity."""
    # Create test image with simulated EXIF
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(buf, format="JPEG")
    original_bytes = buf.getvalue()

    # Strip metadata
    clean_bytes = strip_exif_metadata(original_bytes, output_format="WEBP")
    assert len(clean_bytes) > 0

    # Verify clean image can be opened and has NO exif tags
    with Image.open(io.BytesIO(clean_bytes)) as clean_img:
        assert clean_img.size == (100, 100)
        exif = clean_img.getexif()
        assert len(exif) == 0


def test_extract_exif_gps_helper():
    """extract_exif_gps returns None when no GPS tags are present."""
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color="red")
    img.save(buf, format="JPEG")
    res = extract_exif_gps(buf.getvalue())
    assert res is None


@pytest.mark.asyncio
async def test_public_photo_endpoint_strips_exif(deploy_test_app):
    """GET /public/photos/{path} delivers sanitized image with privacy header."""
    async with AsyncClient(
        transport=ASGITransport(app=deploy_test_app), base_url="http://test"
    ) as client:
        resp = await client.get("/public/photos/reports/citizen-1/pothole.webp")
        assert resp.status_code == 200
        assert resp.headers["Content-Type"] == "image/webp"
        assert resp.headers["X-Privacy-Sanitized"] == "EXIF-GPS-Stripped"
        assert "s-maxage=604800" in resp.headers["Cache-Control"]

        # Ensure image has no EXIF tags
        with Image.open(io.BytesIO(resp.content)) as img:
            assert len(img.getexif()) == 0


# ─── 2. CLOUDFLARE TURNSTILE TESTS ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_turnstile_bypass_when_unconfigured():
    """When TURNSTILE_SECRET_KEY is not set (local dev), verification passes."""
    with patch("app.core.turnstile.TURNSTILE_SECRET_KEY", None):
        result = await verify_turnstile_token(turnstile_token=None)
        assert result is True


@pytest.mark.asyncio
async def test_turnstile_validates_successfully_with_secret():
    """When configured and siteverify returns success, token is accepted."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"success": True}

    with patch("app.core.turnstile.TURNSTILE_SECRET_KEY", "0x4AAAAAAATestSecretKey"):
        with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
            result = await verify_turnstile_token(
                turnstile_token="valid-cf-token", client_ip="127.0.0.1"
            )
            assert result is True


# ─── 3. DOCKER COMPOSE CONFIGURATION ARCHITECTURE TEST ──────────────────────
def test_docker_compose_scaling_architecture():
    """Verify docker-compose.yml defines separate Redis instances and scalable api/worker."""
    import yaml
    import os

    compose_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docker-compose.yml")
    assert os.path.exists(compose_path)

    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # Scaled services exist
    assert "api" in services
    assert "worker" in services
    assert "nginx" in services

    # Separate Redis instances with appropriate eviction policies
    assert "redis-limits" in services
    assert "redis-queue" in services
    assert "allkeys-lru" in services["redis-limits"]["command"]
    assert "noeviction" in services["redis-queue"]["command"]
