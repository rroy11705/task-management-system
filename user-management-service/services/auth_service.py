# File: task-management-system/user-management-service/models.py
"""
Database models for the User Management Service.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Association tables for many-to-many relationships
user_role_association = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id")),
    Column("role_id", String, ForeignKey("roles.id")),
)

role_permission_association = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String, ForeignKey("roles.id")),
    Column("permission_id", String, ForeignKey("permissions.id")),
)

class UserModel(Base):
    """
    User database model.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    tenant_id = Column(String, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    roles = relationship("RoleModel", secondary=user_role_association, back_populates="users")

class RoleModel(Base):
    """
    Role database model.
    """
    __tablename__ = "roles"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("UserModel", secondary=user_role_association, back_populates="roles")
    permissions = relationship("PermissionModel", secondary=role_permission_association, back_populates="roles")

class PermissionModel(Base):
    """
    Permission database model.
    """
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    roles = relationship("RoleModel", secondary=role_permission_association, back_populates="permissions")

# File: task-management-system/user-management-service/schemas.py
"""
Pydantic schemas for the User Management Service.
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tenant_id: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    roles: List["Role"] = []

    class Config:
        orm_mode = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class Role(RoleBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    permissions: List["Permission"] = []

    class Config:
        orm_mode = True

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class Permission(PermissionBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Update forward references
User.update_forward_refs()
Role.update_forward_refs()

# File: task-management-system/user-management-service/services/auth_service.py
"""
Service for handling authentication and authorization.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import UserModel
from schemas import User

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your_secret_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    """
    Verify password against hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Hash password.
    """
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    """
    Authenticate user with username and password.
    """
    # TODO: Implement user authentication logic
    # 1. Get user from database
    # 2. Verify password
    # 3. Return user if authentication successful
    pass

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT token.
    """
    # TODO: Implement token creation logic
    # 1. Copy data to encode
    # 2. Set expiration
    # 3. Create JWT token
    pass

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get current user from JWT token.
    """
    # TODO: Implement current user retrieval logic
    # 1. Decode JWT token
    # 2. Get user from database
    # 3. Return user
    pass