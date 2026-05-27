"""
Pydantic v2 schema for User response DTO.
"""

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """Schema for user data returned in responses."""

    id: str
    email: EmailStr

    model_config = {"from_attributes": True}
