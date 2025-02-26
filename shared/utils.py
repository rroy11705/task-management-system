"""
Shared utility functions for the Task Management System.
"""

import uuid
import time
import hashlib
import base64
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

def generate_id() -> str:
    """
    Generate a unique ID.
    """
    return str(uuid.uuid4())

def generate_short_code(original_string: str, tenant_id: str) -> str:
    """
    Generate a short code for a URL.
    """
    # Combine original string, tenant ID, and timestamp
    combined = f"{original_string}_{tenant_id}_{time.time()}"
    
    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(combined.encode())
    hash_bytes = hash_obj.digest()
    
    # Encode in base64 and remove non-alphanumeric characters
    code = base64.urlsafe_b64encode(hash_bytes).decode()
    code = ''.join(c for c in code if c.isalnum())
    
    # Return first 8 characters
    return code[:8]

def create_jwt_token(data: Dict[str, Any], secret_key: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token.
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode.update({"exp": expire})
    
    # Create JWT token
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt

def decode_jwt_token(token: str, secret_key: str) -> Dict[str, Any]:
    """
    Decode a JWT token.
    """
    return jwt.decode(token, secret_key, algorithms=["HS256"])