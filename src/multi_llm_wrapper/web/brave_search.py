from typing import Dict, Any, List, Optional
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
    ) -> List[SearchResult]:
        """
        Execute search with rate limiting and error handling
        
        Args:
            query: Search query string
            count: Optional number of results to return
            
        Returns:
            List of processed search results
            
        Raises:
            BraveSearchError: For API or processing errors
        """
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()
            
            # Execute search
            results_count = count or self.config.max_results_per_query
            headers = {
                "X-Subscription-Token": self.config.api_key,
                "Accept": "application/json"
            }
            params = {
                "q": query,
                "count": min(results_count, 20)  # API limit
            }
            
            async with self.session.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=self.config.timeout_seconds
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    processed_results = self._process_results(data)
                    
                    # Track usage
                    self.usage_stats["queries"] += 1
                    self.usage_stats["results"] += len(processed_results)
                    
                    return processed_results
                else:
                    self.usage_stats["errors"] += 1
                    raise BraveSearchError(
                        f"API error: {response.status}"
                    )
                    
        except asyncio.TimeoutError:
            self.usage_stats["errors"] += 1
            raise BraveSearchError("Request timed out")
            
        except Exception as e:
            self.usage_stats["errors"] += 1
            raise BraveSearchError(f"Search failed: {str(e)}")
    
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