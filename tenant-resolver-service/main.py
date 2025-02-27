"""
Tenant Resolver Service for the Task Management System.
Manages organization subdomains and their corresponding database connections.
"""

import os
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
import asyncio

from database import get_db, init_db
from models import TenantModel
from schemas import TenantCreate, Tenant, DatabaseConnection
from services.tenant_service import (
    create_tenant, 
    get_tenant, 
    get_tenant_by_subdomain,
    get_database_connection
)
from events.rabbitmq_client import rabbitmq_client

# Initialize FastAPI app
app = FastAPI(
    title="Task Management System - Tenant Resolver Service",
    description="Manages organization subdomains and their corresponding database connections",
    version="1.0.0"
)

# Initialize database
init_db()

@app.get("/", tags=["Health"])
async def root():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "Tenant Resolver Service"}

@app.post("/tenants", response_model=Tenant, status_code=status.HTTP_201_CREATED, tags=["Tenants"])
async def create_new_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    """
    Create a new tenant and provision a database for it.
    
    - **name**: The display name for the tenant organization
    - **subdomain**: The subdomain that will be used to access the tenant's instance
    """
    return await create_tenant(db, tenant)

@app.get("/tenants/{tenant_id}", response_model=Tenant, tags=["Tenants"])
async def get_tenant_by_id(tenant_id: str, db: Session = Depends(get_db)):
    """
    Get tenant details by ID.
    """
    return get_tenant(db, tenant_id)

@app.get("/tenants/by-subdomain/{subdomain}", response_model=Tenant, tags=["Tenants"])
async def get_tenant_details_by_subdomain(subdomain: str, db: Session = Depends(get_db)):
    """
    Get tenant details by subdomain.
    """
    tenant = get_tenant_by_subdomain(db, subdomain)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with subdomain '{subdomain}' not found",
        )
    return tenant

@app.get("/tenants/{tenant_id}/database", response_model=DatabaseConnection, tags=["Databases"])
async def get_tenant_database_connection_details(tenant_id: str, db: Session = Depends(get_db)):
    """
    Get database connection details for a tenant.
    """
    return get_database_connection(db, tenant_id)

@app.post("/tenants/{tenant_id}/migrations", tags=["Databases"])
async def run_tenant_migrations(tenant_id: str, db: Session = Depends(get_db)):
    """
    Run database migrations for a tenant.
    """
    from database_service import run_migrations
    
    tenant = get_tenant(db, tenant_id)
    try:
        run_migrations(tenant)
        return {"status": "success", "message": f"Migrations completed for tenant {tenant_id}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run migrations: {str(e)}",
        )

@app.on_event("startup")
async def startup_event():
    """
    Connect to RabbitMQ on startup.
    """
    try:
        await rabbitmq_client.connect()
    except Exception as e:
        print(f"Warning: Failed to connect to RabbitMQ on startup: {str(e)}")
        print("The service will attempt to reconnect when events are published.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Close RabbitMQ connection on shutdown.
    """
    await rabbitmq_client.close()