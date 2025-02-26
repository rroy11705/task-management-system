"""
Pydantic schemas for the Project Service.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: str
    tenant_id: str
    created_by: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str
    priority: int = 0
    assigned_to: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: str
    project_id: str
    board_id: Optional[str]
    created_by: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class BoardColumnBase(BaseModel):
    name: str
    order: int

class BoardColumnCreate(BoardColumnBase):
    pass

class BoardColumn(BoardColumnBase):
    id: str
    board_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class BoardBase(BaseModel):
    name: str
    description: Optional[str] = None

class BoardCreate(BoardBase):
    columns: List[BoardColumnCreate]

class Board(BoardBase):
    id: str
    project_id: str
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]
    columns: List[BoardColumn] = []

    class Config:
        orm_mode = True

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: str
    task_id: str
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True