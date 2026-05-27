"""
SQLAlchemy ORM model for Photo.

Represents a photo contributed by an authenticated user for a specific
attraction. Photos are stored on Railway Persistent Volume (or Cloudflare R2
as fallback). Thumbnails are generated server-side with Pillow at upload time.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # FK → attractions.id
    attraction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("attractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # FK → users.id
    uploader_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Paths/URLs for the full image and its thumbnail
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(1000), nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    attraction: Mapped["Attraction"] = relationship(  # noqa: F821
        "Attraction",
        back_populates="photos",
        lazy="select",
    )
    uploader: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="photos",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Photo id={self.id!r} attraction_id={self.attraction_id!r} "
            f"uploader_user_id={self.uploader_user_id!r}>"
        )
