from app.schemas.attraction import (
    AttractionCreate,
    AttractionResponse,
    AttractionUpdate,
)
from app.schemas.auth import (
    AuthRequest,
    AuthResponse,
    PasswordResetRequest,
    RegisterRequest,
)
from app.schemas.photo import PhotoPage, PhotoResponse
from app.schemas.user import UserResponse

__all__ = [
    # Attraction
    "AttractionCreate",
    "AttractionUpdate",
    "AttractionResponse",
    # Auth
    "RegisterRequest",
    "AuthRequest",
    "AuthResponse",
    "PasswordResetRequest",
    # Photo
    "PhotoResponse",
    "PhotoPage",
    # User
    "UserResponse",
]
