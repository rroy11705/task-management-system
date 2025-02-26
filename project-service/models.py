"""
Database models for the Project Service.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class ProjectModel(Base):
    """
    Project database model.
    """
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    tenant_id = Column(String, index=True, nullable=False)
    created_by = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tasks = relationship("TaskModel", back_populates="project")
    boards = relationship("BoardModel", back_populates="project")

class TaskModel(Base):
    """
    Task database model.
    """
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    assigned_to = Column(String)
    created_by = Column(String, nullable=False)
    board_id = Column(String, ForeignKey("boards.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("ProjectModel", back_populates="tasks")
    board = relationship("BoardModel", back_populates="tasks")
    comments = relationship("CommentModel", back_populates="task")

class BoardModel(Base):
    """
    Kanban board database model.
    """
    __tablename__ = "boards"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("ProjectModel", back_populates="boards")
    tasks = relationship("TaskModel", back_populates="board")
    columns = relationship("BoardColumnModel", back_populates="board")

class BoardColumnModel(Base):
    """
    Kanban board column database model.
    """
    __tablename__ = "board_columns"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    board_id = Column(String, ForeignKey("boards.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    board = relationship("BoardModel", back_populates="columns")

class CommentModel(Base):
    """
    Task comment database model.
    """
    __tablename__ = "comments"

    id = Column(String, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    task = relationship("TaskModel", back_populates="comments")