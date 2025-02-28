"""
Logging Middleware

This module provides middleware for logging request and response information.
"""

import logging
import time
import uuid
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging request and response information.
    
    This middleware logs information about each request and response, including
    timing, status code, and tenant information if available.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request through the middleware.
        
        Args:
            request: The request object
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract request information
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        
        # Start timing
        start_time = time.time()
        
        # Log request information
        logger.info(
            f"Request {request_id} started: {method} {url} from {client_ip}"
        )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate request duration
            process_time = time.time() - start_time
            
            # Extract tenant ID if available
            tenant_id = getattr(request.state, "tenant_id", None)
            
            # Log response information
            log_message = (
                f"Request {request_id} completed: {method} {url} "
                f"- Status: {response.status_code} - Duration: {process_time:.3f}s"
            )
            
            if tenant_id:
                log_message += f" - Tenant: {tenant_id}"
            
            if 200 <= response.status_code < 400:
                logger.info(log_message)
            else:
                logger.warning(log_message)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate request duration
            process_time = time.time() - start_time
            
            # Log error information
            logger.error(
                f"Request {request_id} failed: {method} {url} "
                f"- Error: {str(e)} - Duration: {process_time:.3f}s",
                exc_info=True
            )
            
            # Re-raise the exception to be handled by FastAPI's exception handlers
            raise