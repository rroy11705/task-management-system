"""
Service for managing roles and permissions.
"""

import uuid
from typing import Optional, List, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from models import RoleModel, PermissionModel, UserModel, user_role_association, role_permission_association
from schemas import RoleCreate, Role, PermissionCreate, Permission
from events.rabbitmq_client import rabbitmq_client
from shared.events import UserPermissionChangedEvent

async def create_role(db: Session, role_create: RoleCreate) -> RoleModel:
    """
    Create a new role.
    
    Args:
        db: Database session
        role_create: Role data
        
    Returns:
        The created role
        
    Raises:
        HTTPException: If role already exists
    """
    # Check if role already exists with the same name
    existing_role = db.query(RoleModel).filter(RoleModel.name == role_create.name).first()
    
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with name '{role_create.name}' already exists"
        )
    
    # Generate a unique ID for the role
    role_id = str(uuid.uuid4())
    
    # Create role in database
    db_role = RoleModel(
        id=role_id,
        name=role_create.name,
        description=role_create.description
    )
    
    try:
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role could not be created due to a conflict with existing data"
        )
    
    return db_role

async def create_permission(db: Session, permission_create: PermissionCreate) -> PermissionModel:
    """
    Create a new permission.
    
    Args:
        db: Database session
        permission_create: Permission data
        
    Returns:
        The created permission
        
    Raises:
        HTTPException: If permission already exists
    """
    # Check if permission already exists with the same name
    existing_permission = db.query(PermissionModel).filter(
        PermissionModel.name == permission_create.name
    ).first()
    
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Permission with name '{permission_create.name}' already exists"
        )
    
    # Generate a unique ID for the permission
    permission_id = str(uuid.uuid4())
    
    # Create permission in database
    db_permission = PermissionModel(
        id=permission_id,
        name=permission_create.name,
        description=permission_create.description
    )
    
    try:
        db.add(db_permission)
        db.commit()
        db.refresh(db_permission)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission could not be created due to a conflict with existing data"
        )
    
    return db_permission

async def assign_role_to_user(db: Session, user_id: str, role_id: str, tenant_id: str) -> Tuple[UserModel, RoleModel]:
    """
    Assign a role to a user.
    
    Args:
        db: Database session
        user_id: User ID
        role_id: Role ID
        tenant_id: Tenant ID for event publishing
        
    Returns:
        Tuple of (user, role)
        
    Raises:
        HTTPException: If user or role not found
    """
    # Get user
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get role
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Check if user already has this role
    if role in user.roles:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User already has role '{role.name}'"
        )
    
    # Assign role to user
    user.roles.append(role)
    
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role assignment could not be completed due to a data conflict"
        )
    
    # Publish UserPermissionChanged event
    try:
        # Get all permission names from the role
        permission_names = [permission.name for permission in role.permissions]
        
        event = UserPermissionChangedEvent(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=role_id,
            role_name=role.name,
            permissions=permission_names
        )
        await rabbitmq_client.publish_event(event.event_type, event.to_dict())
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Failed to publish UserPermissionChanged event: {str(e)}")
    
    return (user, role)

async def remove_role_from_user(db: Session, user_id: str, role_id: str) -> Tuple[UserModel, RoleModel]:
    """
    Remove a role from a user.
    
    Args:
        db: Database session
        user_id: User ID
        role_id: Role ID
        
    Returns:
        Tuple of (user, role)
        
    Raises:
        HTTPException: If user or role not found, or user doesn't have the role
    """
    # Get user
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get role
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Check if user has this role
    if role not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User does not have role '{role.name}'"
        )
    
    # Remove role from user
    user.roles.remove(role)
    
    db.commit()
    db.refresh(user)
    
    return (user, role)

async def assign_permission_to_role(db: Session, role_id: str, permission_id: str) -> Tuple[RoleModel, PermissionModel]:
    """
    Assign a permission to a role.
    
    Args:
        db: Database session
        role_id: Role ID
        permission_id: Permission ID
        
    Returns:
        Tuple of (role, permission)
        
    Raises:
        HTTPException: If role or permission not found
    """
    # Get role
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Get permission
    permission = db.query(PermissionModel).filter(PermissionModel.id == permission_id).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with ID {permission_id} not found"
        )
    
    # Check if role already has this permission
    if permission in role.permissions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role already has permission '{permission.name}'"
        )
    
    # Assign permission to role
    role.permissions.append(permission)
    
    db.commit()
    db.refresh(role)
    
    return (role, permission)

async def remove_permission_from_role(db: Session, role_id: str, permission_id: str) -> Tuple[RoleModel, PermissionModel]:
    """
    Remove a permission from a role.
    
    Args:
        db: Database session
        role_id: Role ID
        permission_id: Permission ID
        
    Returns:
        Tuple of (role, permission)
        
    Raises:
        HTTPException: If role or permission not found, or role doesn't have the permission
    """
    # Get role
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Get permission
    permission = db.query(PermissionModel).filter(PermissionModel.id == permission_id).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with ID {permission_id} not found"
        )
    
    # Check if role has this permission
    if permission not in role.permissions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role does not have permission '{permission.name}'"
        )
    
    # Remove permission from role
    role.permissions.remove(permission)
    
    db.commit()
    db.refresh(role)
    
    return (role, permission)

def get_role(db: Session, role_id: str) -> Optional[RoleModel]:
    """
    Get role by ID.
    
    Args:
        db: Database session
        role_id: Role ID
        
    Returns:
        The role if found, None otherwise
    """
    return db.query(RoleModel).filter(RoleModel.id == role_id).first()

def get_role_by_name(db: Session, name: str) -> Optional[RoleModel]:
    """
    Get role by name.
    
    Args:
        db: Database session
        name: Role name
        
    Returns:
        The role if found, None otherwise
    """
    return db.query(RoleModel).filter(RoleModel.name == name).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[RoleModel]:
    """
    Get all roles.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of roles
    """
    return db.query(RoleModel).offset(skip).limit(limit).all()

def get_permission(db: Session, permission_id: str) -> Optional[PermissionModel]:
    """
    Get permission by ID.
    
    Args:
        db: Database session
        permission_id: Permission ID
        
    Returns:
        The permission if found, None otherwise
    """
    return db.query(PermissionModel).filter(PermissionModel.id == permission_id).first()

def get_permission_by_name(db: Session, name: str) -> Optional[PermissionModel]:
    """
    Get permission by name.
    
    Args:
        db: Database session
        name: Permission name
        
    Returns:
        The permission if found, None otherwise
    """
    return db.query(PermissionModel).filter(PermissionModel.name == name).first()

def get_permissions(db: Session, skip: int = 0, limit: int = 100) -> List[PermissionModel]:
    """
    Get all permissions.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of permissions
    """
    return db.query(PermissionModel).offset(skip).limit(limit).all()

def get_user_roles(db: Session, user_id: str) -> List[RoleModel]:
    """
    Get all roles for a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        List of roles
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    
    if not user:
        return []
        
    return user.roles

def get_role_permissions(db: Session, role_id: str) -> List[PermissionModel]:
    """
    Get all permissions for a role.
    
    Args:
        db: Database session
        role_id: Role ID
        
    Returns:
        List of permissions
    """
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    
    if not role:
        return []
        
    return role.permissions