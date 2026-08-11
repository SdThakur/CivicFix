"""Search API Router."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.search import SearchResult
from app.services.search_service import search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/", response_model=SearchResult)
async def global_search(
    q: str = Query(..., min_length=2, description="Search query string"),
    category: Optional[str] = Query(None),
    neighborhood: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> SearchResult:
    """Perform global cross-entity search across reports, issues, and work orders."""
    return await search_service.search_all(
        db=db,
        query_text=q,
        category=category,
        neighborhood=neighborhood,
        limit=limit,
    )
