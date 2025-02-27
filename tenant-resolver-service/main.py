"""
Tenant Resolver Service for the Task Management System.
Manages organization subdomains and their corresponding database connections.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session

from database import get_db, init_db
from models import TenantModel
from schemas import TenantCreate, Tenant, DatabaseConnection
from services import tenant_service, database_service
from events.rabbitmq_client import rabbitmq_client
from shared.events import EventType

# Initialize FastAPI app
app = FastAPI(title="Task Management System - Tenant Resolver Service")

# Initialize database
init_db()

@app.get("/")
async def root():
    return {"message": "Tenant Resolver Service"}

@app.post("/tenants", response_model=Tenant, status_code=status.HTTP_201_CREATED)
async def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    """
    Create a new tenant and provision a database for it.
    """
    # Check if tenant with this subdomain already exists
    existing_tenant = tenant_service.get_tenant_by_subdomain(db, tenant.subdomain)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with subdomain '{tenant.subdomain}' already exists"
        )
    
    # Create tenant in the database
    new_tenant = await tenant_service.create_tenant(db, tenant)
    
    # Publish TenantCreated event
    event_payload = {
        "tenant_id": new_tenant.id,
        "name": new_tenant.name,
        "subdomain": new_tenant.subdomain,
        "db_name": new_tenant.db_name
    }
    
    try:
        await rabbitmq_client.publish_event(EventType.TENANT_CREATED, event_payload)
    except Exception as e:
        # Log this error but don't fail the request, as the tenant is created successfully
        print(f"Failed to publish tenant creation event: {str(e)}")
    
    return new_tenant

@app.get("/tenants/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """
    Get tenant details by ID.
    """
    tenant = tenant_service.get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found"
        )
    return tenant

@app.get("/tenants/subdomain/{subdomain}", response_model=Tenant)
async def get_tenant_by_subdomain(subdomain: str, db: Session = Depends(get_db)):
    """
    Get tenant details by subdomain.
    """
    tenant = tenant_service.get_tenant_by_subdomain(db, subdomain)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with subdomain '{subdomain}' not found"
        )
    return tenant

@app.get("/tenants/{tenant_id}/database", response_model=DatabaseConnection)
async def get_tenant_database_connection(tenant_id: str, db: Session = Depends(get_db)):
    """
    Get database connection details for a tenant.
    """
    tenant = tenant_service.get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found"
        )
    
    # Return database connection details
    return DatabaseConnection(
        db_name=tenant.db_name,
        db_host=tenant.db_host,
        db_port=tenant.db_port,
        db_user=tenant.db_user,
        db_password=tenant.db_password
    )

@app.post("/tenants/{tenant_id}/migrations", status_code=status.HTTP_200_OK)
async def run_tenant_migrations(tenant_id: str, db: Session = Depends(get_db)):
    """
    Run database migrations for a tenant.
    """
    tenant = tenant_service.get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found"
        )
    
    try:
        database_service.run_migrations(tenant)
        return {"message": f"Migrations successfully applied for tenant '{tenant.name}'"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run migrations: {str(e)}"
        )

@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler with improved error handling.
    """
    try:
        print("Initializing tenant-resolver-service...")
        # Try to connect to RabbitMQ, but don't fail startup if it doesn't connect
        try:
            await rabbitmq_client.connect()
        except Exception as e:
            print(f"Warning: Failed to connect to RabbitMQ during startup: {str(e)}")
            print("The service will attempt to reconnect when needed.")
            # We'll continue startup even if RabbitMQ is not available
        
        print("Tenant-resolver-service initialized successfully.")
    except Exception as e:
        print(f"Error during startup: {str(e)}")
        # Don't re-raise the exception to allow the app to start anyway

@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    """
    try:
        # Only try to close if we previously connected
        if rabbitmq_client._connected:
            await rabbitmq_client.close()
    except Exception as e:
        print(f"Error during shutdown: {str(e)}")