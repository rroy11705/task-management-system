"""
Event definitions for the User Management Service.
"""

from enum import Enum
from typing import Dict, Any, Optional, List

class EventType(str, Enum):
    """Event types for the User Management Service."""
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_DEACTIVATED = "user.deactivated"
    USER_REACTIVATED = "user.reactivated"
    USER_PERMISSION_CHANGED = "user.permission_changed"
    
    # Tenant events
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_DELETED = "tenant.deleted"

    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    
    # Task events
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_STATUS_CHANGED = "task.status_changed"
    TASK_ASSIGNED = "task.assigned"
    TASK_DELETED = "task.deleted"
    
    # Board events
    BOARD_CREATED = "board.created"
    BOARD_UPDATED = "board.updated"
    BOARD_DELETED = "board.deleted"
    
class Event:
    """Base class for all events."""
    def __init__(
        self,
        event_type: EventType,
        tenant_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.event_type = event_type
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "metadata": self.metadata
        }

class UserCreatedEvent(Event):
    """Event emitted when a user is created."""
    def __init__(self, tenant_id: str, user_id: str, email: str, username: str):
        super().__init__(EventType.USER_CREATED, tenant_id, user_id)
        self.metadata.update({
            "email": email,
            "username": username
        })

class UserUpdatedEvent(Event):
    """Event emitted when a user is updated."""
    def __init__(self, tenant_id: str, user_id: str, updated_fields: Dict[str, Any]):
        super().__init__(EventType.USER_UPDATED, tenant_id, user_id)
        self.metadata.update({
            "updated_fields": updated_fields
        })

class UserDeactivatedEvent(Event):
    """Event emitted when a user is deactivated."""
    def __init__(self, tenant_id: str, user_id: str, deactivated_by: Optional[str] = None):
        super().__init__(EventType.USER_DEACTIVATED, tenant_id, user_id)
        self.metadata.update({
            "deactivated_by": deactivated_by
        })

class UserReactivatedEvent(Event):
    """Event emitted when a user is reactivated."""
    def __init__(self, tenant_id: str, user_id: str, reactivated_by: Optional[str] = None):
        super().__init__(EventType.USER_REACTIVATED, tenant_id, user_id)
        self.metadata.update({
            "reactivated_by": reactivated_by
        })

class UserPermissionChangedEvent(Event):
    """Event emitted when a user's permissions change."""
    def __init__(
        self, 
        tenant_id: str, 
        user_id: str, 
        role_id: str, 
        role_name: str,
        permissions: List[str]
    ):
        super().__init__(EventType.USER_PERMISSION_CHANGED, tenant_id, user_id)
        self.metadata.update({
            "role_id": role_id,
            "role_name": role_name,
            "permissions": permissions
        })

class ProjectCreatedEvent(Event):
    """Event emitted when a project is created."""
    def __init__(self, tenant_id: str, user_id: str, project_id: str, project_name: str):
        super().__init__(EventType.PROJECT_CREATED, tenant_id, user_id)
        self.metadata.update({
            "project_id": project_id,
            "project_name": project_name
        })

class ProjectUpdatedEvent(Event):
    """Event emitted when a project is updated."""
    def __init__(self, tenant_id: str, user_id: str, project_id: str, updated_fields: Dict[str, Any]):
        super().__init__(EventType.PROJECT_UPDATED, tenant_id, user_id)
        self.metadata.update({
            "project_id": project_id,
            "updated_fields": updated_fields
        })

class ProjectDeletedEvent(Event):
    """Event emitted when a project is deleted."""
    def __init__(self, tenant_id: str, user_id: str, project_id: str, project_name: str):
        super().__init__(EventType.PROJECT_DELETED, tenant_id, user_id)
        self.metadata.update({
            "project_id": project_id,
            "project_name": project_name
        })

class TaskCreatedEvent(Event):
    """Event emitted when a task is created."""
    def __init__(self, tenant_id: str, user_id: str, task_id: str, project_id: str, task_title: str, assigned_to: Optional[str] = None):
        super().__init__(EventType.TASK_CREATED, tenant_id, user_id)
        self.metadata.update({
            "task_id": task_id,
            "project_id": project_id,
            "task_title": task_title,
            "assigned_to": assigned_to
        })

class TaskUpdatedEvent(Event):
    """Event emitted when a task is updated."""
    def __init__(self, tenant_id: str, user_id: str, task_id: str, project_id: str, updated_fields: Dict[str, Any]):
        super().__init__(EventType.TASK_UPDATED, tenant_id, user_id)
        self.metadata.update({
            "task_id": task_id,
            "project_id": project_id,
            "updated_fields": updated_fields
        })

class TaskStatusChangedEvent(Event):
    """Event emitted when a task status is changed."""
    def __init__(self, tenant_id: str, user_id: str, task_id: str, project_id: str, old_status: str, new_status: str):
        super().__init__(EventType.TASK_STATUS_CHANGED, tenant_id, user_id)
        self.metadata.update({
            "task_id": task_id,
            "project_id": project_id,
            "old_status": old_status,
            "new_status": new_status
        })

class TaskAssignedEvent(Event):
    """Event emitted when a task is assigned to a user."""
    def __init__(self, tenant_id: str, user_id: str, task_id: str, project_id: str, assigned_to: str):
        super().__init__(EventType.TASK_ASSIGNED, tenant_id, user_id)
        self.metadata.update({
            "task_id": task_id,
            "project_id": project_id,
            "assigned_to": assigned_to
        })

class TaskDeletedEvent(Event):
    """Event emitted when a task is deleted."""
    def __init__(self, tenant_id: str, user_id: str, task_id: str, project_id: str, task_title: str):
        super().__init__(EventType.TASK_DELETED, tenant_id, user_id)
        self.metadata.update({
            "task_id": task_id,
            "project_id": project_id,
            "task_title": task_title
        })

class BoardCreatedEvent(Event):
    """Event emitted when a board is created."""
    def __init__(self, tenant_id: str, user_id: str, board_id: str, project_id: str, board_name: str):
        super().__init__(EventType.BOARD_CREATED, tenant_id, user_id)
        self.metadata.update({
            "board_id": board_id,
            "project_id": project_id,
            "board_name": board_name
        })

class BoardUpdatedEvent(Event):
    """Event emitted when a board is updated."""
    def __init__(self, tenant_id: str, user_id: str, board_id: str, project_id: str, updated_fields: Dict[str, Any]):
        super().__init__(EventType.BOARD_UPDATED, tenant_id, user_id)
        self.metadata.update({
            "board_id": board_id,
            "project_id": project_id,
            "updated_fields": updated_fields
        })

class BoardDeletedEvent(Event):
    """Event emitted when a board is deleted."""
    def __init__(self, tenant_id: str, user_id: str, board_id: str, project_id: str, board_name: str):
        super().__init__(EventType.BOARD_DELETED, tenant_id, user_id)
        self.metadata.update({
            "board_id": board_id,
            "project_id": project_id,
            "board_name": board_name
        })
