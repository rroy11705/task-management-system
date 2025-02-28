"""
Tenant Resolver Middleware

This module provides middleware for extracting tenant information from request headers or subdomains.
"""

import logging
import re
from typing import Optional, Tuple
import httpx
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from config import settings

logger = logging.getLogger(__name__)


class TenantResolverMiddleware(BaseHTTPMiddleware):
    """
    Middleware for extracting tenant information from requests.
    
    This middleware extracts tenant information from the request's host header
    (subdomain) or from custom headers, and attaches it to the request state.
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
        self.tenant_resolver_url = settings.TENANT_RESOLVER_SERVICE_URL
    
    @staticmethod
    def extract_subdomain(host: str) -> Optional[str]:
        """
        Extract subdomain from host header.
        
        Args:
            host: The host header value (e.g., tenant1.example.com)
            
        Returns:
            The subdomain or None if it's the root domain
        """
        # Handle cases with port number
        host = host.split(':')[0]
        
        # Extract subdomain
        parts = host.split('.')
        if len(parts) >= 3:
            return parts[0]
        
        return None
    
    async def resolve_tenant_from_subdomain(self, subdomain: str) -> Optional[str]:
        """
        Resolve tenant ID from subdomain by calling Tenant Resolver Service.
        
        Args:
            subdomain: The subdomain to resolve
            
        Returns:
            The tenant ID or None if not found
        """
        if not subdomain:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.tenant_resolver_url}/resolve/{subdomain}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("tenant_id")
                
                logger.warning(
                    f"Failed to resolve tenant for subdomain '{subdomain}'. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
        
        except httpx.RequestError as e:
            logger.error(f"Error calling Tenant Resolver Service: {str(e)}")
        
        return None
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request through the middleware.
        
        Args:
            request: The request object
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        # Skip tenant resolution for public routes
        path = request.url.path
        if (
            path.startswith("/health") or
            path.startswith("/api/auth") or
            path == "/"
        ):
            return await call_next(request)
        
        # Check for explicit tenant ID in headers
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # If no tenant ID in headers, try to extract from subdomain
        if not tenant_id:
            host = request.headers.get("host", "")
            subdomain = self.extract_subdomain(host)
            
            if subdomain:
                tenant_id = await self.resolve_tenant_from_subdomain(subdomain)
        
        # Attach tenant ID to request state if found
        if tenant_id:
            request.state.tenant_id = tenant_id
            logger.debug(f"Resolved tenant ID: {tenant_id}")
        else:
            logger.debug("No tenant ID resolved")
        
        # Continue processing the request
        return await call_next(request)