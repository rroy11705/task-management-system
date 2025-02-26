"""
Service for managing tasks.
"""

import uuid
from sqlalchemy.orm import Session

from models import TaskModel, ProjectModel
from schemas import TaskCreate, Task
from events.rabbitmq_client import rabbitmq_client

def create_task(db: Session, task: TaskCreate, project_id: str, tenant_id: str, user_id: str):
    """
    Create a new task.
    """
    # TODO: Implement task creation logic
    # 1. Check if project exists and belongs to tenant
    # 2. Generate a unique ID for the task
    # 3. Create task in database
    # 4. Publish TaskCreated event
    pass

def get_task(db: Session, task_id: str, tenant_id: str):
    """
    Get task by ID.
    """
    # TODO: Implement get task logic
    # 1. Get task from database
    # 2. Check if task exists and belongs to tenant
    pass

def get_tasks(db: Session, project_id: str, tenant_id: str):
    """
    Get all tasks for a project.
    """
    # TODO: Implement get tasks logic
    # 1. Check if project exists and belongs to tenant
    # 2. Get all tasks from database for project
    pass

def update_task_status(db: Session, task_id: str, status: str, tenant_id: str, user_id: str):
    """
    Update task status.
    """
    # TODO: Implement update task status logic
    # 1. Get task from database
    # 2. Check if task exists and belongs to tenant
    # 3. Update task status
    # 4. Publish TaskStatusChanged event
    pass