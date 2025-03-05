from typing import Dict, Any, List, Optional, AsyncGenerator, AsyncIterator
from dataclasses import dataclass
import aiohttp
import asyncio
import time
from ..config_types import BraveSearchConfig

class BraveSearchError(Exception):
    """Custom exception for Brave Search errors"""
    pass

class RateLimiter:
    """Token bucket rate limiter"""
    def __init__(self, max_rate: int = 20):
        self.max_rate = max_rate
        self.tokens = max_rate
        self.last_update = time.monotonic()
        self.token_rate = max_rate / 1.0  # tokens per second
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire rate limit token"""
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(
                self.max_rate,
                self.tokens + elapsed * self.token_rate
            )
            self.last_update = now
            
            if self.tokens < 1:
                raise BraveSearchError("Rate limit exceeded")
            
            self.tokens -= 1

@dataclass
class SearchResult:
    """Structured search result"""
    title: str
    url: str
    description: str
    metadata: Dict[str, Any]

class BraveSearchClient:
    """Client for interacting with Brave Search API"""
    def __init__(self, config: BraveSearchConfig):
        self.config = config
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.session = aiohttp.ClientSession()
        self.rate_limiter = RateLimiter(config.max_rate)
        self.usage_stats = {
            "queries": 0,
            "results": 0,
            "errors": 0
        }
        self.start_time = time.monotonic()
        
    async def search(
        self,
        query: str,
        count: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Returns an async iterator that yields search results
        
        Args:
            query: Search query string
            count: Optional number of results to return
            
        Returns:
            AsyncIterator that yields search results as dictionaries
            
        Raises:
            BraveSearchError: For API or processing errors
        """
        return SearchResultIterator(self, query, count)
    
    def _process_results(
        self,
        raw_results: Dict[str, Any]
    ) -> List[SearchResult]:
        """Process raw API results into structured format"""
        processed = []
        for result in raw_results.get("web", {}).get("results", []):
            processed.append(SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                description=result.get("description", ""),
                metadata={
                    "age": result.get("age"),
                    "language": result.get("language"),
                    "family_friendly": result.get("family_friendly", True)
                }
            ))
        return processed
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        elapsed = time.monotonic() - self.start_time
        stats = {
            **self.usage_stats,
            "uptime": elapsed,
            "queries_per_hour": self.usage_stats["queries"] / (elapsed / 3600),
            "error_rate": self.usage_stats["errors"] / max(1, self.usage_stats["queries"])
        }
        return stats
    
    async def close(self):
        """Close the HTTP session"""
        await self.session.close()

class SearchResultIterator:
    """Async iterator for search results."""
    
    def __init__(self, client, query: str, count: Optional[int] = None):
        self.client = client
        self.query = query
        self.count = count
        self._results = None
        self._index = 0
        self._initialized = False
    
    def __aiter__(self):
        """Return self as the iterator object."""
        return self
    
    async def __anext__(self):
        """Get the next search result."""
        # Initialize on first iteration
        if not self._initialized:
            await self._initialize()
            
        # Check if we've reached the end of results
        if self._index >= len(self._results or []):
            raise StopAsyncIteration
        
        # Get the next result and convert from SearchResult to dict format
        result = self._results[self._index]
        # Convert SearchResult to dict format to be compatible with the other client
        result_dict = {
            "title": result.title,
            "url": result.url,
            "description": result.description,
            **result.metadata
        }
        self._index += 1
        return result_dict
    
    async def _initialize(self):
        """Initialize the iterator by fetching results."""
        try:
            self._initialized = True
            
            # Prepare request parameters
            results_count = self.count or self.client.config.max_results_per_query
            headers = {
                "X-Subscription-Token": self.client.config.api_key,
                "Accept": "application/json"
            }
            params = {
                "q": self.query,
                "count": min(results_count, 20)  # API limit
            }
            
            # Apply rate limiting
            await self.client.rate_limiter.acquire()
            
            async with self.client.session.get(
                self.client.base_url,
                headers=headers,
                params=params,
                timeout=self.client.config.timeout_seconds
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._results = self.client._process_results(data)
                    # Track usage
                    self.client.usage_stats["queries"] += 1
                    self.client.usage_stats["results"] += len(self._results)
                else:
                    self.client.usage_stats["errors"] += 1
                    raise BraveSearchError(f"API error: {response.status}")
                
        except asyncio.TimeoutError:
            self.client.usage_stats["errors"] += 1
            raise BraveSearchError("Request timed out")
            
        except Exception as e:
            self.client.usage_stats["errors"] += 1
            raise BraveSearchError(f"Search failed: {str(e)}")