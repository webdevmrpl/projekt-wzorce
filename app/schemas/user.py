from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRoles(str, Enum):
    ADMIN = "admin"
    USER = "user"
    STAFF = "staff"


class User(BaseModel):
    """Base schema for a user, shared across other schemas."""

    username: str = Field(min_length=3, max_length=50, example="john_doe")
    email: EmailStr = Field(..., example="john_doe@gmail.com")
    password: str = Field(..., min_length=8, max_length=100, example="hashed_password")

    full_name: Optional[str] = Field(default=None, max_length=100, example="John Doe")

    is_active: bool = Field(True)
    is_verified: bool = Field(False)

    roles: List[str] = Field(default=["user"], example=["user"])
    created_at: Optional[datetime] = Field(default=None, example="2021-01-01T00:00:00Z")
    updated_at: Optional[datetime] = Field(default=None, example="2021-01-01T00:00:00Z")


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(min_length=3, max_length=50, example="john_doe")
    email: EmailStr = Field(..., example="john_doe@gmail.com")
    password: str = Field(
        ..., min_length=8, max_length=100, example="nonhashed_password12"
    )
    full_name: Optional[str] = Field(None, max_length=100, example="John Doe")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter")
        return value


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    username: Optional[str] = Field(
        default=None, min_length=6, max_length=50, example="john_doe"
    )
    full_name: Optional[str] = Field(default=None, max_length=100, example="John Doe")
    password: Optional[str] = Field(
        default=None, min_length=8, max_length=100, example="hashed_password12"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: Optional[str]) -> Optional[str]:
        if value:
            if len(value) < 8:
                raise ValueError("Password must be at least 8 characters long")
            if not any(char.isdigit() for char in value):
                raise ValueError("Password must contain at least one digit")
            if not any(char.isalpha() for char in value):
                raise ValueError("Password must contain at least one letter")
        return value


class UserLogin(BaseModel):
    """Schema for user login."""

    email: str = Field(..., example="john_doe@gmail.com")
    password: str = Field(..., example="nonhashed_password12")


class UserToken(BaseModel):
    """Schema for access and refresh tokens."""

    access_token: str = Field(..., example="access_token")
    refresh_token: str = Field(..., example="refresh_token")
    token_type: str = Field(default="bearer", example="bearer")
    expires_in: int = Field(..., example=3600)


class UserPasswordReset(BaseModel):
    """Schema for resetting the password."""

    email: EmailStr = Field(..., example="john_doe@gmail.com")


class UserPasswordChange(BaseModel):
    """Schema for changing the password."""

    current_password: str = Field(
        ..., min_length=8, max_length=100, example="current_nonshashed_password"
    )
    new_password: str = Field(
        ..., min_length=8, max_length=100, examples="new_nonhashed_password"
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter")
        return value


class UserPermission(str, Enum):
    """Enum for user permissions."""

    LIST_TASKS = "list_tasks"
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    LIST_USERS = "list_users"
    DELETE_USERS = "delete_users"
