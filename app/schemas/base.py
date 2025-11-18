from pydantic import BaseModel, EmailStr, Field, ConfigDict, ValidationError, model_validator, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
import re


class UserBase(BaseModel):
    """Base user schema with common fields"""
    first_name: str = Field(
        min_length=1,
        max_length=50,
        description="User's first name",
        example="John"
    )
    last_name: str = Field(
        min_length=1,
        max_length=50,
        description="User's last name",
        example="Doe"
    )
    email: EmailStr = Field(
        description="User's email address (must be valid email format)",
        example="john.doe@example.com"
    )
    username: str = Field(
        min_length=3,
        max_length=50,
        description="Unique username (alphanumeric, underscore, and hyphen allowed)",
        example="johndoe"
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and sanitize name fields"""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        # Remove leading/trailing whitespace
        v = v.strip()
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Name can only contain letters, spaces, hyphens, and apostrophes")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not v or not v.strip():
            raise ValueError("Username cannot be empty or whitespace only")
        v = v.strip()
        # Username should be alphanumeric with underscore and hyphen
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        # Username should start with a letter or number
        if not re.match(r"^[a-zA-Z0-9]", v):
            raise ValueError("Username must start with a letter or number")
        return v

    model_config = ConfigDict(from_attributes=True)


class PasswordMixin(BaseModel):
    """Mixin for password validation"""
    password: str = Field(min_length=6, max_length=128, example="SecurePass123")

    @model_validator(mode="before")
    @classmethod
    def validate_password(cls, values: dict) -> dict:
        password = values.get("password")
        if not password:
            raise ValidationError("Password is required", model=cls) # pragma: no cover
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        return values


class UserCreate(UserBase, PasswordMixin):
    """
    Schema for user creation with comprehensive validation.
    
    Validates:
    - First and last names (non-empty, valid characters only)
    - Email (valid email format)
    - Username (3-50 chars, alphanumeric with underscore/hyphen)
    - Password (6-128 chars, must contain uppercase, lowercase, and digit)
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "username": "johndoe",
                "password": "SecurePass123"
            }
        }
    )


class UserRead(UserBase):
    """
    Schema for reading/retrieving user data.
    
    Includes all user information except sensitive data like password.
    Used for API responses when returning user information.
    """
    id: UUID = Field(
        description="Unique identifier for the user",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    is_active: bool = Field(
        description="Whether the user account is active",
        example=True
    )
    is_verified: bool = Field(
        description="Whether the user email has been verified",
        example=False
    )
    last_login: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the user's last login",
        example="2025-01-08T12:00:00"
    )
    created_at: datetime = Field(
        description="Timestamp when the user account was created",
        example="2025-01-01T00:00:00"
    )
    updated_at: datetime = Field(
        description="Timestamp when the user account was last updated",
        example="2025-01-08T12:00:00"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "is_verified": False,
                "last_login": "2025-01-08T12:00:00",
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-08T12:00:00"
            }
        }
    )


class UserLogin(PasswordMixin):
    """Schema for user login"""
    username: str = Field(
        description="Username or email",
        min_length=3,
        max_length=50,
        example="johndoe123"
    )