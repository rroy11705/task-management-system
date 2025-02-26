"""
Pydantic schemas for the URL Shortener Service.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class URLBase(BaseModel):
    original_url: str
    expires_at: Optional[datetime] = None
    password: Optional[str] = None

class URLCreate(URLBase):
    pass

class URL(BaseModel):
    id: str
    original_url: str
    short_code: str
    created_by: str
    tenant_id: str
    expires_at: Optional[datetime]
    has_password: bool
    access_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class URLAccess(BaseModel):
    url_id: str
    accessed_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    referrer: Optional[str]