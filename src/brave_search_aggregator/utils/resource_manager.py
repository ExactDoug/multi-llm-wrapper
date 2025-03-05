import asyncio
import logging
import os
import time
from typing import Dict, List, Set, Any, Optional, Callable

logger = logging.getLogger(__name__)

class ResourceManager:
    """
    Manages memory and resources for async operations.
    Tracks resource usage and enforces limits.
    """
    def __init__(self, max_memory_mb=10):
        """
        Initialize the resource manager.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_memory = max_memory_mb * 1024 * 1024  # Convert to bytes
        self.current_usage = 0
        self._resources = set()
        self._resource_locks = {}
        self._cleanup_handlers = {}
        self._lock = asyncio.Lock()
        self._stats = {
            "peak_memory": 0,
            "current_memory": 0,
            "tracked_resources": 0,
            "cleaned_resources": 0
        }
    
    async def __aenter__(self):
        """Context manager entry - sets up monitoring."""
        await self._setup_monitoring()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleans up resources."""
        await self._cleanup_resources()
    
    async def _setup_monitoring(self):
        """Set up resource monitoring."""
        # This could include setting up periodic checks
        # For now, we'll just track resources manually
        pass
    
    async def track_resource(self, resource, size_bytes=0, cleanup_handler=None):
        """
        Track a resource for cleanup and memory monitoring.
        
        Args:
            resource: The resource to track
            size_bytes: Estimated memory size of the resource
            cleanup_handler: Optional function to call when cleaning up
            
        Returns:
            Resource tracking ID
        """
        async with self._lock:
            resource_id = id(resource)
            self._resources.add(resource_id)
            
            if cleanup_handler:
                self._cleanup_handlers[resource_id] = cleanup_handler
            
            self.current_usage += size_bytes
            self._stats["current_memory"] = self.current_usage
            self._stats["peak_memory"] = max(self._stats["peak_memory"], self.current_usage)
            self._stats["tracked_resources"] = len(self._resources)
            
            await self._check_memory_usage()
            
            return resource_id
    
    async def untrack_resource(self, resource_id):
        """
        Remove tracking for a resource.
        
        Args:
            resource_id: The resource ID to untrack
        """
        async with self._lock:
            if resource_id in self._resources:
                self._resources.remove(resource_id)
                
                # Call cleanup handler if it exists
                if resource_id in self._cleanup_handlers:
                    try:
                        await self._cleanup_handlers[resource_id]()
                    except Exception as e:
                        logger.error(f"Error in cleanup handler: {str(e)}")
                    finally:
                        del self._cleanup_handlers[resource_id]
                
                self._stats["cleaned_resources"] += 1
    
    async def _check_memory_usage(self):
        """Check memory usage and trigger cleanup if needed."""
        if self.current_usage > self.max_memory:
            logger.warning(f"Memory usage ({self.current_usage} bytes) exceeds limit ({self.max_memory} bytes)")
            await self._cleanup_oldest_resources()
    
    async def _cleanup_oldest_resources(self, count=5):
        """
        Clean up the oldest tracked resources.
        
        Args:
            count: Number of resources to clean up
        """
        # In a real implementation, we might want to track timestamps
        # For simplicity, we'll just take the first N resources
        resources_to_clean = list(self._resources)[:count]
        
        for resource_id in resources_to_clean:
            await self.untrack_resource(resource_id)
    
    async def _cleanup_resources(self):
        """Clean up all tracked resources."""
        resources_to_clean = list(self._resources)
        
        for resource_id in resources_to_clean:
            await self.untrack_resource(resource_id)
    
    def get_stats(self):
        """
        Get resource usage statistics.
        
        Returns:
            Dict containing resource statistics
        """
        return self._stats.copy()