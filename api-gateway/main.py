"""
API Gateway Service

This module serves as the main entry point for the API Gateway service.
It routes client requests to appropriate microservices, handles authentication,
extracts tenant information, and implements rate limiting.
"""

import logging
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from jwt.exceptions import InvalidTokenError

from config import settings
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.tenant_resolver import TenantResolverMiddleware
from middlewares.logging_middleware import LoggingMiddleware
from utils.service_registry import service_registry
from utils.jwt_utils import validate_token, extract_user_info
from proxy import proxy_request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api_gateway")

# Initialize FastAPI application
app = FastAPI(
    title="SaaS Platform API Gateway",
    description="API Gateway for routing requests to appropriate microservices",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, rate_limit=settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(TenantResolverMiddleware)


@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup."""
    logger.info("API Gateway starting up")
    # Register services
    service_registry.register_service("user-management", settings.USER_MANAGEMENT_SERVICE_URL)
    service_registry.register_service("tenant-resolver", settings.TENANT_RESOLVER_SERVICE_URL)
    # Add other services as they become available


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    logger.info("API Gateway shutting down")


async def get_token_header(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Validates the JWT token in the Authorization header.
    
    Args:
        authorization: The Authorization header value
        
    Returns:
        Dict containing user information extracted from the token
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme. Expected 'Bearer'"
        )
    
    try:
        payload = validate_token(token)
        return extract_user_info(payload)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for the API Gateway."""
    return {"status": "healthy", "timestamp": time.time()}


# User Management Service routes
@app.api_route("/api/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_management_proxy(request: Request, path: str, user_info: Dict = Depends(get_token_header)):
    """Routes requests to the User Management Service."""
    return await proxy_request(request, "user-management", path)


# Tenant Resolver Service routes
@app.api_route("/api/tenants/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def tenant_resolver_proxy(request: Request, path: str, user_info: Dict = Depends(get_token_header)):
    """Routes requests to the Tenant Resolver Service."""
    return await proxy_request(request, "tenant-resolver", path)


# Authentication routes (no token required)
@app.api_route("/api/auth/{path:path}", methods=["GET", "POST"])
async def auth_proxy(request: Request, path: str):
    """Routes authentication requests to the User Management Service."""
    return await proxy_request(request, "user-management", f"auth/{path}")

# Roles routes
@app.api_route("/api/roles/{path:path}", methods=["GET", "POST"])
async def auth_proxy(request: Request, path: str):
    """Routes roles requests to the User Management Service."""
    return await proxy_request(request, "user-management", f"roles/{path}")


# Fallback route for unmatched paths
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def catch_all(request: Request, path: str):
    """Catches all unmatched routes and returns a 404 error."""
    return JSONResponse(
        status_code=404,
        content={"detail": f"Endpoint '{request.method} /{path}' not found"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )