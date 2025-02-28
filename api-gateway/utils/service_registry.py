"""
Service Registry

This module provides a registry for tracking available microservices and their endpoints.
"""

import logging
from typing import Dict, Optional, List
from threading import Lock

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Registry for managing service endpoints.
    
    This class provides a thread-safe way to register, unregister, and retrieve
    service endpoints. It can be extended to support service discovery mechanisms
    like Consul or etcd.
    """
    
    def __init__(self):
        """Initialize the service registry."""
        self._services: Dict[str, str] = {}
        self._lock = Lock()
    
    def register_service(self, service_name: str, service_url: str) -> None:
        """
        Register a service with its URL.
        
        Args:
            service_name: The name of the service
            service_url: The base URL of the service
        """
        with self._lock:
            self._services[service_name] = service_url
            logger.info(f"Registered service '{service_name}' at {service_url}")
    
    def unregister_service(self, service_name: str) -> None:
        """
        Unregister a service.
        
        Args:
            service_name: The name of the service to unregister
        """
        with self._lock:
            if service_name in self._services:
                del self._services[service_name]
                logger.info(f"Unregistered service '{service_name}'")
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """
        Get the URL for a registered service.
        
        Args:
            service_name: The name of the service
            
        Returns:
            The service URL or None if the service is not registered
        """
        with self._lock:
            return self._services.get(service_name)
    
    def list_services(self) -> List[str]:
        """
        List all registered services.
        
        Returns:
            List of registered service names
        """
        with self._lock:
            return list(self._services.keys())
    
    def get_all_services(self) -> Dict[str, str]:
        """
        Get all registered services and their URLs.
        
        Returns:
            Dict mapping service names to their URLs
        """
        with self._lock:
            return self._services.copy()

# Initialize service registry
service_registry = ServiceRegistry()
