"""Brave Search API client implementation."""
import logging
import asyncio
import time
from typing import List, Dict, Any
import aiohttp

logger = logging.getLogger(__name__)

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

class BraveSearchClient:
    """Client for interacting with Brave Search API."""
    
    def __init__(self, session: aiohttp.ClientSession, config: Any):
        """Initialize the client with configuration."""
        self.session = session
        self.api_key = config.brave_api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"  # Correct endpoint
        self.max_results = config.max_results_per_query
        self.timeout = config.timeout_seconds
        self.rate_limiter = RateLimiter(config.rate_limit)
        
    async def search(self, query: str, count: int = None) -> List[Dict[str, Any]]:
        """
        Execute a search query against Brave Search API.
        
        Args:
            query: Search query string
            count: Number of results to return (defaults to config.max_results_per_query)
            
        Returns:
            List of search results
            
        Raises:
            BraveSearchError: For API or processing errors
        """
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()
            
            # Use correct headers from working implementation
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
            
            async with self.session.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=self.timeout
            ) as response:
                logger.debug(f"Brave Search API response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    results = data.get("web", {}).get("results", [])
                    logger.debug(f"Received {len(results)} results from Brave Search API")
                    return results
                else:
                    error_text = await response.text()
                    logger.error(f"Brave Search API error: {error_text}")
                    raise BraveSearchError(f"API error: {response.status} - {error_text}")
                    
        except asyncio.TimeoutError:
            logger.error("Brave Search API request timed out")
            raise BraveSearchError("Request timed out")
            
        except Exception as e:
            logger.error(f"Brave Search API request failed: {str(e)}")
            raise BraveSearchError(f"Search failed: {str(e)}")