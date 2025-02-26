"""
Middleware functions for the Project Service.
"""

import os
import httpx
from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key_here")
ALGORITHM = "HS256"

async def extract_tenant_id(request: Request):
    """
    Extract tenant ID from request header.
    """
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID not provided",
        )
    
    request.state.tenant_id = tenant_id
    return tenant_id

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