"""
Pydantic schemas for the User Management Service.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
import re

from shared.validation import validate_password_strength

class TokenData(BaseModel):
    """Token data for JWT payload."""
    user_id: str
    tenant_id: Optional[str] = None

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    tenant_id: str
    roles: List[str]

class PermissionBase(BaseModel):
    """Base permission schema."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    """Permission creation schema."""
    pass

class Permission(PermissionBase):
    """Permission response schema."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None

class RoleCreate(RoleBase):
    """Role creation schema."""
    pass

class Role(RoleBase):
    """Role response schema."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: List[Permission] = []

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tenant_id: str

    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must contain only letters, numbers, underscores, and hyphens')
        return v

class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password(cls, v):
        error = validate_password_strength(v)
        if error:
            raise ValueError(error)
        return v

class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('username')
    def username_alphanumeric(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must contain only letters, numbers, underscores, and hyphens')
        return v

    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            error = validate_password_strength(v)
            if error:
                raise ValueError(error)
        return v

class User(UserBase):
    """User response schema."""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    roles: List[Role] = []

    class Config:
        orm_mode = True

class UserRole(BaseModel):
    """User-role assignment schema."""
    user_id: str
    role_id: str

class RolePermission(BaseModel):
    """Role-permission assignment schema."""
    role_id: str
    permission_id: str

# Update forward references
User.update_forward_refs()
Role.update_forward_refs()