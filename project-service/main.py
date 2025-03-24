"""
Project Service for the Task Management System.
Manages projects, tasks, and Kanban boards.
"""

import os
from fastapi import FastAPI, Depends, HTTPException, status, Request, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from database import get_db_for_tenant
from models import ProjectModel, TaskModel, BoardModel, BoardColumnModel, CommentModel
from schemas import (
    ProjectCreate, Project, ProjectUpdate,
    TaskCreate, Task, TaskUpdate, TaskStatusUpdate, TaskAssignment,
    BoardCreate, Board, BoardUpdate, BoardColumn, BoardColumnCreate, ColumnOrder,
    CommentCreate, Comment,
    BoardTasksResponse
)
from services import project_service, task_service, board_service
from events.rabbitmq_client import rabbitmq_client
from auth_handler import (
    get_current_user, extract_tenant_id_from_token,
    require_create_project, require_update_project, require_delete_project,
    require_create_task, require_update_task, require_delete_task, require_assign_task
)
from shared.constants import TaskStatus

# Initialize FastAPI app
app = FastAPI(
    title="Task Management System - Project Service",
    description="Service for managing projects, tasks, and Kanban boards",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup."""
    print("Project Service starting up")
    try:
        await rabbitmq_client.connect()
    except Exception as e:
        print(f"Warning: Failed to connect to RabbitMQ: {str(e)}")
        print("The service will attempt to reconnect when needed.")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    print("Project Service shutting down")
    if rabbitmq_client._connected:
        await rabbitmq_client.close()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Project Service", "status": "healthy"}

# Project endpoints
@app.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_create_project),
    db: Session = Depends(get_db_for_tenant)
):
    """
    Create a new project.
    
    Requires CREATE_PROJECT permission.
    """
    return await project_service.create_project(db, project, tenant_id, user["user_id"])

@app.get("/projects", response_model=List[Project])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Get all projects for the tenant."""
    return await project_service.get_projects(db, tenant_id, skip, limit)

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Get project by ID."""
    return await project_service.get_project(db, project_id, tenant_id)

@app.put("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_update_project),
    db: Session = Depends(get_db_for_tenant)
):
    """
    Update a project.
    
    Requires UPDATE_PROJECT permission.
    """
    return await project_service.update_project(db, project_id, project_update, tenant_id, user["user_id"])

@app.delete("/projects/{project_id}", response_model=Project)
async def delete_project(
    project_id: str,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_delete_project),
    db: Session = Depends(get_db_for_tenant)
):
    """
    Delete a project (soft delete).
    
    Requires DELETE_PROJECT permission.
    """
    return await project_service.delete_project(db, project_id, tenant_id, user["user_id"])

@app.get("/projects/search/{search_term}", response_model=List[Project])
async def search_projects(
    search_term: str,
    skip: int = 0,
    limit: int = 100,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Search projects by name or description."""
    return await project_service.search_projects(db, tenant_id, search_term, skip, limit)

# Task endpoints
@app.post("/projects/{project_id}/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: str,
    task: TaskCreate,
    board_id: Optional[str] = None,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_create_task),
    db: Session = Depends(get_db_for_tenant)
):
    """
    Create a new task in a project.
    
    Requires CREATE_TASK permission.
    """
    return await task_service.create_task(db, task, project_id, tenant_id, user["user_id"], board_id)

@app.get("/projects/{project_id}/tasks", response_model=List[Task])
async def get_tasks(
    project_id: str,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Get all tasks for a project with optional filtering."""
    return await task_service.get_tasks(db, project_id, tenant_id, status, assigned_to, skip, limit)

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Get task by ID."""
    return await task_service.get_task(db, task_id, tenant_id)

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_update_task),
    db: Session = Depends(get_db_for_tenant)
):
    """
    Update a task.
    
    Requires UPDATE_TASK permission.
    """
    return await task_service.update_task(db, task_id, task_update, tenant_id, user["user_id"])

@app.delete("/tasks/{task_id}", response_model=Task)
async def delete_task(
    task_id: str,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_delete_task),
    db: Session = Depends(get_db_for_tenant)
):
    """
    Delete a task (soft delete).
    
    Requires DELETE_TASK permission.
    """
    return await task_service.delete_task(db, task_id, tenant_id, user["user_id"])

@app.put("/tasks/{task_id}/status", response_model=Task)
async def update_task_status(
    task_id: str,
    status_update: TaskStatusUpdate,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_update_task),
    db: Session = Depends(get_db_for_tenant)
):
    """
    Update task status.
    
    Requires UPDATE_TASK permission.
    """
    return await task_service.update_task_status(db, task_id, status_update.status, tenant_id, user["user_id"])

@app.put("/tasks/{task_id}/assign", response_model=Task)
async def assign_task(
    task_id: str,
    assignment: TaskAssignment,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_assign_task),
    db: Session = Depends(get_db_for_tenant)
):
    """
    Assign a task to a user.
    
    Requires ASSIGN_TASK permission.
    """
    return await task_service.assign_task(db, task_id, assignment.assigned_to, tenant_id, user["user_id"])

