"""Brave Search API client implementation."""
import logging
import asyncio
import time
from typing import Dict, Any, AsyncGenerator, AsyncIterator, Optional
import aiohttp
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential
from functools import wraps
from aiohttp.client_exceptions import (
    ClientConnectionError,
    ClientResponseError,
    ServerDisconnectedError,
)

logger = logging.getLogger(__name__)

def retry_on_connection_error(retry_attempts: int = 3, max_wait: float = 8):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(retry_attempts):
                try:
                    return await func(*args, **kwargs)
                except (ClientConnectionError, ServerDisconnectedError) as e:
                    if attempt == retry_attempts - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
                    logger.warning(f"Connection attempt {{attempt+1}} failed, retrying in {{2**attempt}} seconds")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class BraveSearchClient:
    """Client for interacting with Brave Search API."""

    def __init__(self, session: aiohttp.ClientSession, config: Any):
        """Initialize the client with configuration."""
        self.session = session
        self.api_key = config.brave_api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.max_results = config.max_results_per_query
        self.timeout = config.timeout_seconds
        self.rate_limiter = RateLimiter(config.rate_limit)

    async def search(self, query: str, count: Optional[int] = None) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute a search query against Brave Search API with retry logic.
        Returns an async iterator that yields search results one at a time.
        """
        return SearchResultIterator(self, query, count)

class SearchResultIterator:
    """Async iterator for search results."""
    
    def __init__(self, client, query: str, count: Optional[int] = None):
        self.client = client
        self.query = query
        self.count = count
        self._results = None
        self._index = 0
        self._initialized = False
        self._page = 1
        self._total_results = 0
        self._results_yielded = 0
        self._max_retries = 5
        self._retry_jitter = 1
        self._all_results_fetched = False
        self._current_results = []
        
    def __aiter__(self):
        """Return self as the iterator (synchronous method)"""
        print("SearchResultIterator.__aiter__ called!")
        return self
    
    async def __anext__(self):
        """Get the next search result (asynchronous method)."""
        try:
            # If we've reached the end of the current batch and there are more pages, fetch the next page
            if not self._all_results_fetched and (not self._current_results or self._index >= len(self._current_results)):
                await self._fetch_next_page()
                self._index = 0  # Reset index for the new batch
            
            # If we've reached the end of all results
            if self._all_results_fetched and self._index >= len(self._current_results):
                raise StopAsyncIteration
                
            # Get the next result
            result = self._current_results[self._index]
            self._index += 1
            self._results_yielded += 1
            
            # If we've reached the maximum requested count, mark as complete
            if self._results_yielded >= (self.count or self.client.max_results):
                self._all_results_fetched = True
                
            return result
        except IndexError:
            # No more results
            raise StopAsyncIteration
        except Exception as e:
            logger.error(f"Error getting next search result: {str(e)}")
            raise BraveSearchError(f"Iterator error: {str(e)}") from e
    
    async def _fetch_next_page(self):
        """Fetch the next page of results."""
        try:
            # Acquire rate limit token
            await self.client.rate_limiter.acquire()
            
            # Prepare request parameters
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.client.api_key,
                "Connection": "keep-alive",
            }
            params = {
                "q": self.query,
                "count": min(self.count or self.client.max_results, 20),  # API limit
                "page": self._page,
            }
            
            # Make the API request with retries
            for attempt in range(self._max_retries):
                try:
                    async with self.client.session.get(
                        self.client.base_url,
                        headers=headers,
                        params=params,
                        timeout=self.client.timeout,
                    ) as response:
                        logger.debug(f"Brave Search API response status: {response.status}")
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Brave Search API error: {error_text}")
                            raise BraveSearchError(f"API error: {response.status} - {error_text}")
                        
                        data = await response.json()
                        self._current_results = data.get("web", {}).get("results", [])
                        self._total_results = data.get("web", {}).get("total", 0)
                        
                        logger.debug(f"Received {len(self._current_results)} results from Brave Search API, page {self._page}")
                        
                        # Check if this is the last page
                        if not self._current_results or len(self._current_results) < 20 or self._results_yielded + len(self._current_results) >= self._total_results:
                            self._all_results_fetched = True
                        else:
                            self._page += 1  # Increment page for next fetch
                        
                        return
                        
                except (asyncio.TimeoutError, ClientConnectionError, ServerDisconnectedError) as e:
                    logger.warning(f"Request attempt {attempt + 1}/{self._max_retries} failed: {str(e)}")
                    if attempt < self._max_retries - 1:
                        retry_sleep = self._retry_jitter * (2 ** attempt)
                        logger.info(f"Retrying in {retry_sleep} seconds...")
                        await asyncio.sleep(retry_sleep)
                    else:
                        logger.error(f"Max retries ({self._max_retries}) reached. Giving up.")
                        raise
                except Exception as e:
                    logger.error(f"Unexpected error during request: {str(e)}")
                    raise
        
        except BraveSearchError:
            # Just re-raise BraveSearchError, which already has proper context
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search: {str(e)}")
            raise BraveSearchError(f"Search failed: {str(e)}") from e

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
                self.tokens + elapsed * self.token_rate,
            )
            self.last_update = now

            if self.tokens < 1:
                raise BraveSearchError("Rate limit exceeded")

            self.tokens -= 1

class BraveSearchError(Exception):
    """Custom exception for Brave Search errors"""
    pass