"""
Shared validation utilities for the Task Management System.
"""

import re
from typing import Optional

def validate_email(email: str) -> bool:
    """
    Validate an email address.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def validate_username(username: str) -> bool:
    """
    Validate a username.
    """
    pattern = r"^[a-zA-Z0-9_-]{3,16}$"
    return bool(re.match(pattern, username))

def validate_password_strength(password: str) -> Optional[str]:
    """
    Validate password strength. Returns error message if invalid, None if valid.
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character"
    
    return None

def validate_subdomain(subdomain: str) -> bool:
    """
    Validate a subdomain.
    """
    pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$"
    return bool(re.match(pattern, subdomain))

def validate_url(url: str) -> bool:
    """
    Validate a URL.
    """
    pattern = r"^(http|https)://[a-zA-Z0-9]([a-zA-Z0-9\-\._~:/?#\[\]@!$&'\(\)\*\+,;=]+)?$"
    return bool(re.match(pattern, url))