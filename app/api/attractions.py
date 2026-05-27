"""
Attractions endpoints.

Routes
------
GET  /attractions        — list all attractions
GET  /attractions/{id}   — get a single attraction by ID

Both endpoints are public (no JWT required).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.attraction import Attraction
from app.schemas.attraction import AttractionResponse

router = APIRouter(prefix="/attractions", tags=["attractions"])


# ── GET /attractions ──────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[AttractionResponse],
    summary="Listă toate atracțiile",
)
async def list_attractions(
    db: AsyncSession = Depends(get_db),
) -> list[AttractionResponse]:
    """
    Return all tourist attractions, ordered alphabetically by name.

    Public endpoint — no authentication required (Requirement 10.10).
    """
    result = await db.execute(select(Attraction).order_by(Attraction.name))
    attractions = result.scalars().all()
    return [AttractionResponse.from_orm_model(a) for a in attractions]


# ── GET /attractions/{id} ─────────────────────────────────────────────────────

@router.get(
    "/{attraction_id}",
    response_model=AttractionResponse,
    summary="Detalii atracție",
)
async def get_attraction(
    attraction_id: str,
    db: AsyncSession = Depends(get_db),
) -> AttractionResponse:
    """
    Return details for a single attraction.

    Raises HTTP 404 if the attraction does not exist.
    Public endpoint — no authentication required (Requirement 10.10).
    """
    result = await db.execute(
        select(Attraction).where(Attraction.id == attraction_id)
    )
    attraction: Attraction | None = result.scalar_one_or_none()

    if attraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atracția cu id={attraction_id!r} nu a fost găsită.",
        )

    return AttractionResponse.from_orm_model(attraction)
