"""
Middleware functions for the API Gateway.
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key_here")
ALGORITHM = "HS256"

security = HTTPBearer()

async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token and extract user information.
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def extract_tenant(request: Request):
    """
    Extract tenant information from subdomain or header.
    """
    # TODO: Extract tenant from subdomain or header
    # For development, might use a header like X-Tenant-ID
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        # Try to extract from host
        host = request.headers.get("host", "")
        # TODO: Parse subdomain to get tenant_id
        
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID not provided",
        )
    
    request.state.tenant_id = tenant_id
    return tenant_id