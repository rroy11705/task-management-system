"""
Database models for the URL Shortener Service.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from database import Base

class URLModel(Base):
    """
    URL database model.
    """
    __tablename__ = "urls"

    id = Column(String, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True, nullable=False)
    created_by = Column(String, nullable=False)
    tenant_id = Column(String, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    password_hash = Column(String)
    access_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())