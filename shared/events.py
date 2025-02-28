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