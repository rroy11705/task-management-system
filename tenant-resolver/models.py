from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    subdomain = Column(String, unique=True, index=True)
    project_db_url = Column(String)
    short_url_db_url = Column(String)
    analytics_db_url = Column(String)
    permissions_db_url = Column(String)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
