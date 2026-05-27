"""
Pydantic v2 schemas for Photo request/response DTOs.

These schemas define the JSON shape for photo-related API responses.
The Android client deserializes these into Kotlin data classes (PhotoDto, PhotoPage).

Field naming follows the API contract defined in design.md.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class PhotoResponse(BaseModel):
    """
    Schema for a single photo API response.

    Matches the Android PhotoDto:
      id, attraction_id, uploader_user_id, image_url, thumbnail_url, uploaded_at (ISO 8601)
    """

    id: str
    attraction_id: str
    uploader_user_id: str
    image_url: str
    thumbnail_url: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, photo: object) -> "PhotoResponse":
        """Build a response from an ORM Photo instance."""
        from app.models.photo import Photo as PhotoORM

        assert isinstance(photo, PhotoORM)
        return cls(
            id=photo.id,
            attraction_id=photo.attraction_id,
            uploader_user_id=photo.uploader_user_id,
            image_url=photo.image_url,
            thumbnail_url=photo.thumbnail_url,
            uploaded_at=photo.uploaded_at,
        )


class PhotoPage(BaseModel):
    """
    Paginated gallery response.

    Matches the Android PhotoPage DTO:
      photos, total, page, page_size
    """

    photos: List[PhotoResponse]
    total: int = Field(..., ge=0, description="Total number of photos for this attraction")
    page: int = Field(..., ge=1, description="Current page number (1-based)")
    page_size: int = Field(..., ge=1, description="Number of photos per page")
