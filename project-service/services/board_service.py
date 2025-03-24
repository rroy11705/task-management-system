"""
Service for managing Kanban boards.
"""

import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime

from models import BoardModel, BoardColumnModel, ProjectModel, TaskModel
from schemas import BoardCreate, BoardUpdate, Board, BoardColumnCreate
from events.rabbitmq_client import rabbitmq_client
from events.project_events import BoardCreatedEvent, BoardUpdatedEvent, BoardDeletedEvent

async def create_board(db: Session, board: BoardCreate, project_id: str, tenant_id: str, user_id: str) -> BoardModel:
    """
    Create a new Kanban board.
    
    Args:
        db: Database session
        board: Board data
        project_id: Project ID
        tenant_id: Tenant ID
        user_id: User ID
        
    Returns:
        The created board
        
    Raises:
        HTTPException: If project not found or board creation fails
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
    
    # Generate a unique ID for the board
    board_id = str(uuid.uuid4())
    
    # Create board in database
    db_board = BoardModel(
        id=board_id,
        name=board.name,
        description=board.description,
        project_id=project_id,
        created_by=user_id
    )
    
    try:
        db.add(db_board)
        db.flush()  # Flush to get the board ID without committing
        
        # Create board columns
        for idx, column in enumerate(board.columns):
            column_id = str(uuid.uuid4())
            db_column = BoardColumnModel(
                id=column_id,
                name=column.name,
                order=column.order if column.order is not None else idx,
                board_id=board_id
            )
            db.add(db_column)
        
        db.commit()
        db.refresh(db_board)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create board: {str(e)}"
        )
    
    # Publish BoardCreated event
    try:
        event = BoardCreatedEvent(
            tenant_id=tenant_id,
            user_id=user_id,
            board_id=board_id,
            project_id=project_id,
            board_name=board.name
        )
        await rabbitmq_client.publish_event(event.event_type, event.to_dict())
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Failed to publish BoardCreated event: {str(e)}")
    
    return db_board

async def get_board(db: Session, board_id: str, tenant_id: str) -> BoardModel:
    """
    Get board by ID.
    
    Args:
        db: Database session
        board_id: Board ID
        tenant_id: Tenant ID
        
    Returns:
        The board
        
    Raises:
        HTTPException: If board not found or doesn't belong to tenant
    """
    # Join with project to verify tenant
    board = db.query(BoardModel).join(
        ProjectModel, BoardModel.project_id == ProjectModel.id
    ).filter(
        BoardModel.id == board_id,
        ProjectModel.tenant_id == tenant_id,
        ProjectModel.is_active == True
    ).first()
    
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board with ID {board_id} not found"
        )
    
    return board

async def get_boards(db: Session, project_id: str, tenant_id: str) -> List[BoardModel]:
    """
    Get all boards for a project.
    
    Args:
        db: Database session
        project_id: Project ID
        tenant_id: Tenant ID
        
    Returns:
        List of boards
        
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
    
    return db.query(BoardModel).filter(BoardModel.project_id == project_id).all()

async def update_board(
    db: Session, 
    board_id: str, 
    board_update: BoardUpdate, 
    tenant_id: str, 
    user_id: str
) -> BoardModel:
    """
    Update a board.
    
    Args:
        db: Database session
        board_id: Board ID
        board_update: Board update data
        tenant_id: Tenant ID
        user_id: User ID
        
    Returns:
        The updated board
        
    Raises:
        HTTPException: If board not found or update fails
    """
    # Get board
    board = await get_board(db, board_id, tenant_id)
    
    # Track updated fields for event
    updated_fields = {}
    
    # Update fields
    if board_update.name is not None and board_update.name != board.name:
        board.name = board_update.name
        updated_fields["name"] = board_update.name
    
    if board_update.description is not None and board_update.description != board.description:
        board.description = board_update.description
        updated_fields["description"] = board_update.description
    
    # Only commit if there are changes
    if updated_fields:
        try:
            board.updated_at = datetime.now()
            db.commit()
            db.refresh(board)
            
            # Publish BoardUpdated event
            try:
                event = BoardUpdatedEvent(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    board_id=board_id,
                    project_id=board.project_id,
                    updated_fields=updated_fields
                )
                await rabbitmq_client.publish_event(event.event_type, event.to_dict())
            except Exception as e:
                # Log the error but don't fail the request
                print(f"Failed to publish BoardUpdated event: {str(e)}")
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update board: {str(e)}"
            )
    
    return board

async def delete_board(db: Session, board_id: str, tenant_id: str, user_id: str) -> BoardModel:
    """
    Delete a board.
    
    Args:
        db: Database session
        board_id: Board ID
        tenant_id: Tenant ID
        user_id: User ID
        
    Returns:
        The deleted board
        
    Raises:
        HTTPException: If board not found or deletion fails
    """
    # Get board
    board = await get_board(db, board_id, tenant_id)
    
    # Store board details for event
    board_name = board.name
    project_id = board.project_id
    
    try:
        # Delete associated columns
        db.query(BoardColumnModel).filter(BoardColumnModel.board_id == board_id).delete()
        
        # Unlink tasks from this board
        db.query(TaskModel).filter(TaskModel.board_id == board_id).update({
            TaskModel.board_id: None
        })
        
        # Delete the board
        db.delete(board)
        db.commit()
        
        # Publish BoardDeleted event
        try:
            event = BoardDeletedEvent(
                tenant_id=tenant_id,
                user_id=user_id,
                board_id=board_id,
                project_id=project_id,
                board_name=board_name
            )
            await rabbitmq_client.publish_event(event.event_type, event.to_dict())
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Failed to publish BoardDeleted event: {str(e)}")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete board: {str(e)}"
        )
    
    return board

