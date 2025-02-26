"""
Database models for the Tenant Resolver Service.
"""

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base

class TenantModel(Base):
    """
    Tenant database model.
    """
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subdomain = Column(String, unique=True, nullable=False, index=True)
    db_name = Column(String, nullable=False)
    db_host = Column(String, nullable=False)
    db_port = Column(String, nullable=False)
    db_user = Column(String, nullable=False)
    db_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())