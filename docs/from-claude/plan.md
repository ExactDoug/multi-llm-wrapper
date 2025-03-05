## The Issue

The error "'async for' requires an object with __aiter__ method, got coroutine" is occurring because:

1. In the `BraveKnowledgeAggregator.process_query` method (line 79-86 in brave_knowledge_aggregator.py), it's trying to use `async for` with `self.brave_client.search()`:
   ```python
   async for result in self.brave_client.search(query_analysis.search_string):
       results.append(result)
       analysis_batch.append(result)
       # ...rest of the code
   ```

2. In the `BraveSearchClient.search` method (brave_client.py), the method is implemented as an async generator but is missing the `__aiter__` method:
   ```python
   async def search(self, query: str, count: int = None):
       # ...
       for result in results:
           yield result
   ```

3. The method is technically a valid async generator, but when it's being called, it's returning a coroutine object (the generator function itself) rather than an async iterator (the result of calling the generator function).

## The Solution

The issue is that `BraveSearchClient.search` is implemented as an async generator function, but the Python runtime still expects an object with `__aiter__` and `__anext__` methods. We need to make sure this method follows the proper async iterator protocol.

Here's the fix:

1. Change the `BraveSearchClient.search` method to properly implement the async iterator protocol:

```python
# Update in BraveSearchClient class in brave_client.py
async def search(self, query: str, count: int = None):
    """
    Execute a search query against Brave Search API.
    Returns an async iterator that yields search results one at a time.
    """
    await self.rate_limiter.acquire()

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": self.api_key
    }

    params = {
        "q": query,
        "count": min(count or self.max_results, 20)  # API limit
    }

    logger.debug(f"Making Brave Search API request to {self.base_url}")
    logger.debug(f"Query parameters: {params}")

    try:
        async with self.session.get(
            self.base_url,
            headers=headers,
            params=params,
            timeout=self.timeout
        ) as response:
            logger.debug(f"Brave Search API response status: {response.status}")

            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Brave Search API error: {error_text}")
                raise BraveSearchError(f"API error: {response.status} - {error_text}")

            data = await response.json()
            results = data.get("web", {}).get("results", [])
            logger.debug(f"Received {len(results)} results from Brave Search API")

            for result in results:
                yield result

    except asyncio.TimeoutError:
        logger.error("Brave Search API request timed out")
        raise BraveSearchError("Request timed out")

    except BraveSearchError:
        raise

    except Exception as e:
        logger.error(f"Brave Search API request failed: {str(e)}")
        raise BraveSearchError(f"Search failed: {str(e)}")
```

2. Create a search iterator class that properly implements `__aiter__`:

```python
# Add this to BraveSearchClient class in brave_client.py
class SearchResultIterator:
    """Async iterator for search results."""
    
    def __init__(self, client, query, count=None):
        self.client = client
        self.query = query
        self.count = count
        self._results = None
        self._index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self._results is None:
            # Fetch results on first iteration
            self._results = []
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.client.api_key
            }
            
            params = {
                "q": self.query,
                "count": min(self.count or self.client.max_results, 20)  # API limit
            }
            
            await self.client.rate_limiter.acquire()
            
            try:
                async with self.client.session.get(
                    self.client.base_url,
                    headers=headers,
                    params=params,
                    timeout=self.client.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise BraveSearchError(f"API error: {response.status} - {error_text}")
                    
                    data = await response.json()
                    self._results = data.get("web", {}).get("results", [])
            except Exception as e:
                raise BraveSearchError(f"Search failed: {str(e)}")
        
        if self._index >= len(self._results):
            raise StopAsyncIteration
        
        result = self._results[self._index]
        self._index += 1
        return result

# Then modify the search method to use this iterator
async def search(self, query: str, count: int = None):
    """Returns an async iterator for search results."""
    return self.SearchResultIterator(self, query, count)
```

## Implementation Details

The key to fixing this issue is ensuring that `BraveSearchClient.search` returns a proper async iterator object (like our new `SearchResultIterator` class) that correctly implements `__aiter__` and `__anext__`. This is a more robust approach than simply modifying the existing generator function.

