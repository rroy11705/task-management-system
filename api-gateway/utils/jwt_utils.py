"""
JWT Utilities

This module provides utilities for JWT token validation and user information extraction.
"""

import jwt
from typing import Dict, Any
from datetime import datetime, timezone

from config import settings


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validates a JWT token and returns the payload.
    
    Args:
        token: The JWT token to validate
        
    Returns:
        Dict containing the token payload
        
    Raises:
        jwt.PyJWTError: If the token is invalid
    """
    # Decode and validate the token
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM]
    )
    
    # Check if the token has expired
    if "exp" in payload and datetime.now(timezone.utc).timestamp() > payload["exp"]:
        raise jwt.ExpiredSignatureError("Token has expired")
    
    return payload


def extract_user_info(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts user information from a token payload.
    
    Args:
        payload: The token payload
        
    Returns:
        Dict containing user information
    """
    user_info = {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "user"),
        "tenant_id": payload.get("tenant_id")
    }
    
    # Add other claims that might be useful
    if "permissions" in payload:
        user_info["permissions"] = payload["permissions"]
    
    return user_info