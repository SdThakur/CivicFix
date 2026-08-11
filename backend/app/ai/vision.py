"""Vision analysis module using Google Gemini Vision API with mock fallback."""

from abc import ABC, abstractmethod
import asyncio
import base64
import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class VisionAnalysisResult(BaseModel):
    """Structured result from computer vision analysis of civic infrastructure images."""

    category: str = Field(..., description="Detected category, e.g., Pothole, Streetlight, Water Leak")
    severity_score: float = Field(..., ge=0.0, le=10.0, description="Severity rating from 0 (minor) to 10 (critical)")
    visual_damage_score: float = Field(..., ge=0.0, le=1.0, description="Normalized visual damage factor from 0.0 to 1.0")
    title: str = Field(..., description="Short descriptive title of the issue")
    description: str = Field(..., description="Detailed technical description of visible damage")
    safety_hazard: bool = Field(False, description="True if issue poses an immediate public safety hazard")
    estimated_cost_level: str = Field("MEDIUM", description="Estimated repair cost level: LOW, MEDIUM, HIGH, CRITICAL")
    tags: List[str] = Field(default_factory=list, description="Keywords / tags describing the issue")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw response payload if available")

    model_config = {
        "extra": "ignore",
    }


class VisionAnalyzer(ABC):
    """Abstract base class for vision analyzer implementations."""

    @abstractmethod
    async def analyze_image(
        self, image_data: Union[bytes, str], prompt_context: Optional[str] = None
    ) -> VisionAnalysisResult:
        """Analyze an image asynchronously and return structured issue analysis.

        Args:
            image_data: Raw byte content, base64 string, or image file path.
            prompt_context: Optional additional context (e.g. citizen notes).
        """
        pass

    def analyze_image_sync(
        self, image_data: Union[bytes, str], prompt_context: Optional[str] = None
    ) -> VisionAnalysisResult:
        """Synchronous wrapper around analyze_image for Celery worker tasks."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If running inside existing loop, create new event loop in runner context
            import nest_asyncio  # type: ignore # noqa
            nest_asyncio.apply()
            return loop.run_until_complete(self.analyze_image(image_data, prompt_context))
        else:
            return loop.run_until_complete(self.analyze_image(image_data, prompt_context))


class MockVisionAnalyzer(VisionAnalyzer):
    """Deterministic mock vision analyzer for offline development and testing."""

    CATEGORIES = [
        ("Pothole", "Severe road pavement degradation with exposed aggregate", 0.75, 7.5, True, "MEDIUM", ["road", "asphalt", "pothole"]),
        ("Water Leak", "Pressurized water gusher from subsurface main leak", 0.85, 8.5, True, "HIGH", ["water", "pipe", "flooding"]),
        ("Streetlight Failure", "Non-functional streetlight fixture causing darkness", 0.40, 4.0, False, "LOW", ["lighting", "electrical", "darkness"]),
        ("Illegal Dumping", "Accumulated construction debris blocking public right-of-way", 0.60, 6.0, False, "MEDIUM", ["garbage", "waste", "sanitation"]),
        ("Damaged Traffic Sign", "Stop sign bent at 45 degree angle obscured from drivers", 0.70, 7.0, True, "LOW", ["traffic", "sign", "safety"]),
        ("Traffic Signal Fault", "Traffic signal light unpowered at busy intersection", 0.95, 9.5, True, "CRITICAL", ["traffic_signal", "intersection", "hazard"]),
        ("Fallen Tree Branch", "Large tree limb obstructing vehicle travel lane", 0.65, 6.5, True, "MEDIUM", ["tree", "obstruction", "parks"]),
        ("Sidewalk Crack", "Uneven concrete slab uplift causing tripping hazard", 0.50, 5.0, False, "LOW", ["sidewalk", "concrete", "pedestrian"]),
    ]

    async def analyze_image(
        self, image_data: Union[bytes, str], prompt_context: Optional[str] = None
    ) -> VisionAnalysisResult:
        """Generate realistic mock analysis based on deterministic hash of input."""
        if isinstance(image_data, str):
            image_bytes = image_data.encode("utf-8")
        else:
            image_bytes = image_data

        # Hash input bytes to pick a consistent category for mock testing
        digest = int(hashlib.md5(image_bytes).hexdigest(), 16)
        cat_tuple = self.CATEGORIES[digest % len(self.CATEGORIES)]

        category, desc, damage_score, severity, hazard, cost_level, tags = cat_tuple

        title = f"{category} Reported"
        if prompt_context:
            title = f"{category} - {prompt_context[:30]}"

        return VisionAnalysisResult(
            category=category,
            severity_score=severity,
            visual_damage_score=damage_score,
            title=title,
            description=f"[Mock AI] {desc}. Citizen notes: {prompt_context or 'None provided.'}",
            safety_hazard=hazard,
            estimated_cost_level=cost_level,
            tags=tags,
            confidence=0.92,
            raw_response={"mock": True, "hash_digest": digest},
        )


class GeminiVisionAnalyzer(VisionAnalyzer):
    """Google Gemini AI implementation for civic infrastructure vision analysis."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        from app.core.config import settings
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.mock_fallback = MockVisionAnalyzer()

    async def analyze_image(
        self, image_data: Union[bytes, str], prompt_context: Optional[str] = None
    ) -> VisionAnalysisResult:
        """Analyze image using Gemini 2.5 REST API with automatic mock fallback on error."""
        if not self.api_key:
            return await self.mock_fallback.analyze_image(image_data, prompt_context)

        try:
            # Prepare base64 image data
            mime_type = "image/jpeg"
            if isinstance(image_data, bytes):
                raw_bytes = image_data
            elif isinstance(image_data, str) and image_data.startswith("data:image"):
                header, encoded = image_data.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]
                raw_bytes = base64.b64decode(encoded)
            elif isinstance(image_data, str) and os.path.exists(image_data):
                with open(image_data, "rb") as f:
                    raw_bytes = f.read()
            else:
                raw_bytes = base64.b64decode(image_data) if isinstance(image_data, str) else image_data

            b64_str = base64.b64encode(raw_bytes).decode("utf-8")

            system_prompt = (
                "You are an expert civic infrastructure inspection AI for municipal public works. "
                "Analyze the provided image of reported urban infrastructure damage or issue. "
                "Respond ONLY with a valid JSON object matching this exact schema:\n"
                "{\n"
                '  "category": "<Pothole|Water Leak|Streetlight Failure|Illegal Dumping|Damaged Traffic Sign|Traffic Signal Fault|Fallen Tree Branch|Sidewalk Crack|Other>",\n'
                '  "severity_score": <float 0.0 to 10.0>,\n'
                '  "visual_damage_score": <float 0.0 to 1.0>,\n'
                '  "title": "<short descriptive title>",\n'
                '  "description": "<technical damage assessment description>",\n'
                '  "safety_hazard": <true|false>,\n'
                '  "estimated_cost_level": "<LOW|MEDIUM|HIGH|CRITICAL>",\n'
                '  "tags": ["tag1", "tag2"],\n'
                '  "confidence": <float 0.0 to 1.0>\n'
                "}\n"
            )
            if prompt_context:
                system_prompt += f"\nCitizen report context: {prompt_context}"

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": system_prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": b64_str,
                                }
                            },
                        ]
                    }
                ]
            }

            # REST call to Google Generative Language API
            import urllib.request

            models_to_try = [self.model_name, "gemini-flash-latest", "gemini-2.0-flash"]
            last_err = None

            for m in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.api_key}"
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )

                try:
                    def _call_api():
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            return json.loads(resp.read().decode("utf-8"))

                    data = await asyncio.to_thread(_call_api)
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

                    # Clean markdown code blocks ```json ... ```
                    if raw_text.startswith("```"):
                        lines = raw_text.splitlines()
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        raw_text = "\n".join(lines).strip()

                    parsed = json.loads(raw_text)
                    parsed["raw_response"] = {"model": m, "raw_text": raw_text}
                    return VisionAnalysisResult(**parsed)

                except Exception as err:
                    last_err = err
                    logger.warning("Gemini REST model %s failed: %s", m, err)
                    continue

            raise last_err or RuntimeError("All Gemini Vision models failed")

        except Exception as err:
            logger.error("Gemini Vision API call failed: %s. Falling back to Mock analyzer.", err)
            return await self.mock_fallback.analyze_image(image_data, prompt_context)


def get_vision_analyzer(api_key: Optional[str] = None) -> VisionAnalyzer:
    """Factory function returning GeminiVisionAnalyzer if API key available, else MockVisionAnalyzer."""
    from app.core.config import settings
    effective_key = api_key or getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
    if effective_key:
        return GeminiVisionAnalyzer(api_key=effective_key)
    return MockVisionAnalyzer()
