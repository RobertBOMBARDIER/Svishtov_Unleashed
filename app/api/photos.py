"""
Photo endpoints.

Routes
------
GET    /attractions/{id}/photos               — paginated gallery (public)
GET    /attractions/{id}/photos/recent        — recent highlights (public)
POST   /attractions/{id}/photos               — upload a photo (JWT required)
DELETE /photos/{photoId}                      — delete own photo (JWT required)

Pagination (gallery)
--------------------
Query params: ``page`` (1-based, default 1) and ``size`` (default 20).
Response: ``PhotoPage`` schema with ``photos``, ``total``, ``page``, ``page_size``.

Recent highlights (Requirement 11.1 / 11.2)
--------------------------------------------
Query params: ``days`` (default 7) and ``limit`` (default 10, max 10).
Returns photos uploaded within the last ``days`` calendar days, sorted
descending by ``uploaded_at``, capped at ``limit`` items.

Upload (Requirement 3.7 / 3.9 / 4.1)
--------------------------------------
Multipart/form-data with a single ``file`` field.
Validates JPEG/PNG with Pillow, saves to Railway Volume, generates thumbnail.

Delete (Requirement 4.8)
------------------------
Only the photo owner can delete their photo (HTTP 403 otherwise).
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.attraction import Attraction
from app.models.photo import Photo
from app.models.user import User
from app.schemas.photo import PhotoPage, PhotoResponse
from app.services.photo_storage import delete_photo_files, save_photo

router = APIRouter(tags=["photos"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_attraction_or_404(
    attraction_id: str, db: AsyncSession
) -> Attraction:
    """Fetch an attraction by ID or raise HTTP 404."""
    result = await db.execute(
        select(Attraction).where(Attraction.id == attraction_id)
    )
    attraction: Attraction | None = result.scalar_one_or_none()
    if attraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atracția cu id={attraction_id!r} nu a fost găsită.",
        )
    return attraction


# ── GET /attractions/{id}/photos/recent ──────────────────────────────────────
# NOTE: This route MUST be registered before /attractions/{id}/photos to avoid
# FastAPI matching "recent" as a page/size query string on the paginated route.

@router.get(
    "/attractions/{attraction_id}/photos/recent",
    response_model=list[PhotoResponse],
    summary="Highlight-uri recente",
)
async def get_recent_photos(
    attraction_id: str,
    days: int = Query(default=7, ge=1, le=365, description="Numărul de zile în urmă"),
    limit: int = Query(default=10, ge=1, le=10, description="Numărul maxim de fotografii"),
    db: AsyncSession = Depends(get_db),
) -> list[PhotoResponse]:
    """
    Return the most recent photos for an attraction uploaded within the last
    ``days`` calendar days, sorted descending by upload time, capped at
    ``limit`` (max 10).

    Public endpoint — no authentication required.

    Validates: Requirements 11.1, 11.2
    """
    await _get_attraction_or_404(attraction_id, db)

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Photo)
        .where(
            Photo.attraction_id == attraction_id,
            Photo.uploaded_at >= cutoff,
        )
        .order_by(Photo.uploaded_at.desc())
        .limit(limit)
    )
    photos = result.scalars().all()
    return [PhotoResponse.from_orm_model(p) for p in photos]


# ── GET /attractions/{id}/photos ─────────────────────────────────────────────

@router.get(
    "/attractions/{attraction_id}/photos",
    response_model=PhotoPage,
    summary="Galerie paginată",
)
async def get_photos(
    attraction_id: str,
    page: int = Query(default=1, ge=1, description="Numărul paginii (1-based)"),
    size: int = Query(default=20, ge=1, le=100, description="Fotografii per pagină"),
    db: AsyncSession = Depends(get_db),
) -> PhotoPage:
    """
    Return a paginated list of photos for an attraction.

    Query params:
    - ``page``: 1-based page number (default 1)
    - ``size``: photos per page (default 20, max 100)

    Public endpoint — no authentication required (Requirement 4.1).
    """
    await _get_attraction_or_404(attraction_id, db)

    # Total count
    count_result = await db.execute(
        select(func.count(Photo.id)).where(Photo.attraction_id == attraction_id)
    )
    total: int = count_result.scalar_one()

    # Paginated photos, newest first
    offset = (page - 1) * size
    photos_result = await db.execute(
        select(Photo)
        .where(Photo.attraction_id == attraction_id)
        .order_by(Photo.uploaded_at.desc())
        .offset(offset)
        .limit(size)
    )
    photos = photos_result.scalars().all()

    return PhotoPage(
        photos=[PhotoResponse.from_orm_model(p) for p in photos],
        total=total,
        page=page,
        page_size=size,
    )


# ── POST /attractions/{id}/photos ─────────────────────────────────────────────

@router.post(
    "/attractions/{attraction_id}/photos",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Încărcare fotografie",
)
async def upload_photo(
    attraction_id: str,
    file: UploadFile = File(..., description="Fișier imagine JPEG sau PNG"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotoResponse:
    """
    Upload a photo for an attraction.

    - Requires JWT authentication (Requirement 3.9).
    - Accepts JPEG and PNG only; validates with Pillow (Requirement 3.7).
    - Saves original to Railway Volume and generates a 300×300 thumbnail.
    - Associates the photo with the authenticated user and the attraction.

    Validates: Requirements 3.7, 3.9, 4.1, 4.4
    """
    await _get_attraction_or_404(attraction_id, db)

    # Validate and persist the file; raises HTTP 400 on invalid format/size
    image_url, thumbnail_url = await save_photo(file)

    photo = Photo(
        id=str(uuid.uuid4()),
        attraction_id=attraction_id,
        uploader_user_id=current_user.id,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
    )
    db.add(photo)
    await db.flush()  # populate photo.uploaded_at from server_default

    # Refresh to get the server-generated uploaded_at timestamp
    await db.refresh(photo)

    return PhotoResponse.from_orm_model(photo)


# ── DELETE /photos/{photoId} ──────────────────────────────────────────────────

@router.delete(
    "/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Ștergere fotografie proprie",
)
async def delete_photo(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a photo by ID.

    - Requires JWT authentication.
    - Only the photo owner can delete it; returns HTTP 403 otherwise
      (Requirement 4.8).
    - Removes the database record and the physical files from storage.

    Validates: Requirements 4.8
    """
    result = await db.execute(select(Photo).where(Photo.id == photo_id))
    photo: Photo | None = result.scalar_one_or_none()

    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fotografia cu id={photo_id!r} nu a fost găsită.",
        )

    if photo.uploader_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nu ai permisiunea să ștergi această fotografie.",
        )

    # Remove physical files (best-effort; does not raise on missing files)
    delete_photo_files(photo.image_url, photo.thumbnail_url)

    await db.delete(photo)
    # Commit is handled by the get_db dependency after the handler returns.
    return None
