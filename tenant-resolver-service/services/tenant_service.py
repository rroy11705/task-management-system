"""
Service for managing tenants.
"""

import uuid
import os
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models import TenantModel
from schemas import TenantCreate, DatabaseConnection
from database_service import provision_database, run_migrations
from events.rabbitmq_client import rabbitmq_client

async def create_tenant(db: Session, tenant: TenantCreate):
    """
    Create a new tenant in the database and provision its database.
    """
    # Check if tenant with same subdomain already exists
    existing_tenant = get_tenant_by_subdomain(db, tenant.subdomain)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant with subdomain '{tenant.subdomain}' already exists",
        )
    
    # Generate a unique ID for the tenant
    tenant_id = str(uuid.uuid4())
    
    # Generate database credentials
    db_name = f"tenant_{tenant_id.replace('-', '_')}"
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = f"tenant_user_{tenant_id.replace('-', '_')}"
    db_password = str(uuid.uuid4())  # In production, use a stronger password generation method
    
    # Create tenant in database
    db_tenant = TenantModel(
        id=tenant_id,
        name=tenant.name,
        subdomain=tenant.subdomain,
        db_name=db_name,
        db_host=db_host,
        db_port=db_port,
        db_user=db_user,
        db_password=db_password,
        is_active=True
    )
    
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    
    # Provision database for the tenant
    try:
        provision_database(db_tenant)
        run_migrations(db_tenant)
    except Exception as e:
        # Rollback tenant creation in case of database provisioning failure
        db.delete(db_tenant)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to provision database for tenant: {str(e)}",
        )
    
    # Publish TenantCreated event
    try:
        await rabbitmq_client.publish_event("tenant.created", {
            "tenant_id": tenant_id,
            "name": tenant.name,
            "subdomain": tenant.subdomain
        })
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to publish TenantCreated event: {str(e)}")
    
    return db_tenant

def get_tenant(db: Session, tenant_id: str):
    """
    Get tenant details by ID.
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {tenant_id} not found",
        )
    return tenant

def get_tenant_by_subdomain(db: Session, subdomain: str):
    """
    Get tenant details by subdomain.
    """
    return db.query(TenantModel).filter(TenantModel.subdomain == subdomain).first()

def get_database_connection(db: Session, tenant_id: str) -> DatabaseConnection:
    """
    Get database connection details for a tenant.
    """
    tenant = get_tenant(db, tenant_id)
    
    return DatabaseConnection(
        db_name=tenant.db_name,
        db_host=tenant.db_host,
        db_port=tenant.db_port,
        db_user=tenant.db_user,
        db_password=tenant.db_password
    )