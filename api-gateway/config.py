"""
API Gateway Configuration

This module defines the configuration settings for the API Gateway service.
It loads environment variables and provides default values for the service.
"""

import os
from typing import List
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the API Gateway service."""
    
    # Basic service configuration
    SERVICE_NAME: str = "api-gateway"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # JWT configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    
    # Service URLs
    USER_MANAGEMENT_SERVICE_URL: str = os.getenv(
        "USER_MANAGEMENT_SERVICE_URL",
        "http://user-management-service:8001"
    )
    TENANT_RESOLVER_SERVICE_URL: str = os.getenv(
        "TENANT_RESOLVER_SERVICE_URL",
        "http://tenant-resolver-service:8002"
    )
    
    # CORS configuration
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost,http://localhost:3000"
    ).split(",")
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str) -> List[str]:
        """
        Validates and formats the CORS origins.
        
        Args:
            v: The CORS origins as a comma-separated string
            
        Returns:
            List of CORS origins
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Rate limiting configuration
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    
    # Service communication settings
    SERVICE_TIMEOUT: float = float(os.getenv("SERVICE_TIMEOUT", "30.0"))
    
    # Redis configuration for rate limiting (optional)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    USE_REDIS_RATE_LIMIT: bool = os.getenv("USE_REDIS_RATE_LIMIT", "False").lower() in ("true", "1", "t")
    
    class Config:
        """Pydantic config for the Settings class."""
        case_sensitive = True
        env_file = ".env"


# Create a global settings instance
settings = Settings()