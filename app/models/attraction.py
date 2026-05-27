"""
SQLAlchemy ORM model for Attraction.

Represents a tourist attraction in Svishtov. Lore content is stored as
separate columns per language (ro/en) to avoid JSON complexity in queries.
Category and protection_status use string columns with application-level
validation via Pydantic schemas.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Attraction(Base):
    __tablename__ = "attractions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Category: "monument" | "museum" | "natural" | "church" | "other"
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)

    # Lore content per language
    lore_ro: Mapped[str] = mapped_column(Text, nullable=False, default="")
    lore_en: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Optional main representative photo URL
    main_photo_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Accessibility info
    wheelchair_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    audio_facilities: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Heritage / cultural significance fields (nullable — omitted when unavailable)
    # Values: "national_monument" | "unesco" | "local_heritage" | "unprotected" | None
    protection_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    european_significance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship: one attraction → many photos
    photos: Mapped[list["Photo"]] = relationship(  # noqa: F821
        "Photo",
        back_populates="attraction",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Photo.uploaded_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Attraction id={self.id!r} name={self.name!r} category={self.category!r}>"
