"""
Utility functions for proxying requests to other services.
"""

import httpx
import logging
from fastapi import Request, Response
from utils.service_registry import service_registry
from fastapi import Request, Response, HTTPException
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api_gateway")

async def proxy_request(request: Request, service_name: str, path: str) -> Response:
    """
    Proxies the request to the specified service.
    
    Args:
        request: The original request
        service_name: The name of the service to route to
        path: The path to forward to the service
        
    Returns:
        The response from the service
        
    Raises:
        HTTPException: If the service is not found or there's an error in the request
    """
    service_url = service_registry.get_service_url(service_name)
    if not service_url:
        raise HTTPException(status_code=503, detail=f"Service '{service_name}' not available")
    
    # Prepare headers to forward
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header to avoid conflicts
    
    # Add tenant information from request state if available
    if hasattr(request.state, "tenant_id"):
        headers["X-Tenant-ID"] = request.state.tenant_id
    
    # Fetch request body if it exists
    body = await request.body()
    
    target_url = f"{service_url}/{path}"
    method = request.method
    
    async with httpx.AsyncClient(timeout=settings.SERVICE_TIMEOUT) as client:
        try:
            response = await client.request(
                method,
                target_url,
                headers=headers,
                content=body,
                params=request.query_params,
                follow_redirects=True
            )
            
            # Return the response with the same status code
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.RequestError as exc:
            logger.error(f"Error while requesting {target_url}: {str(exc)}")
            raise HTTPException(status_code=503, detail=f"Service communication error: {str(exc)}")