"""
Service for handling authentication and authorization.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import UserModel
from schemas import User, TokenData

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your_secret_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash password.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str) -> Union[UserModel, bool]:
    """
    Authenticate user with username and password.
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        The authenticated user if successful, False otherwise
    """
    # Try to find user by username
    user = db.query(UserModel).filter(UserModel.username == username).first()
    
    # If user not found, try by email
    if not user:
        user = db.query(UserModel).filter(UserModel.email == username).first()
        
    # If still no user or password doesn't match, return False
    if not user or not verify_password(password, user.hashed_password):
        return False
        
    # Check if user is active
    if not user.is_active:
        return False
        
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    # Create JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Get current user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        The current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id, tenant_id=payload.get("tenant_id"))
    except JWTError:
        raise credentials_exception
        
    # Get user from database
    user = db.query(UserModel).filter(UserModel.id == token_data.user_id).first()
    
    if user is None:
        raise credentials_exception
        
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
        
    return user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Get current active user.
    
    Args:
        current_user: Current user from JWT token
        
    Returns:
        The current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Inactive user"
        )
    return current_user

def has_permission(user: UserModel, permission: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user: User to check permissions for
        permission: Permission to check
        
    Returns:
        True if the user has the permission, False otherwise
    """
    if not user.roles:
        return False
        
    for role in user.roles:
        for perm in role.permissions:
            if perm.name == permission:
                return True
                
    return False

def check_permission(permission: str):
    """
    Dependency for checking if user has a specific permission.
    
    Args:
        permission: Permission to check
        
    Returns:
        Dependency function that raises an exception if user doesn't have permission
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    async def _check_permission(current_user: UserModel = Depends(get_current_active_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions: {permission} required"
            )
        return current_user
    return _check_permission