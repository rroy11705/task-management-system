"""
Service for managing tasks.
"""

import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime

from models import TaskModel, ProjectModel
from schemas import TaskCreate, TaskUpdate, Task
from events.rabbitmq_client import rabbitmq_client
from events.project_events import (
    TaskCreatedEvent, TaskUpdatedEvent, TaskStatusChangedEvent, 
    TaskAssignedEvent, TaskDeletedEvent
)

async def create_task(
    db: Session, 
    task: TaskCreate, 
    project_id: str, 
    tenant_id: str, 
    user_id: str,
    board_id: Optional[str] = None
) -> TaskModel:
    """
    Create a new task.
    
    Args:
        db: Database session
        task: Task data
        project_id: Project ID
        tenant_id: Tenant ID
        user_id: User ID
        board_id: Optional board ID
        
    Returns:
        The created task
        
    Raises:
        HTTPException: If project not found or task creation fails
    """
    # Check if project exists and belongs to tenant
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
    
    # Generate a unique ID for the task
    task_id = str(uuid.uuid4())
    
    # Create task in database
    db_task = TaskModel(
        id=task_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        project_id=project_id,
        assigned_to=task.assigned_to,
        created_by=user_id,
        board_id=board_id,
        is_active=True
    )
    
    try:
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )
    
    # Publish TaskCreated event
    try:
        event = TaskCreatedEvent(
            tenant_id=tenant_id,
            user_id=user_id,
            task_id=task_id,
            project_id=project_id,
            task_title=task.title,
            assigned_to=task.assigned_to
        )
        await rabbitmq_client.publish_event(event.event_type, event.to_dict())
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Failed to publish TaskCreated event: {str(e)}")
    
    return db_task

async def get_task(db: Session, task_id: str, tenant_id: str) -> TaskModel:
    """
    Get task by ID.
    
    Args:
        db: Database session
        task_id: Task ID
        tenant_id: Tenant ID
        
    Returns:
        The task
        
    Raises:
        HTTPException: If task not found or doesn't belong to tenant
    """
    # Join with project to verify tenant
    task = db.query(TaskModel).join(
        ProjectModel, TaskModel.project_id == ProjectModel.id
    ).filter(
        TaskModel.id == task_id,
        ProjectModel.tenant_id == tenant_id,
        TaskModel.is_active == True,
        ProjectModel.is_active == True
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return task

async def get_tasks(
    db: Session, 
    project_id: str, 
    tenant_id: str,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[TaskModel]:
    """
    Get all tasks for a project with optional filtering.
    
    Args:
        db: Database session
        project_id: Project ID
        tenant_id: Tenant ID
        status: Optional status filter
        assigned_to: Optional assignee filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of tasks
        
    Raises:
        HTTPException: If project not found or doesn't belong to tenant
    """
    # Check if project exists and belongs to tenant
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
    
    # Build query
    query = db.query(TaskModel).filter(
        TaskModel.project_id == project_id,
        TaskModel.is_active == True
    )
    
    # Apply filters
    if status:
        query = query.filter(TaskModel.status == status)
        
    if assigned_to:
        query = query.filter(TaskModel.assigned_to == assigned_to)
    
    return query.offset(skip).limit(limit).all()

async def update_task(
    db: Session, 
    task_id: str, 
    task_update: TaskUpdate, 
    tenant_id: str, 
    user_id: str
) -> TaskModel:
    """
    Update a task.
    
    Args:
        db: Database session
        task_id: Task ID
        task_update: Task update data
        tenant_id: Tenant ID
        user_id: User ID
        
    Returns:
        The updated task
        
    Raises:
        HTTPException: If task not found or update fails
    """
    # Get task
    task = await get_task(db, task_id, tenant_id)
    
    # Track updated fields for event
    updated_fields = {}
    
    # Check for status change
    old_status = None
    if task_update.status is not None and task_update.status != task.status:
        old_status = task.status
        task.status = task_update.status
        updated_fields["status"] = task_update.status
    
    # Check for assignment change
    old_assigned_to = None
    if task_update.assigned_to is not None and task_update.assigned_to != task.assigned_to:
        old_assigned_to = task.assigned_to
        task.assigned_to = task_update.assigned_to
        updated_fields["assigned_to"] = task_update.assigned_to
    
    # Update other fields
    if task_update.title is not None and task_update.title != task.title:
        task.title = task_update.title
        updated_fields["title"] = task_update.title
    
    if task_update.description is not None and task_update.description != task.description:
        task.description = task_update.description
        updated_fields["description"] = task_update.description
    
    if task_update.priority is not None and task_update.priority != task.priority:
        task.priority = task_update.priority
        updated_fields["priority"] = task_update.priority
    
    if task_update.board_id is not None and task_update.board_id != task.board_id:
        task.board_id = task_update.board_id
        updated_fields["board_id"] = task_update.board_id
    
    # Only commit if there are changes
    if updated_fields:
        try:
            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)
            
            # Status change event
            if old_status is not None:
                try:
                    event = TaskStatusChangedEvent(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        task_id=task_id,
                        project_id=task.project_id,
                        old_status=old_status,
                        new_status=task.status
                    )
                    await rabbitmq_client.publish_event(event.event_type, event.to_dict())
                except Exception as e:
                    print(f"Failed to publish TaskStatusChanged event: {str(e)}")
            
            # Assignment change event
            if old_assigned_to is not None:
                try:
                    event = TaskAssignedEvent(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        task_id=task_id,
                        project_id=task.project_id,
                        assigned_to=task.assigned_to
                    )
                    await rabbitmq_client.publish_event(event.event_type, event.to_dict())
                except Exception as e:
                    print(f"Failed to publish TaskAssigned event: {str(e)}")
            
            # General update event
            try:
                event = TaskUpdatedEvent(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    task_id=task_id,
                    project_id=task.project_id,
                    updated_fields=updated_fields
                )
                await rabbitmq_client.publish_event(event.event_type, event.to_dict())
            except Exception as e:
                print(f"Failed to publish TaskUpdated event: {str(e)}")
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update task: {str(e)}"
            )
    
    return task

async def delete_task(db: Session, task_id: str, tenant_id: str, user_id: str) -> TaskModel:
    """
    Delete a task (soft delete).
    
    Args:
        db: Database session
        task_id: Task ID
        tenant_id: Tenant ID
        user_id: User ID
        
    Returns:
        The deleted task
        
    Raises:
        HTTPException: If task not found or deletion fails
    """
    # Get task
    task = await get_task(db, task_id, tenant_id)
    
    # Store task details for event
    task_title = task.title
    project_id = task.project_id
    
    # Soft delete
    task.is_active = False
    
    try:
        db.commit()
        db.refresh(task)
        
        # Publish TaskDeleted event
        try:
            event = TaskDeletedEvent(
                tenant_id=tenant_id,
                user_id=user_id,
                task_id=task_id,
                project_id=project_id,
                task_title=task_title
            )
            await rabbitmq_client.publish_event(event.event_type, event.to_dict())
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Failed to publish TaskDeleted event: {str(e)}")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )
    
    return task

async def update_task_status(
    db: Session, 
    task_id: str, 
    status: str, 
    tenant_id: str, 
    user_id: str
) -> TaskModel:
    """
    Update task status.
    
    Args:
        db: Database session
        task_id: Task ID
        status: New status
        tenant_id: Tenant ID
        user_id: User ID
        
    Returns:
        The updated task
        
    Raises:
        HTTPException: If task not found or update fails
    """
    # Create a TaskUpdate with only the status field
    task_update = TaskUpdate(status=status)
    
    # Use the update_task function
    return await update_task(db, task_id, task_update, tenant_id, user_id)

async def assign_task(
    db: Session, 
    task_id: str, 
    assigned_to: str, 
    tenant_id: str, 
    user_id: str
) -> TaskModel:
    """
    Assign a task to a user.
    
    Args:
        db: Database session
        task_id: Task ID
        assigned_to: User ID to assign to
        tenant_id: Tenant ID
        user_id: User ID making the assignment
        
    Returns:
        The updated task
        
    Raises:
        HTTPException: If task not found or update fails
    """
    # Create a TaskUpdate with only the assigned_to field
    task_update = TaskUpdate(assigned_to=assigned_to)
    
    # Use the update_task function
    return await update_task(db, task_id, task_update, tenant_id, user_id)

async def search_tasks(
    db: Session, 
    tenant_id: str, 
    search_term: str,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[TaskModel]:
    """
    Search tasks by title or description.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        search_term: Search term
        project_id: Optional project filter
        status: Optional status filter
        assigned_to: Optional assignee filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of matching tasks
    """
    # Join with project to verify tenant
    query = db.query(TaskModel).join(
        ProjectModel, TaskModel.project_id == ProjectModel.id
    ).filter(
        ProjectModel.tenant_id == tenant_id,
        TaskModel.is_active == True,
        ProjectModel.is_active == True,
        (
            TaskModel.title.ilike(f"%{search_term}%") | 
            TaskModel.description.ilike(f"%{search_term}%")
        )
    )
    
    # Apply filters
    if project_id:
        query = query.filter(TaskModel.project_id == project_id)
        
    if status:
        query = query.filter(TaskModel.status == status)
        
    if assigned_to:
        query = query.filter(TaskModel.assigned_to == assigned_to)
    
    return query.offset(skip).limit(limit).all()