@app.get("/tasks/search/{search_term}", response_model=List[Task])
async def search_tasks(
    search_term: str,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Search tasks by title or description with optional filtering."""
    return await task_service.search_tasks(
        db, tenant_id, search_term, project_id, status, assigned_to, skip, limit
    )

# Board endpoints
@app.post("/projects/{project_id}/boards", response_model=Board, status_code=status.HTTP_201_CREATED)
async def create_board(
    project_id: str,
    board: BoardCreate,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_update_project),  # Creating a board requires project update permission
    db: Session = Depends(get_db_for_tenant)
):
    """
    Create a new Kanban board for a project.
    
    Requires UPDATE_PROJECT permission.
    """
    # If no columns are provided, create default columns
    if not board.columns:
        board.columns = [
            BoardColumnCreate(name=TaskStatus.TODO, order=0),
            BoardColumnCreate(name=TaskStatus.IN_PROGRESS, order=1),
            BoardColumnCreate(name=TaskStatus.REVIEW, order=2),
            BoardColumnCreate(name=TaskStatus.DONE, order=3)
        ]
    
    return await board_service.create_board(db, board, project_id, tenant_id, user["user_id"])

@app.get("/projects/{project_id}/boards", response_model=List[Board])
async def get_boards(
    project_id: str,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Get all Kanban boards for a project."""
    return await board_service.get_boards(db, project_id, tenant_id)

@app.get("/boards/{board_id}", response_model=Board)
async def get_board(
    board_id: str,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Get board by ID."""
    return await board_service.get_board(db, board_id, tenant_id)

@app.put("/boards/{board_id}", response_model=Board)
async def update_board(
    board_id: str,
    board_update: BoardUpdate,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_update_project),  # Updating a board requires project update permission
    db: Session = Depends(get_db_for_tenant)
):
    """
    Update a board.
    
    Requires UPDATE_PROJECT permission.
    """
    return await board_service.update_board(db, board_id, board_update, tenant_id, user["user_id"])

@app.delete("/boards/{board_id}", response_model=Board)
async def delete_board(
    board_id: str,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_update_project),  # Deleting a board requires project update permission
    db: Session = Depends(get_db_for_tenant)
):
    """
    Delete a board.
    
    Requires UPDATE_PROJECT permission.
    """
    return await board_service.delete_board(db, board_id, tenant_id, user["user_id"])

@app.post("/boards/{board_id}/columns", response_model=BoardColumn)
async def add_column(
    board_id: str,
    column: BoardColumnCreate,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_update_project),  # Adding a column requires project update permission
    db: Session = Depends(get_db_for_tenant)
):
    """
    Add a column to a board.
    
    Requires UPDATE_PROJECT permission.
    """
    return await board_service.add_column(db, board_id, column, tenant_id)

@app.put("/columns/{column_id}", response_model=BoardColumn)
async def update_column(
    column_id: str,
    column_update: BoardColumnCreate,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_update_project),  # Updating a column requires project update permission
    db: Session = Depends(get_db_for_tenant)
):
    """
    Update a board column.
    
    Requires UPDATE_PROJECT permission.
    """
    return await board_service.update_column(db, column_id, column_update, tenant_id)

@app.delete("/columns/{column_id}", response_model=BoardColumn)
async def delete_column(
    column_id: str,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_update_project),  # Deleting a column requires project update permission
    db: Session = Depends(get_db_for_tenant)
):
    """
    Delete a board column.
    
    Requires UPDATE_PROJECT permission.
    """
    return await board_service.delete_column(db, column_id, tenant_id)

@app.put("/boards/{board_id}/columns/reorder", response_model=List[BoardColumn])
async def reorder_columns(
    board_id: str,
    column_orders: ColumnOrder,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(require_update_project),  # Reordering columns requires project update permission
    db: Session = Depends(get_db_for_tenant)
):
    """
    Reorder columns in a board.
    
    Requires UPDATE_PROJECT permission.
    """
    return await board_service.reorder_columns(db, board_id, column_orders.column_orders, tenant_id)

@app.get("/boards/{board_id}/tasks", response_model=BoardTasksResponse)
async def get_board_tasks(
    board_id: str,
    column_id: Optional[str] = None,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Get tasks for a board, optionally filtered by column."""
    tasks_by_column = await board_service.get_board_tasks(db, board_id, tenant_id, column_id)
    return BoardTasksResponse(columns=tasks_by_column)

# Comment endpoints
@app.post("/tasks/{task_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: str,
    comment: CommentCreate,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Create a new comment on a task."""
    # First, check if task exists and belongs to tenant
    task = await task_service.get_task(db, task_id, tenant_id)
    
    # Generate a unique ID for the comment
    comment_id = str(uuid.uuid4())
    
    # Create comment in database
    db_comment = CommentModel(
        id=comment_id,
        content=comment.content,
        task_id=task_id,
        created_by=user["user_id"]
    )
    
    try:
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment: {str(e)}"
        )
    
    return db_comment

@app.get("/tasks/{task_id}/comments", response_model=List[Comment])
async def get_comments(
    task_id: str,
    tenant_id: str = Depends(extract_tenant_id_from_token),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_for_tenant)
):
    """Get all comments for a task."""
    # First, check if task exists and belongs to tenant
    task = await task_service.get_task(db, task_id, tenant_id)
    
    # Get comments
    comments = db.query(CommentModel).filter(
        CommentModel.task_id == task_id
    ).order_by(
        CommentModel.created_at
    ).all()
    
    return comments

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8003")),
        reload=os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    )