With this change, when `process_query` tries to iterate over the results with `async for`, it will get a proper async iterator object instead of a coroutine, which will resolve the error.

## Additional Recommendations

1. Add proper error handling in the `__anext__` method to ensure any errors are properly propagated.

2. Consider implementing a caching mechanism in the `SearchResultIterator` to avoid redundant API calls.

3. Add proper cleanup methods to ensure resources are released when the iterator is no longer needed.

4. Make sure any other methods that return async generators are similarly updated to return proper async iterator objects.

## 1. Complete Implementation of SearchResultIterator

Here's a complete implementation of the `SearchResultIterator` class with proper error handling, caching, and cleanup:

```python
# Add to src/brave_search_aggregator/client/brave_client.py
import asyncio
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class SearchResultIterator:
    """Async iterator for search results with caching and error handling."""
    
    def __init__(self, client, query: str, count: Optional[int] = None):
        """
        Initialize the search result iterator.
        
        Args:
            client: The BraveSearchClient instance
            query: The search query string
            count: Maximum number of results to return (defaults to client's max_results)
        """
        self.client = client
        self.query = query
        self.count = count
        self._results: Optional[List[Dict[str, Any]]] = None
        self._index = 0
        self._initialized = False
        self._error: Optional[Exception] = None
        self._cleanup_required = False
        self._stats = {
            "total_results": 0,
            "yielded_results": 0,
            "fetch_timestamp": None
        }
    
    def __aiter__(self):
        """Return self as the iterator object."""
        return self
    
    async def __anext__(self):
        """Get the next search result."""
        # Initialize on first iteration
        if not self._initialized:
            await self._initialize()
            
        # Check for previous errors
        if self._error:
            self._cleanup_required = True
            await self._cleanup()
            raise self._error
            
        # Check if we've reached the end of results
        if self._index >= len(self._results or []):
            self._cleanup_required = True
            await self._cleanup()
            raise StopAsyncIteration
        
        # Get the next result
        try:
            result = self._results[self._index]
            self._index += 1
            self._stats["yielded_results"] += 1
            return result
        except Exception as e:
            logger.error(f"Error retrieving result at index {self._index}: {str(e)}")
            self._error = e
            self._cleanup_required = True
            await self._cleanup()
            raise
    
    async def _initialize(self):
        """Initialize the iterator by fetching results."""
        import time
        
        try:
            self._initialized = True
            self._cleanup_required = True
            
            # Acquire rate limit token
            await self.client.rate_limiter.acquire()
            
            # Prepare request parameters
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.client.api_key
            }
            
            params = {
                "q": self.query,
                "count": min(self.count or self.client.max_results, 20)  # API limit
            }
            
            logger.debug(f"Making Brave Search API request to {self.client.base_url}")
            logger.debug(f"Query parameters: {params}")
            
            # Make the API request
            async with self.client.session.get(
                self.client.base_url,
                headers=headers,
                params=params,
                timeout=self.client.timeout
            ) as response:
                logger.debug(f"Brave Search API response status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Brave Search API error: {error_text}")
                    self._error = BraveSearchError(f"API error: {response.status} - {error_text}")
                    return
                
                data = await response.json()
                self._results = data.get("web", {}).get("results", [])
                self._stats["total_results"] = len(self._results)
                self._stats["fetch_timestamp"] = time.time()
                
                logger.debug(f"Received {len(self._results)} results from Brave Search API")
        
        except asyncio.TimeoutError:
            logger.error("Brave Search API request timed out")
            self._error = BraveSearchError("Request timed out")
        
        except Exception as e:
            logger.error(f"Brave Search API request failed: {str(e)}")
            self._error = BraveSearchError(f"Search failed: {str(e)}")
    
    async def _cleanup(self):
        """Clean up resources used by the iterator."""
        if not self._cleanup_required:
            return
        
        try:
            # Log statistics about the iteration
            logger.debug(
                f"SearchResultIterator stats: "
                f"total={self._stats['total_results']}, "
                f"yielded={self._stats['yielded_results']}"
            )
            
            # Any additional cleanup can go here (e.g., closing file handles, etc.)
            # Currently, we don't need to manually clean up anything else
            
            self._cleanup_required = False
        except Exception as e:
            logger.error(f"Error during iterator cleanup: {str(e)}")

## 2. Update BraveSearchClient to Use the Iterator

Here's how to update the `BraveSearchClient.search` method to use our new iterator pattern:

```python
# Update in src/brave_search_aggregator/client/brave_client.py

