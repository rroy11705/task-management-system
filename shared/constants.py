"""
Shared constants for the Task Management System.
"""

# Task statuses
class TaskStatus:
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

# User roles
class UserRole:
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"

# Permissions
class Permission:
    # Project permissions
    CREATE_PROJECT = "create_project"
    UPDATE_PROJECT = "update_project"
    DELETE_PROJECT = "delete_project"
    
    # Task permissions
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    ASSIGN_TASK = "assign_task"
    
    # User permissions
    MANAGE_USERS = "manage_users"
    ASSIGN_ROLES = "assign_roles"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view_analytics"

# Service URLs
class ServiceURL:
    API_GATEWAY = "http://api-gateway:8000"
    TENANT_RESOLVER = "http://tenant-resolver:8001"
    USER_MANAGEMENT = "http://user-management:8002"
    PROJECT_SERVICE = "http://project-service:8003"
    URL_SHORTENER = "http://url-shortener:8004"
    ANALYTICS = "http://analytics:8005"