"""
Authentication and authorization handler for the Project Service.
"""

import os
import jwt
from typing import Dict, Any, List, Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from shared.constants import Permission

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key_here")
ALGORITHM = "HS256"

# Security scheme
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify JWT token and extract user information.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        The decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token_payload: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Get current user from token payload.
    
    Args:
        token_payload: Decoded token payload
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user ID is missing from token
    """
    user_id = token_payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: user ID missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract tenant ID
    tenant_id = token_payload.get("tenant_id")
    
    # Extract roles
    roles = token_payload.get("roles", [])
    
    # Extract permissions
    permissions = token_payload.get("permissions", [])
    
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "roles": roles,
        "permissions": permissions
    }

def require_permission(required_permission: str):
    """
    Dependency function to check if user has a specific permission.
    
    Args:
        required_permission: The permission required to access the endpoint
        
    Returns:
        Dependency function
    """
    async def check_permission(user: Dict[str, Any] = Depends(get_current_user)):
        # Extract permissions from user data
        permissions = user.get("permissions", [])
        
        # Check if user has required permission
        if required_permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required_permission} required"
            )
        
        return user
    
    return check_permission

def has_permission(user: Dict[str, Any], permission: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user: User information
        permission: The permission to check
        
    Returns:
        True if user has the permission, False otherwise
    """
    # Extract permissions from user data
    permissions = user.get("permissions", [])
    
    # Check if user has permission
    return permission in permissions

async def extract_tenant_id_from_token(token_payload: Dict[str, Any] = Depends(verify_token)) -> str:
    """
    Extract tenant ID from token payload.
    
    Args:
        token_payload: Decoded token payload
        
    Returns:
        Tenant ID
        
    Raises:
        HTTPException: If tenant ID is missing from token
    """
    tenant_id = token_payload.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID not found in token",
        )
    
    return tenant_id

# Permission check functions for specific operations
require_create_project = require_permission(Permission.CREATE_PROJECT)
require_update_project = require_permission(Permission.UPDATE_PROJECT)
require_delete_project = require_permission(Permission.DELETE_PROJECT)
require_create_task = require_permission(Permission.CREATE_TASK)
require_update_task = require_permission(Permission.UPDATE_TASK)
require_delete_task = require_permission(Permission.DELETE_TASK)
require_assign_task = require_permission(Permission.ASSIGN_TASK)