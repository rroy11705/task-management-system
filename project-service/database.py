"""
Database configuration for the Project Service.
"""

import os
import httpx
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import Depends, Request

Base = declarative_base()

# Dict to cache database sessions for tenants
tenant_sessions = {}

async def get_db_connection_for_tenant(tenant_id: str):
    """
    Get database connection details for a tenant from Tenant Resolver Service.
    """
    # TODO: Implement tenant database connection retrieval
    # 1. Query Tenant Resolver Service for database connection details
    # 2. Return connection details
    tenant_resolver_url = os.getenv("TENANT_RESOLVER_SERVICE_URL", "http://localhost:8001")
    
    # For development, hardcode a connection string
    return f"postgresql://postgres:postgres@localhost:5432/tenant_{tenant_id}"

def get_db_for_tenant(request: Request):
    """
    Get database session for a tenant.
    """
    # Extract tenant_id from request state (set by middleware)
    tenant_id = request.state.tenant_id
    
    # Check if we already have a session for this tenant
    if tenant_id not in tenant_sessions:
        # Get database connection details
        db_url = get_db_connection_for_tenant(tenant_id)
        
        # Create engine and session
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Cache session
        tenant_sessions[tenant_id] = SessionLocal
    
    # Get session from cache
    db = tenant_sessions[tenant_id]()
    try:
        yield db
    finally:
        db.close()