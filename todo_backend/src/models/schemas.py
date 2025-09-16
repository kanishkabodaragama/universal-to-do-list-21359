from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# Auth/token models
class Token(BaseModel):
    """Access token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type, usually 'bearer'")


class TokenData(BaseModel):
    """Decoded token data."""
    username: Optional[str] = Field(None, description="User email/username")
    scopes: List[str] = Field(default_factory=list, description="Granted scopes")


# User models
class UserCreate(BaseModel):
    """Payload for creating/registering a user."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")


class UserUpdatePassword(BaseModel):
    """Payload for updating user's password."""
    new_password: str = Field(..., min_length=6, description="New password")


class UserPublic(BaseModel):
    """Public user profile."""
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


# Todo models
class TodoBase(BaseModel):
    """Base fields for a Todo item."""
    title: str = Field(..., description="Todo title")
    description: Optional[str] = Field(None, description="Optional details")
    completed: bool = Field(False, description="Completion flag")


class TodoCreate(TodoBase):
    """Payload to create a Todo."""
    pass


class TodoUpdate(BaseModel):
    """Payload to update a Todo."""
    title: Optional[str] = Field(None, description="Todo title")
    description: Optional[str] = Field(None, description="Optional details")
    completed: Optional[bool] = Field(None, description="Completion flag")


class TodoPublic(TodoBase):
    """Public representation of a Todo."""
    id: str = Field(..., description="Todo ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
