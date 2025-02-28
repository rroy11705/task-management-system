"""
User Management Service for the Task Management System.
Handles authentication, authorization, and user management.
"""

import os
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional

from database import get_db, init_db
from models import UserModel, RoleModel, PermissionModel
from schemas import (
    UserCreate, UserUpdate, User, Token, 
    RoleCreate, Role, PermissionCreate, Permission,
    UserRole, RolePermission
)
from services import auth_service, user_service, role_service
from events.rabbitmq_client import rabbitmq_client
from shared.constants import UserRole as UserRoleConstants
from shared.constants import Permission as PermissionConstants

# Initialize FastAPI app
app = FastAPI(
    title="Task Management System - User Management Service",
    description="Service for authentication, authorization, and user management",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT configuration
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    print("Initializing User Management Service...")
    
    # Initialize database
    init_db()
    
    # Try to connect to RabbitMQ
    try:
        await rabbitmq_client.connect()
    except Exception as e:
        print(f"Warning: Failed to connect to RabbitMQ: {str(e)}")
        print("The service will attempt to reconnect when needed.")
    
    # Bootstrap default roles and permissions if none exist
    async def _bootstrap_defaults():
        db = next(get_db())
        
        # Check if we need to bootstrap
        roles_count = db.query(RoleModel).count()
        perms_count = db.query(PermissionModel).count()
        
        if roles_count == 0 and perms_count == 0:
            print("Bootstrapping default roles and permissions...")
            
            # Create default permissions
            permissions = {}
            
            # Project permissions
            permissions["create_project"] = await role_service.create_permission(
                db, PermissionCreate(name=PermissionConstants.CREATE_PROJECT, description="Can create new projects")
            )
            permissions["update_project"] = await role_service.create_permission(
                db, PermissionCreate(name=PermissionConstants.UPDATE_PROJECT, description="Can update projects")
            )
            permissions["delete_project"] = await role_service.create_permission(
                db, PermissionCreate(name=PermissionConstants.DELETE_PROJECT, description="Can delete projects")
            )
            
            # Task permissions
            permissions["create_task"] = await role_service.create_permission(
                db, PermissionCreate(name=PermissionConstants.CREATE_TASK, description="Can create new tasks")
            )
            permissions["update_task"] = await role_service.create_permission(
                db, PermissionCreate(name=PermissionConstants.UPDATE_TASK, description="Can update tasks")
            )
            permissions["delete_task"] = await role_service.create_permission(
                db, PermissionCreate(name=PermissionConstants.DELETE_TASK, description="Can delete tasks")
            )
            permissions["assign_task"] = await role_service.create_permission(
                db, PermissionCreate(name=PermissionConstants.ASSIGN_TASK, description="Can assign tasks")
            )
            
            # User management permissions
            permissions["manage_users"] = await role_service.create_permission(
                db, PermissionCreate(name=PermissionConstants.MANAGE_USERS, description="Can manage users")
            )
            permissions["assign_roles"] = await role_service.create_permission(
                db, PermissionCreate(name=PermissionConstants.ASSIGN_ROLES, description="Can assign roles")
            )
            
            # Analytics permissions
            permissions["view_analytics"] = await role_service.create_permission(
                db, PermissionCreate(name=PermissionConstants.VIEW_ANALYTICS, description="Can view analytics")
            )
            
            # Create default roles
            roles = {}
            
            # Admin role
            roles["admin"] = await role_service.create_role(
                db, RoleCreate(name=UserRoleConstants.ADMIN, description="Administrator with full access")
            )
            
            # Manager role
            roles["manager"] = await role_service.create_role(
                db, RoleCreate(name=UserRoleConstants.MANAGER, description="Project manager")
            )
            
            # Member role
            roles["member"] = await role_service.create_role(
                db, RoleCreate(name=UserRoleConstants.MEMBER, description="Team member")
            )
            
            # Viewer role
            roles["viewer"] = await role_service.create_role(
                db, RoleCreate(name=UserRoleConstants.VIEWER, description="Read-only user")
            )
            
            # Assign permissions to roles
            
            # Admin: all permissions
            for perm in permissions.values():
                await role_service.assign_permission_to_role(db, roles["admin"].id, perm.id)
            
            # Manager: all except user management
            manager_perms = [
                "create_project", "update_project", "delete_project",
                "create_task", "update_task", "delete_task", "assign_task",
                "view_analytics"
            ]
            for perm_name in manager_perms:
                await role_service.assign_permission_to_role(db, roles["manager"].id, permissions[perm_name].id)
            
            # Member: create/update tasks, create projects
            member_perms = [
                "create_project", "update_project",
                "create_task", "update_task", "assign_task"
            ]
            for perm_name in member_perms:
                await role_service.assign_permission_to_role(db, roles["member"].id, permissions[perm_name].id)
            
            # Viewer: no permissions (read-only)
            
            print("Successfully bootstrapped default roles and permissions")
    
    await _bootstrap_defaults()
    print("User Management Service initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    try:
        if rabbitmq_client._connected:
            await rabbitmq_client.close()
    except Exception as e:
        print(f"Error during shutdown: {str(e)}")

# Root endpoint for health check
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "User Management Service",
        "status": "healthy"
    }

# Authentication endpoints
@app.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint.
    
    Authenticates user with username/email and password, returns JWT token.
    """
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Include user ID and tenant ID in token payload
    token_data = {
        "sub": user.id,
        "tenant_id": user.tenant_id
    }
    
    access_token = auth_service.create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    # Get user roles
    role_names = [role.name for role in user.roles]
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "roles": role_names
    }

@app.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Creates a new user in the database and returns the user data.
    """
    return await user_service.create_user(db, user)

# User management endpoints
@app.get("/users/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(auth_service.get_current_active_user)
):
    """
    Get current user's information.
    
    Returns the authenticated user's data.
    """
    return current_user

@app.get("/users/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.check_permission(PermissionConstants.MANAGE_USERS))
):
    """
    Get user by ID.
    
    Returns a user's data by their ID. Requires MANAGE_USERS permission.
    """
    user = user_service.get_user(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return user

@app.get("/users", response_model=List[User])
async def get_users(
    tenant_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.check_permission(PermissionConstants.MANAGE_USERS))
):
    """
    Get all users.
    
    Returns all users, optionally filtered by tenant ID. Requires MANAGE_USERS permission.
    """
    # If tenant_id is provided, filter by it
    if tenant_id:
        return user_service.get_users_by_tenant(db, tenant_id, skip, limit)
    
    # Otherwise, return users from the same tenant as the current user
    return user_service.get_users_by_tenant(db, current_user.tenant_id, skip, limit)

@app.put("/users/{user_id}", response_model=User)
async def update_user_by_id(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.get_current_active_user)
):
    """
    Update user by ID.
    
    Updates a user's data by their ID. Users can update their own data,
    but only users with MANAGE_USERS permission can update other users.
    """
    # Check if user is updating their own data or has manage_users permission
    if user_id != current_user.id and not auth_service.has_permission(current_user, PermissionConstants.MANAGE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update other users"
        )
    
    updated_user = await user_service.update_user(db, user_id, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return updated_user

@app.put("/users/{user_id}/deactivate", response_model=User)
async def deactivate_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.check_permission(PermissionConstants.MANAGE_USERS))
):
    """
    Deactivate user by ID.
    
    Deactivates a user by their ID. Requires MANAGE_USERS permission.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    deactivated_user = await user_service.deactivate_user(db, user_id)
    
    if not deactivated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return deactivated_user

@app.put("/users/{user_id}/reactivate", response_model=User)
async def reactivate_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.check_permission(PermissionConstants.MANAGE_USERS))
):
    """
    Reactivate user by ID.
    
    Reactivates a user by their ID. Requires MANAGE_USERS permission.
    """
    reactivated_user = await user_service.reactivate_user(db, user_id)
    
    if not reactivated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return reactivated_user

# Role and permission endpoints
@app.get("/roles", response_model=List[Role])
async def get_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.get_current_active_user)
):
    """
    Get all roles.
    
    Returns all roles in the system.
    """
    return role_service.get_roles(db, skip, limit)

@app.post("/roles", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.check_permission(PermissionConstants.ASSIGN_ROLES))
):
    """
    Create a new role.
    
    Creates a new role in the system. Requires ASSIGN_ROLES permission.
    """
    return await role_service.create_role(db, role)

@app.get("/permissions", response_model=List[Permission])
async def get_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.get_current_active_user)
):
    """
    Get all permissions.
    
    Returns all permissions in the system.
    """
    return role_service.get_permissions(db, skip, limit)

@app.post("/permissions", response_model=Permission, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.check_permission(PermissionConstants.ASSIGN_ROLES))
):
    """
    Create a new permission.
    
    Creates a new permission in the system. Requires ASSIGN_ROLES permission.
    """
    return await role_service.create_permission(db, permission)

@app.post("/users/{user_id}/roles", status_code=status.HTTP_200_OK)
async def assign_role_to_user(
    user_id: str,
    role_id: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.check_permission(PermissionConstants.ASSIGN_ROLES))
):
    """
    Assign a role to a user.
    
    Assigns a role to a user by their IDs. Requires ASSIGN_ROLES permission.
    """
    user, role = await role_service.assign_role_to_user(db, user_id, role_id, current_user.tenant_id)
    
    return {
        "message": f"Role '{role.name}' successfully assigned to user '{user.username}'"
    }

@app.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_200_OK)
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.check_permission(PermissionConstants.ASSIGN_ROLES))
):
    """
    Remove a role from a user.
    
    Removes a role from a user by their IDs. Requires ASSIGN_ROLES permission.
    """
    user, role = await role_service.remove_role_from_user(db, user_id, role_id)
    
    return {
        "message": f"Role '{role.name}' successfully removed from user '{user.username}'"
    }

@app.post("/roles/{role_id}/permissions", status_code=status.HTTP_200_OK)
async def assign_permission_to_role(
    role_id: str,
    permission_id: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.check_permission(PermissionConstants.ASSIGN_ROLES))
):
    """
    Assign a permission to a role.
    
    Assigns a permission to a role by their IDs. Requires ASSIGN_ROLES permission.
    """
    role, permission = await role_service.assign_permission_to_role(db, role_id, permission_id)
    
    return {
        "message": f"Permission '{permission.name}' successfully assigned to role '{role.name}'"
    }

@app.delete("/roles/{role_id}/permissions/{permission_id}", status_code=status.HTTP_200_OK)
async def remove_permission_from_role(
    role_id: str,
    permission_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.check_permission(PermissionConstants.ASSIGN_ROLES))
):
    """
    Remove a permission from a role.
    
    Removes a permission from a role by their IDs. Requires ASSIGN_ROLES permission.
    """
    role, permission = await role_service.remove_permission_from_role(db, role_id, permission_id)
    
    return {
        "message": f"Permission '{permission.name}' successfully removed from role '{role.name}'"
    }

@app.get("/users/{user_id}/roles", response_model=List[Role])
async def get_user_roles(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.get_current_active_user)
):
    """
    Get roles for a user.
    
    Returns all roles assigned to a user.
    """
    # Users can view their own roles, but viewing other users' roles requires MANAGE_USERS permission
    if user_id != current_user.id and not auth_service.has_permission(current_user, PermissionConstants.MANAGE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view other users' roles"
        )
    
    # Get user
    user = user_service.get_user(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return user.roles

@app.get("/roles/{role_id}/permissions", response_model=List[Permission])
async def get_role_permissions(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth_service.get_current_active_user)
):
    """
    Get permissions for a role.
    
    Returns all permissions assigned to a role.
    """
    # Get role
    role = role_service.get_role(db, role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    return role.permissions