class BraveSearchClient:
    # ... existing code ...
    
    async def search(self, query: str, count: Optional[int] = None):
        """
        Execute a search query against Brave Search API.
        Returns an async iterator that yields search results one at a time.
        
        Args:
            query: The search query string
            count: Maximum number of results to return (defaults to self.max_results)
            
        Returns:
            An async iterator that yields search results
        """
        return SearchResultIterator(self, query, count)
```

## 3. Update BraveKnowledgeAggregator to Properly Handle the Iterator

Now, let's update the `BraveKnowledgeAggregator.process_query` method to properly handle the async iterator:

```python
# Update in src/brave_search_aggregator/synthesizer/brave_knowledge_aggregator.py

async def process_query(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Process a query through the Brave Knowledge Aggregator.
    
    Args:
        query: The query string to process
        
    Yields:
        Status updates and search results
    """
    try:
        # Get query analysis first
        query_analysis = await self.query_analyzer.analyze_query(query)
        
        # Yield initial status message
        yield {
            "type": "status",
            "stage": "search_started",
            "message": f"Searching knowledge sources for: {query}"
        }
        
        # Initialize result tracking
        results = []
        analysis_batch = []
        batch_size = self.config.batch_size
        
        # Get search results using async iterator
        search_iterator = self.brave_client.search(query_analysis.search_string)
        
        # Process search results
        async for result in search_iterator:
            results.append(result)
            analysis_batch.append(result)
            
            # Stream result to user
            yield {
                "type": "search_result",
                "index": len(results),
                "total_so_far": len(results),
                "result": self._format_result(result)
            }
            
            # Perform interim analysis when batch is complete
            if len(analysis_batch) >= batch_size:
                patterns = self._analyze_patterns(analysis_batch)
                yield {
                    "type": "interim_analysis",
                    "results_analyzed": len(results),
                    "patterns": patterns,
                    "message": "Processing initial results..."
                }
                analysis_batch = []
        
        # Perform source selection
        if results:
            selected_sources = self._select_sources(results, min_sources=5)
            yield {
                "type": "status",
                "stage": "source_selection",
                "message": f"Selected {len(selected_sources)} most relevant sources",
                "sources": selected_sources
            }
        
        # Final summary
        if results:
            yield {
                "type": "summary",
                "total_results": len(results),
                "selected_sources": len(selected_sources) if selected_sources else 0,
                "key_findings": self._generate_summary(results)
            }
        else:
            yield {
                "type": "status",
                "stage": "no_results",
                "message": "No results found for query"
            }
            
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        yield {
            "type": "error",
            "error": str(e)
        }
```

## 4. Enhanced Error Handling Implementation

Here's an extended error handling class that can be used to improve error recovery throughout the application:

```python
# Add to src/brave_search_aggregator/utils/error_handler.py

import logging
import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional, Union

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """Context information for errors."""
    operation: str
    timestamp: float = field(default_factory=time.time)
    partial_results: List = field(default_factory=list)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

class ErrorHandler:
    """
    Enhanced error handling for streaming operations.
    Provides partial result preservation and recovery strategies.
    """
    def __init__(self):
        self._recovery_strategies = {}
        self._partial_results = {}
        self._error_stats = {
            "total_errors": 0,
            "recovered_errors": 0,
            "unrecoverable_errors": 0
        }
    
    def register_recovery_strategy(self, error_type, strategy_func):
        """
        Register a recovery strategy for a specific error type.
        
        Args:
            error_type: The type of exception to handle
            strategy_func: A callable that handles the error recovery
        """
        self._recovery_strategies[error_type] = strategy_func
    
    async def handle_error(self, error: Exception, context: ErrorContext) -> Dict:
        """
        Handle an error with appropriate recovery strategy.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            Dict containing error details and partial results if available
        """
        self._error_stats["total_errors"] += 1
        
        # Log the error
        logger.error(f"Error in {context.operation}: {str(error)}")
        logger.debug(f"Error traceback: {traceback.format_exc()}")
        
        # Store partial results
        self._partial_results[context.operation] = context.partial_results
        
        # Check if we have a recovery strategy
        for error_type, strategy in self._recovery_strategies.items():
            if isinstance(error, error_type):
                if context.recovery_attempts < context.max_recovery_attempts:
                    context.recovery_attempts += 1
                    try:
                        logger.info(f"Attempting recovery for {context.operation} (attempt {context.recovery_attempts})")
                        result = await strategy(error, context)
                        self._error_stats["recovered_errors"] += 1
                        return result
                    except Exception as recovery_error:
                        logger.error(f"Recovery failed: {str(recovery_error)}")
                else:
                    logger.warning(f"Maximum recovery attempts ({context.max_recovery_attempts}) reached")
        
        # If we get here, we couldn't recover
        self._error_stats["unrecoverable_errors"] += 1
        
        # Create error response with partial results
        return {
            "type": "error",
            "operation": context.operation,
            "error": str(error),
            "partial_results": context.partial_results,
            "recoverable": False
        }
    
    async def get_partial_results(self, operation: str) -> List:
        """
        Get partial results from a failed operation.
        
        Args:
            operation: The operation identifier
            
        Returns:
            List of partial results if available, or empty list
        """
        return self._partial_results.get(operation, [])
    
    def get_error_stats(self) -> Dict[str, int]:
        """
        Get error handling statistics.
        
        Returns:
            Dict containing error statistics
        """
        return self._error_stats.copy()
```

## 5. Memory Management Implementation

Here's a memory management class to track and limit resource usage:

```python
# Add to src/brave_search_aggregator/utils/resource_manager.py

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
```

## 6. Complete Implementation Guide

Here's a step-by-step guide for implementing the complete solution:

1. **Create or update the required files**:
   - Update `src/brave_search_aggregator/client/brave_client.py` with the new `SearchResultIterator` class and updated `search` method
   - Update `src/brave_search_aggregator/synthesizer/brave_knowledge_aggregator.py` with the improved `process_query` method
   - Create new utility files for error handling and resource management

## 7. Additional Notes on AsyncIteratorPattern Best Practices

Here are some best practices for implementing async iterators in Python:

1. **Proper implementation of `__aiter__` and `__anext__`**:
   - `__aiter__` should be synchronous and return `self`
   - `__anext__` should be async and return the next item or raise `StopAsyncIteration`

2. **Initialization handling**:
   - Defer expensive initialization until the first call to `__anext__`
   - Use a flag to track initialization state

3. **Error handling**:
   - Catch and handle errors during iteration
   - Provide meaningful error messages and propagate errors appropriately
   - Consider providing partial results when errors occur

4. **Resource management**:
   - Track and clean up resources used by the iterator
   - Implement proper cleanup when iteration is complete or errors occur
   - Consider using context managers for resource management

5. **Performance considerations**:
   - Cache results to avoid redundant API calls
   - Use batched processing when appropriate
   - Monitor and limit memory usage

By following these practices, you can ensure robust and efficient async iterator implementations in your Python code.

## Testing

- Start the test server on port 8001
- Make search requests to verify streaming behavior
- Check error scenarios by forcing errors (e.g., invalid API key)
- Monitor memory usage during high-load tests

Verify success criteria:

- First status message appears in < 100ms
- First result appears in < 1s
- No memory leaks during extended use
- Error handling properly preserves partial results
- Resources are properly cleaned up