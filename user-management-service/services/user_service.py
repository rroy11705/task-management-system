"""
Service for managing users.
"""

import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models import UserModel
from schemas import UserCreate, User
from services.auth_service import get_password_hash
from events.rabbitmq_client import rabbitmq_client

def create_user(db: Session, user: UserCreate):
    """
    Create a new user.
    """
    # TODO: Implement user creation logic
    # 1. Check if user already exists
    # 2. Hash password
    # 3. Create user in database
    # 4. Publish UserCreated event
    pass

def get_user(db: Session, user_id: str):
    """
    Get user by ID.
    """
    # TODO: Implement get user logic
    # 1. Get user from database
    # 2. Check if user exists
    pass

def get_user_by_email(db: Session, email: str):
    """
    Get user by email.
    """
    # TODO: Implement get user by email logic
    # 1. Get user from database with email filter
    pass

def get_user_by_username(db: Session, username: str):
    """
    Get user by username.
    """
    # TODO: Implement get user by username logic
    # 1. Get user from database with username filter
    pass