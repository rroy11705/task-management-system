"""
Pydantic schemas for the Tenant Resolver Service.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TenantBase(BaseModel):
    name: str
    subdomain: str

class TenantCreate(TenantBase):
    pass

class Tenant(TenantBase):
    id: str
    db_name: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class DatabaseConnection(BaseModel):
    db_name: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str
