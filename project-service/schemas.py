"""
Pydantic schemas for the Project Service.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
import re

from shared.constants import TaskStatus

class ProjectBase(BaseModel):
    """Base schema for Project."""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")

class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass

class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")

class Project(ProjectBase):
    """Schema for project response."""
    id: str
    tenant_id: str
    created_by: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class TaskBase(BaseModel):
    """Base schema for Task."""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task description")
    status: str = Field(TaskStatus.TODO, description="Task status")
    priority: int = Field(0, ge=0, le=5, description="Task priority (0-5)")
    assigned_to: Optional[str] = Field(None, description="User ID task is assigned to")

    @validator('status')
    def validate_status(cls, v):
        """Validate task status."""
        valid_statuses = [
            TaskStatus.TODO, 
            TaskStatus.IN_PROGRESS, 
            TaskStatus.REVIEW, 
            TaskStatus.DONE
        ]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    pass

class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task description")
    status: Optional[str] = Field(None, description="Task status")
    priority: Optional[int] = Field(None, ge=0, le=5, description="Task priority (0-5)")
    assigned_to: Optional[str] = Field(None, description="User ID task is assigned to")
    board_id: Optional[str] = Field(None, description="Board ID")

    @validator('status')
    def validate_status(cls, v):
        """Validate task status."""
        if v is None:
            return v
            
        valid_statuses = [
            TaskStatus.TODO, 
            TaskStatus.IN_PROGRESS, 
            TaskStatus.REVIEW, 
            TaskStatus.DONE
        ]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

class Task(TaskBase):
    """Schema for task response."""
    id: str
    project_id: str
    board_id: Optional[str] = None
    created_by: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class CommentBase(BaseModel):
    """Base schema for Comment."""
    content: str = Field(..., min_length=1, max_length=1000, description="Comment content")

class CommentCreate(CommentBase):
    """Schema for creating a new comment."""
    pass

class Comment(CommentBase):
    """Schema for comment response."""
    id: str
    task_id: str
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class BoardColumnBase(BaseModel):
    """Base schema for Board Column."""
    name: str = Field(..., min_length=1, max_length=50, description="Column name")
    order: Optional[int] = Field(None, ge=0, description="Column order")

class BoardColumnCreate(BoardColumnBase):
    """Schema for creating a new board column."""
    pass

class BoardColumn(BoardColumnBase):
    """Schema for board column response."""
    id: str
    board_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class BoardBase(BaseModel):
    """Base schema for Board."""
    name: str = Field(..., min_length=1, max_length=100, description="Board name")
    description: Optional[str] = Field(None, max_length=500, description="Board description")

class BoardCreate(BoardBase):
    """Schema for creating a new board."""
    columns: List[BoardColumnCreate] = Field([], description="Board columns")

class BoardUpdate(BaseModel):
    """Schema for updating a board."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Board name")
    description: Optional[str] = Field(None, max_length=500, description="Board description")

class Board(BoardBase):
    """Schema for board response."""
    id: str
    project_id: str
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    columns: List[BoardColumn] = []

    class Config:
        from_attributes = True
        populate_by_name = True

class ColumnOrder(BaseModel):
    """Schema for reordering columns."""
    column_orders: Dict[str, int] = Field(..., description="Map of column IDs to new orders")

class TaskAssignment(BaseModel):
    """Schema for assigning a task."""
    assigned_to: str = Field(..., description="User ID to assign the task to")

class TaskStatusUpdate(BaseModel):
    """Schema for updating a task status."""
    status: str = Field(..., description="New task status")

    @validator('status')
    def validate_status(cls, v):
        """Validate task status."""
        valid_statuses = [
            TaskStatus.TODO, 
            TaskStatus.IN_PROGRESS, 
            TaskStatus.REVIEW, 
            TaskStatus.DONE
        ]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

class BoardTasksResponse(BaseModel):
    """Schema for board tasks response."""
    columns: Dict[str, List[Task]] = Field(..., description="Tasks grouped by column")