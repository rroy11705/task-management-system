"""
Shared event definitions for the Task Management System.
"""

from enum import Enum
from typing import Dict, Any, Optional

class EventType(str, Enum):
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_PERMISSION_CHANGED = "user.permission_changed"
    
    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_USER_ADDED = "project.user_added"
    
    # Task events
    TASK_CREATED = "task.created"
    TASK_STATUS_CHANGED = "task.status_changed"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMMENT_ADDED = "task.comment_added"
    
    # URL events
    URL_CREATED = "url.created"
    URL_ACCESSED = "url.accessed"
    URL_EXPIRED = "url.expired"

class Event:
    """
    Base class for all events.
    """
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
        """
        Convert event to dictionary for serialization.
        """
        return {
            "event_type": self.event_type,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "metadata": self.metadata
        }

# Example event class implementations
class UserCreatedEvent(Event):
    """
    Event emitted when a user is created.
    """
    def __init__(self, tenant_id: str, user_id: str, email: str, username: str):
        super().__init__(EventType.USER_CREATED, tenant_id, user_id)
        self.metadata.update({
            "email": email,
            "username": username
        })

class TaskStatusChangedEvent(Event):
    """
    Event emitted when a task status changes.
    """
    def __init__(self, tenant_id: str, user_id: str, task_id: str, project_id: str, old_status: str, new_status: str):
        super().__init__(EventType.TASK_STATUS_CHANGED, tenant_id, user_id)
        self.metadata.update({
            "task_id": task_id,
            "project_id": project_id,
            "old_status": old_status,
            "new_status": new_status
        })

class URLAccessedEvent(Event):
    """
    Event emitted when a shortened URL is accessed.
    """
    def __init__(self, tenant_id: str, url_id: str, short_code: str, user_id: Optional[str] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None, referrer: Optional[str] = None):
        super().__init__(EventType.URL_ACCESSED, tenant_id, user_id)
        self.metadata.update({
            "url_id": url_id,
            "short_code": short_code,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "referrer": referrer
        })