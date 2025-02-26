"""
Shared exceptions for the Task Management System.
"""

class TenantNotFoundError(Exception):
    """
    Exception raised when a tenant is not found.
    """
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.message = f"Tenant with ID {tenant_id} not found"
        super().__init__(self.message)

class UserNotFoundError(Exception):
    """
    Exception raised when a user is not found.
    """
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.message = f"User with ID {user_id} not found"
        super().__init__(self.message)

class ProjectNotFoundError(Exception):
    """
    Exception raised when a project is not found.
    """
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.message = f"Project with ID {project_id} not found"
        super().__init__(self.message)

class TaskNotFoundError(Exception):
    """
    Exception raised when a task is not found.
    """
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.message = f"Task with ID {task_id} not found"
        super().__init__(self.message)

class URLNotFoundError(Exception):
    """
    Exception raised when a URL is not found.
    """
    def __init__(self, short_code: str):
        self.short_code = short_code
        self.message = f"URL with short code {short_code} not found"
        super().__init__(self.message)

class PermissionDeniedError(Exception):
    """
    Exception raised when a user does not have permission to perform an action.
    """
    def __init__(self, user_id: str, action: str):
        self.user_id = user_id
        self.action = action
        self.message = f"User with ID {user_id} does not have permission to {action}"
        super().__init__(self.message)

class URLExpiredError(Exception):
    """
    Exception raised when a URL has expired.
    """
    def __init__(self, short_code: str):
        self.short_code = short_code
        self.message = f"URL with short code {short_code} has expired"
        super().__init__(self.message)

class PasswordRequiredError(Exception):
    """
    Exception raised when a password is required to access a URL.
    """
    def __init__(self, short_code: str):
        self.short_code = short_code
        self.message = f"Password required to access URL with short code {short_code}"
        super().__init__(self.message)

class IncorrectPasswordError(Exception):
    """
    Exception raised when an incorrect password is provided for a URL.
    """
    def __init__(self, short_code: str):
        self.short_code = short_code
        self.message = f"Incorrect password for URL with short code {short_code}"
        super().__init__(self.message)