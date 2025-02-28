"""
Rate Limiting Middleware

This module provides middleware for rate limiting requests based on client IP address.
It supports both in-memory and Redis-based rate limiting.
"""

import time
import logging
from typing import Dict, Tuple, Optional, Callable
from collections import defaultdict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from config import settings

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using a sliding window algorithm.
    
    This implementation uses a defaultdict to track request timestamps for each client.
    It's suitable for single-instance deployments but won't work in a distributed setup.
    """
    
    def __init__(self, window_seconds: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            window_seconds: The time window in seconds
        """
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def check_rate_limit(self, client_id: str, max_requests: int) -> Tuple[bool, int]:
        """
        Check if the client has exceeded the rate limit.
        
        Args:
            client_id: The client identifier (e.g., IP address)
            max_requests: Maximum allowed requests in the window
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current_time = time.time()
        client_requests = self.requests[client_id]
        
        # Remove expired timestamps
        window_start = current_time - self.window_seconds
        client_requests = [ts for ts in client_requests if ts > window_start]
        self.requests[client_id] = client_requests
        
        # Check if rate limit is exceeded
        if len(client_requests) >= max_requests:
            return False, 0
        
        # Add current request timestamp
        client_requests.append(current_time)
        remaining = max_requests - len(client_requests)
        
        return True, remaining


class RedisRateLimiter:
    """
    Redis-based rate limiter using a sliding window algorithm.
    
    This implementation uses Redis sorted sets to track request timestamps.
    It's suitable for distributed deployments as all instances share the same Redis.
    """
    
    def __init__(self, window_seconds: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            window_seconds: The time window in seconds
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis package is not installed")
        
        self.window_seconds = window_seconds
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
    
    def check_rate_limit(self, client_id: str, max_requests: int) -> Tuple[bool, int]:
        """
        Check if the client has exceeded the rate limit.
        
        Args:
            client_id: The client identifier (e.g., IP address)
            max_requests: Maximum allowed requests in the window
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current_time = time.time()
        key = f"rate_limit:{client_id}"
        
        # Remove expired timestamps
        window_start = current_time - self.window_seconds
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Get the current count
        current_count = self.redis.zcard(key)
        
        # Check if rate limit is exceeded
        if current_count >= max_requests:
            return False, 0
        
        # Add current request timestamp with pipeline for atomicity
        pipeline = self.redis.pipeline()
        pipeline.zadd(key, {str(current_time): current_time})
        pipeline.expire(key, self.window_seconds)
        pipeline.execute()
        
        remaining = max_requests - (current_count + 1)
        
        return True, remaining


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests.
    
    This middleware checks if the client has exceeded the rate limit and
    returns a 429 Too Many Requests response if they have.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        rate_limit: int = 100,
        window_seconds: int = 60,
        get_client_id: Optional[Callable[[Request], str]] = None
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            rate_limit: Maximum requests allowed per client in the time window
            window_seconds: The time window in seconds
            get_client_id: Function to extract client ID from request (default uses client IP)
        """
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.get_client_id = get_client_id or self._default_get_client_id
        
        # Initialize the appropriate rate limiter
        if settings.USE_REDIS_RATE_LIMIT and REDIS_AVAILABLE:
            try:
                self.rate_limiter = RedisRateLimiter(window_seconds)
                logger.info("Using Redis-based rate limiter")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis rate limiter: {e}. Falling back to in-memory.")
                self.rate_limiter = InMemoryRateLimiter(window_seconds)
        else:
            self.rate_limiter = InMemoryRateLimiter(window_seconds)
            logger.info("Using in-memory rate limiter")
    
    @staticmethod
    def _default_get_client_id(request: Request) -> str:
        """
        Extract client ID from request using client's IP address.
        
        Args:
            request: The request object
            
        Returns:
            The client ID (IP address)
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Get the first IP in the chain which is the client's IP
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return client_ip
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request through the middleware.
        
        Args:
            request: The request object
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        # Skip rate limiting for specific paths like health checks
        path = request.url.path
        if path.startswith("/health"):
            return await call_next(request)
        
        client_id = self.get_client_id(request)
        
        # Check rate limit
        is_allowed, remaining = self.rate_limiter.check_rate_limit(client_id, self.rate_limit)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "type": "rate_limit_exceeded"
                },
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # Add rate limit headers to the response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_seconds))
        
        return response