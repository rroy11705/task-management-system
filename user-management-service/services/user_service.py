"""
Service for managing users.
"""

import uuid
from typing import Optional, List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from models import UserModel
from schemas import UserCreate, UserUpdate, User
from services.auth_service import get_password_hash
from events.rabbitmq_client import rabbitmq_client
from shared.events import UserCreatedEvent

async def create_user(db: Session, user: UserCreate) -> UserModel:
    """
    Create a new user.
    
    Args:
        db: Database session
        user: User data
        
    Returns:
        The created user
        
    Raises:
        HTTPException: If user already exists
    """
    # Check if user already exists with the same email or username
    existing_user = db.query(UserModel).filter(
        (UserModel.email == user.email) | (UserModel.username == user.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )
    
    # Generate a unique ID for the user
    user_id = str(uuid.uuid4())
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user in database
    db_user = UserModel(
        id=user_id,
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        tenant_id=user.tenant_id,
        is_active=True
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User could not be created due to a conflict with existing data"
        )
    
    # Publish UserCreated event
    try:
        event = UserCreatedEvent(
            tenant_id=user.tenant_id,
            user_id=user_id,
            email=user.email,
            username=user.username
        )
        await rabbitmq_client.publish_event(event.event_type, event.to_dict())
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Failed to publish UserCreated event: {str(e)}")
    
    return db_user

def get_user(db: Session, user_id: str) -> Optional[UserModel]:
    """
    Get user by ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        The user if found, None otherwise
    """
    return db.query(UserModel).filter(UserModel.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    """
    Get user by email.
    
    Args:
        db: Database session
        email: User email
        
    Returns:
        The user if found, None otherwise
    """
    return db.query(UserModel).filter(UserModel.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
    """
    Get user by username.
    
    Args:
        db: Database session
        username: Username
        
    Returns:
        The user if found, None otherwise
    """
    return db.query(UserModel).filter(UserModel.username == username).first()

def get_users_by_tenant(db: Session, tenant_id: str, skip: int = 0, limit: int = 100) -> List[UserModel]:
    """
    Get all users for a tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of users
    """
    return db.query(UserModel).filter(
        UserModel.tenant_id == tenant_id
    ).offset(skip).limit(limit).all()

async def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[UserModel]:
    """
    Update a user.
    
    Args:
        db: Database session
        user_id: User ID
        user_update: User data to update
        
    Returns:
        The updated user if found, None otherwise
    """
    # Get user
    db_user = get_user(db, user_id)
    
    if not db_user:
        return None
        
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    
    # If password is being updated, hash it
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Update user attributes
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User could not be updated due to a conflict with existing data"
        )
    
    return db_user

async def deactivate_user(db: Session, user_id: str) -> Optional[UserModel]:
    """
    Deactivate a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        The deactivated user if found, None otherwise
    """
    # Get user
    db_user = get_user(db, user_id)
    
    if not db_user:
        return None
        
    # Deactivate user
    db_user.is_active = False
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

async def reactivate_user(db: Session, user_id: str) -> Optional[UserModel]:
    """
    Reactivate a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        The reactivated user if found, None otherwise
    """
    # Get user
    db_user = get_user(db, user_id)
    
    if not db_user:
        return None
        
    # Reactivate user
    db_user.is_active = True
    
    db.commit()
    db.refresh(db_user)
    
    return db_user