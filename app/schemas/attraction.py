"""
Pydantic v2 schemas for Attraction request/response DTOs.

These schemas are the source of truth for API validation and serialization.
The Android client deserializes these JSON responses into Kotlin data classes.

Field naming follows the API contract defined in design.md:
  - lat / lon  (not latitude / longitude) for coordinates
  - lore       (dict langCode → text)
  - main_photo_url, wheelchair_access, audio_facilities, etc.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# Allowed category values (mirrors Android Category enum)
CategoryLiteral = Literal["monument", "museum", "natural", "church", "other"]

# Allowed protection status values (mirrors Android ProtectionStatus enum)
ProtectionStatusLiteral = Literal[
    "national_monument", "unesco", "local_heritage", "unprotected"
]


class AttractionBase(BaseModel):
    """Shared fields used by both create and response schemas."""

    name: str = Field(..., min_length=1, max_length=255)
    category: CategoryLiteral
    lat: float = Field(..., alias="lat", ge=-90.0, le=90.0)
    lon: float = Field(..., alias="lon", ge=-180.0, le=180.0)
    address: str = Field(..., min_length=1, max_length=500)

    # Lore content keyed by language code ("ro", "en", …)
    lore: dict[str, str] = Field(
        default_factory=dict,
        description="Map of language code → lore text. Must include at least 'en'.",
    )

    main_photo_url: Optional[str] = Field(default=None, max_length=1000)
    wheelchair_access: bool = False
    audio_facilities: bool = False
    protection_status: Optional[ProtectionStatusLiteral] = None
    european_significance: Optional[str] = Field(default=None, max_length=5000)

    model_config = ConfigDict(populate_by_name=True)


class AttractionCreate(AttractionBase):
    """Schema for creating a new attraction (admin use)."""

    pass


class AttractionUpdate(BaseModel):
    """Schema for partial updates to an attraction (all fields optional)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[CategoryLiteral] = None
    lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    address: Optional[str] = Field(default=None, min_length=1, max_length=500)
    lore: Optional[dict[str, str]] = None
    main_photo_url: Optional[str] = Field(default=None, max_length=1000)
    wheelchair_access: Optional[bool] = None
    audio_facilities: Optional[bool] = None
    protection_status: Optional[ProtectionStatusLiteral] = None
    european_significance: Optional[str] = Field(default=None, max_length=5000)

    model_config = ConfigDict(populate_by_name=True)


class AttractionResponse(BaseModel):
    """
    Schema for attraction API responses.

    Serializes the ORM Attraction model into the JSON shape expected by the
    Android client (see AttractionDto in design.md).
    """

    id: str
    name: str
    category: str
    lat: float
    lon: float
    address: str
    lore: dict[str, str]
    main_photo_url: Optional[str]
    wheelchair_access: bool
    audio_facilities: bool
    protection_status: Optional[str]
    european_significance: Optional[str]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def from_orm_model(cls, attraction: object) -> "AttractionResponse":
        """
        Build a response from an ORM Attraction instance.

        Merges lore_ro / lore_en columns into the lore dict and maps
        latitude/longitude to lat/lon for the API contract.
        """
        # Import here to avoid circular imports at module level
        from app.models.attraction import Attraction as AttractionORM

        assert isinstance(attraction, AttractionORM)

        lore: dict[str, str] = {}
        if attraction.lore_ro:
            lore["ro"] = attraction.lore_ro
        if attraction.lore_en:
            lore["en"] = attraction.lore_en

        return cls(
            id=attraction.id,
            name=attraction.name,
            category=attraction.category,
            lat=attraction.latitude,
            lon=attraction.longitude,
            address=attraction.address,
            lore=lore,
            main_photo_url=attraction.main_photo_url,
            wheelchair_access=attraction.wheelchair_access,
            audio_facilities=attraction.audio_facilities,
            protection_status=attraction.protection_status,
            european_significance=attraction.european_significance,
        )
