"""
Pydantic v2 schemas for authentication request/response DTOs.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class AuthRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Schema for successful authentication response."""

    token: str
    user_id: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr
