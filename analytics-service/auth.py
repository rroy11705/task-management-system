"""
Authentication utilities for the Analytics Service.
"""

import os
from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key_here")
ALGORITHM = "HS256"

async def get_current_user(request: Request):
    """
    Get current user from JWT token.
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except (JWTError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )