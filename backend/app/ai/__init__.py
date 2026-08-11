"""AI module — exports for vision, embeddings, priority, duplicate detection, and routing."""

from app.ai.vision import VisionAnalyzer, GeminiVisionAnalyzer, MockVisionAnalyzer, get_vision_analyzer
from app.ai.embeddings import ImageEmbedder
from app.ai.priority import PriorityEngine
from app.ai.duplicate_detection import DuplicateDetector
from app.ai.department_routing import DepartmentRouter

__all__ = [
    "VisionAnalyzer",
    "GeminiVisionAnalyzer",
    "MockVisionAnalyzer",
    "get_vision_analyzer",
    "ImageEmbedder",
    "PriorityEngine",
    "DuplicateDetector",
    "DepartmentRouter",
]