async def add_column(
    db: Session, 
    board_id: str, 
    column: BoardColumnCreate, 
    tenant_id: str
) -> BoardColumnModel:
    """
    Add a column to a board.
    
    Args:
        db: Database session
        board_id: Board ID
        column: Column data
        tenant_id: Tenant ID
        
    Returns:
        The created column
        
    Raises:
        HTTPException: If board not found or column creation fails
    """
    # Get board
    board = await get_board(db, board_id, tenant_id)
    
    # Generate a unique ID for the column
    column_id = str(uuid.uuid4())
    
    # Get highest order if not specified
    if column.order is None:
        max_order = db.query(BoardColumnModel).filter(
            BoardColumnModel.board_id == board_id
        ).with_entities(
            BoardColumnModel.order
        ).order_by(
            BoardColumnModel.order.desc()
        ).first()
        
        next_order = (max_order[0] + 1) if max_order else 0
    else:
        next_order = column.order
    
    # Create column
    db_column = BoardColumnModel(
        id=column_id,
        name=column.name,
        order=next_order,
        board_id=board_id
    )
    
    try:
        db.add(db_column)
        db.commit()
        db.refresh(db_column)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create column: {str(e)}"
        )
    
    return db_column

async def update_column(
    db: Session, 
    column_id: str, 
    column_update: BoardColumnCreate, 
    tenant_id: str
) -> BoardColumnModel:
    """
    Update a board column.
    
    Args:
        db: Database session
        column_id: Column ID
        column_update: Column update data
        tenant_id: Tenant ID
        
    Returns:
        The updated column
        
    Raises:
        HTTPException: If column not found or update fails
    """
    # Get column and verify tenant association
    column = db.query(BoardColumnModel).join(
        BoardModel, BoardColumnModel.board_id == BoardModel.id
    ).join(
        ProjectModel, BoardModel.project_id == ProjectModel.id
    ).filter(
        BoardColumnModel.id == column_id,
        ProjectModel.tenant_id == tenant_id
    ).first()
    
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with ID {column_id} not found"
        )
    
    # Update fields
    if column_update.name is not None:
        column.name = column_update.name
    
    if column_update.order is not None:
        column.order = column_update.order
    
    try:
        db.commit()
        db.refresh(column)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update column: {str(e)}"
        )
    
    return column

async def delete_column(db: Session, column_id: str, tenant_id: str) -> BoardColumnModel:
    """
    Delete a board column.
    
    Args:
        db: Database session
        column_id: Column ID
        tenant_id: Tenant ID
        
    Returns:
        The deleted column
        
    Raises:
        HTTPException: If column not found or deletion fails
    """
    # Get column and verify tenant association
    column = db.query(BoardColumnModel).join(
        BoardModel, BoardColumnModel.board_id == BoardModel.id
    ).join(
        ProjectModel, BoardModel.project_id == ProjectModel.id
    ).filter(
        BoardColumnModel.id == column_id,
        ProjectModel.tenant_id == tenant_id
    ).first()
    
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with ID {column_id} not found"
        )
    
    try:
        # Unlink tasks from this column (assuming column status maps to task status)
        db.query(TaskModel).filter(
            TaskModel.board_id == column.board_id,
            TaskModel.status == column.name
        ).update({
            TaskModel.status: "todo"  # Default fallback status
        })
        
        # Delete the column
        db.delete(column)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete column: {str(e)}"
        )
    
    return column

async def reorder_columns(
    db: Session, 
    board_id: str, 
    column_orders: Dict[str, int], 
    tenant_id: str
) -> List[BoardColumnModel]:
    """
    Reorder columns in a board.
    
    Args:
        db: Database session
        board_id: Board ID
        column_orders: Dict mapping column IDs to new orders
        tenant_id: Tenant ID
        
    Returns:
        List of updated columns
        
    Raises:
        HTTPException: If board not found or reordering fails
    """
    # Get board
    board = await get_board(db, board_id, tenant_id)
    
    # Get columns
    columns = db.query(BoardColumnModel).filter(
        BoardColumnModel.board_id == board_id
    ).all()
    
    # Update orders
    for column in columns:
        if column.id in column_orders:
            column.order = column_orders[column.id]
    
    try:
        db.commit()
        # Refresh columns
        columns = db.query(BoardColumnModel).filter(
            BoardColumnModel.board_id == board_id
        ).order_by(
            BoardColumnModel.order
        ).all()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder columns: {str(e)}"
        )
    
    return columns

async def get_board_tasks(
    db: Session, 
    board_id: str, 
    tenant_id: str, 
    column_id: Optional[str] = None
) -> Dict[str, List[TaskModel]]:
    """
    Get tasks for a board, optionally filtered by column.
    
    Args:
        db: Database session
        board_id: Board ID
        tenant_id: Tenant ID
        column_id: Optional column ID to filter by
        
    Returns:
        Dictionary mapping column names to lists of tasks
        
    Raises:
        HTTPException: If board not found
    """
    # Get board
    board = await get_board(db, board_id, tenant_id)
    
    # Get columns
    columns = db.query(BoardColumnModel).filter(
        BoardColumnModel.board_id == board_id
    ).order_by(
        BoardColumnModel.order
    ).all()
    
    if column_id:
        # Filter columns
        columns = [col for col in columns if col.id == column_id]
        
        if not columns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Column with ID {column_id} not found in board"
            )
    
    # Get tasks by column
    result = {}
    for column in columns:
        tasks = db.query(TaskModel).filter(
            TaskModel.board_id == board_id,
            TaskModel.status == column.name,
            TaskModel.is_active == True
        ).all()
        
        result[column.name] = tasks
    
    return result