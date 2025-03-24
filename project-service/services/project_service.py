"""
Service for managing projects.
"""

import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any

from models import ProjectModel
from schemas import ProjectCreate, ProjectUpdate, Project
from events.rabbitmq_client import rabbitmq_client
from events.project_events import ProjectCreatedEvent, ProjectUpdatedEvent, ProjectDeletedEvent

async def create_project(db: Session, project: ProjectCreate, tenant_id: str, user_id: str) -> ProjectModel:
    """
    Create a new project.
    
    Args:
        db: Database session
        project: Project data
        tenant_id: Tenant ID
        user_id: User ID
        
    Returns:
        The created project
        
    Raises:
        HTTPException: If project creation fails
    """
    # Generate a unique ID for the project
    project_id = str(uuid.uuid4())
    
    # Create project in database
    db_project = ProjectModel(
        id=project_id,
        name=project.name,
        description=project.description,
        tenant_id=tenant_id,
        created_by=user_id,
        is_active=True
    )
    
    try:
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )
    
    # Publish ProjectCreated event
    try:
        event = ProjectCreatedEvent(
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            project_name=project.name
        )
        await rabbitmq_client.publish_event(event.event_type, event.to_dict())
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Failed to publish ProjectCreated event: {str(e)}")
    
    return db_project

async def get_project(db: Session, project_id: str, tenant_id: str) -> ProjectModel:
    """
    Get project by ID.
    
    Args:
        db: Database session
        project_id: Project ID
        tenant_id: Tenant ID
        
    Returns:
        The project
        
    Raises:
        HTTPException: If project not found or doesn't belong to tenant
    """
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.tenant_id == tenant_id,
        ProjectModel.is_active == True
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    return project

async def get_projects(db: Session, tenant_id: str, skip: int = 0, limit: int = 100) -> List[ProjectModel]:
    """
    Get all projects for a tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of projects
    """
    return db.query(ProjectModel).filter(
        ProjectModel.tenant_id == tenant_id,
        ProjectModel.is_active == True
    ).offset(skip).limit(limit).all()

async def update_project(
    db: Session, 
    project_id: str, 
    project_update: ProjectUpdate, 
    tenant_id: str, 
    user_id: str
) -> ProjectModel:
    """
    Update a project.
    
    Args:
        db: Database session
        project_id: Project ID
        project_update: Project update data
        tenant_id: Tenant ID
        user_id: User ID
        
    Returns:
        The updated project
        
    Raises:
        HTTPException: If project not found or update fails
    """
    # Get project
    project = await get_project(db, project_id, tenant_id)
    
    # Track updated fields for event
    updated_fields = {}
    
    # Update project fields
    if project_update.name is not None and project_update.name != project.name:
        project.name = project_update.name
        updated_fields["name"] = project_update.name
    
    if project_update.description is not None and project_update.description != project.description:
        project.description = project_update.description
        updated_fields["description"] = project_update.description
    
    # Only commit if there are changes
    if updated_fields:
        try:
            db.commit()
            db.refresh(project)
            
            # Publish ProjectUpdated event
            try:
                event = ProjectUpdatedEvent(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    project_id=project_id,
                    updated_fields=updated_fields
                )
                await rabbitmq_client.publish_event(event.event_type, event.to_dict())
            except Exception as e:
                # Log the error but don't fail the request
                print(f"Failed to publish ProjectUpdated event: {str(e)}")
        
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update project: {str(e)}"
            )
    
    return project

async def delete_project(db: Session, project_id: str, tenant_id: str, user_id: str) -> ProjectModel:
    """
    Delete a project (soft delete).
    
    Args:
        db: Database session
        project_id: Project ID
        tenant_id: Tenant ID
        user_id: User ID
        
    Returns:
        The deleted project
        
    Raises:
        HTTPException: If project not found or deletion fails
    """
    # Get project
    project = await get_project(db, project_id, tenant_id)
    
    # Soft delete
    project.is_active = False
    
    try:
        db.commit()
        db.refresh(project)
        
        # Publish ProjectDeleted event
        try:
            event = ProjectDeletedEvent(
                tenant_id=tenant_id,
                user_id=user_id,
                project_id=project_id,
                project_name=project.name
            )
            await rabbitmq_client.publish_event(event.event_type, event.to_dict())
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Failed to publish ProjectDeleted event: {str(e)}")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )
    
    return project

async def search_projects(
    db: Session, 
    tenant_id: str, 
    search_term: str, 
    skip: int = 0, 
    limit: int = 100
) -> List[ProjectModel]:
    """
    Search projects by name or description.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        search_term: Search term
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of matching projects
    """
    return db.query(ProjectModel).filter(
        ProjectModel.tenant_id == tenant_id,
        ProjectModel.is_active == True,
        (
            ProjectModel.name.ilike(f"%{search_term}%") | 
            ProjectModel.description.ilike(f"%{search_term}%")
        )
    ).offset(skip).limit(limit).all()