"""
Pydantic schemas for the Tenant Resolver Service.
"""

from pydantic import BaseModel, Field, validator
import re
from datetime import datetime
from typing import Optional

class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="The display name for the tenant organization")
    subdomain: str = Field(..., min_length=3, max_length=63, description="The subdomain that will be used to access the tenant's instance")
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        # Subdomain validation: letters, numbers, hyphens, no spaces, no special chars
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$', v):
            raise ValueError('Subdomain must contain only letters, numbers, and hyphens, and cannot start or end with a hyphen')
        return v.lower()  # Convert to lowercase for consistency

class TenantCreate(TenantBase):
    pass

class Tenant(TenantBase):
    id: str
    db_name: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class DatabaseConnection(BaseModel):
    db_name: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str