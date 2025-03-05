"""
Content fetcher for retrieving and processing content from URLs.
"""
import asyncio
import logging
import time
from typing import Dict, List, Set, Any, Optional, AsyncIterator, Tuple
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup
import re
import json

from ..utils.config import Config, FetcherConfig
from ..utils.error_handler import ErrorHandler, ErrorContext

logger = logging.getLogger(__name__)

class ContentFetchError(Exception):
    """Exception raised for content fetching errors."""
    pass

class RateLimitExceededError(ContentFetchError):
    """Exception raised when rate limit is exceeded."""
    pass

class FetchTimeoutError(ContentFetchError):
    """Exception raised when fetching times out."""
    pass

class ContentExtractionError(ContentFetchError):
    """Exception raised when content extraction fails."""
    pass

class ContentFetcher:
    """
    Fetches and processes content from URLs with rate limiting and caching.
    Supports streaming results for real-time processing.
    """
    
    def __init__(self, session: aiohttp.ClientSession, config: Config):
        """
        Initialize the content fetcher.
        
        Args:
            session: aiohttp ClientSession for making HTTP requests
            config: Configuration object
        """
        self.session = session
        self.config = config
        self.fetcher_config = config.fetcher if hasattr(config, 'fetcher') else FetcherConfig()
        self.error_handler = ErrorHandler()
        
        # Rate limiting - global and per domain
        self.global_semaphore = asyncio.Semaphore(self.fetcher_config.max_concurrent_fetches)
        self.domain_semaphores: Dict[str, asyncio.Semaphore] = {}
        
        # Cache of fetched content
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = self.fetcher_config.cache_ttl_seconds
        self.cache_lock = asyncio.Lock()
        
        # Set of known content types that can be processed
        self.supported_content_types = {
            'text/html': self._extract_html_content,
            'text/plain': self._extract_text_content,
            'application/json': self._extract_json_content,
            'application/xml': self._extract_xml_content,
            'text/xml': self._extract_xml_content,
        }
        
        # Tracking active fetches to avoid duplicates
        self.active_fetches: Set[str] = set()
        self.active_fetches_lock = asyncio.Lock()
    
    async def fetch_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract content from a URL.
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Dict containing extracted content and metadata
        """
        try:
            # Check cache first
            cached_content = await self._check_cache(url)
            if cached_content:
                logger.debug(f"Cache hit for {url}")
                return cached_content
            
            # Acquire rate limit token
            domain = urlparse(url).netloc
            await self._acquire_rate_limit(domain)
            
            # Track this fetch as active
            async with self.active_fetches_lock:
                if url in self.active_fetches:
                    # Wait for another fetch of the same URL to complete
                    while url in self.active_fetches:
                        await asyncio.sleep(0.1)
                    # Check cache again after waiting
                    cached_content = await self._check_cache(url)
                    if cached_content:
                        return cached_content
                self.active_fetches.add(url)
            
            try:
                # Perform the fetch with timeout
                start_time = time.time()
                async with self.global_semaphore:
                    logger.debug(f"Fetching content from {url}")
                    try:
                        async with self.session.get(
                            url,
                            timeout=self.fetcher_config.timeout_seconds,
                            allow_redirects=self.fetcher_config.allow_redirects,
                            max_redirects=self.fetcher_config.max_redirects,
                            headers=self.fetcher_config.headers
                        ) as response:
                            # Check status code
                            if response.status != 200:
                                raise ContentFetchError(
                                    f"Failed to fetch content: HTTP {response.status}"
                                )
                            
                            # Get content type
                            content_type = response.headers.get('Content-Type', '').split(';')[0].lower()
                            
                            # Check content size
                            content_length = int(response.headers.get('Content-Length', '0'))
                            if content_length > self.fetcher_config.max_content_size_bytes:
                                raise ContentFetchError(
                                    f"Content too large: {content_length} bytes"
                                )
                            
                            # Read content with size limit
                            content = await response.read()
                            if len(content) > self.fetcher_config.max_content_size_bytes:
                                raise ContentFetchError(
                                    f"Content too large: {len(content)} bytes"
                                )
                            
                            # Extract text content based on content type
                            extracted_content = await self._extract_content(content, content_type, url)
                            
                            # Create result
                            fetch_time = time.time() - start_time
                            result = {
                                'url': url,
                                'content': extracted_content,
                                'content_type': content_type,
                                'fetch_time_ms': round(fetch_time * 1000),
                                'timestamp': time.time(),
                                'size_bytes': len(content),
                                'headers': dict(response.headers),
                                'status': response.status
                            }
                            
                            # Cache the result
                            await self._update_cache(url, result)
                            
                            return result
                    except asyncio.TimeoutError:
                        raise FetchTimeoutError(f"Timeout fetching {url}")
                    except aiohttp.ClientError as e:
                        raise ContentFetchError(f"HTTP client error: {str(e)}")
            finally:
                # Remove from active fetches
                async with self.active_fetches_lock:
                    self.active_fetches.discard(url)
        
        except Exception as e:
            # Handle error with context
            error_context = ErrorContext(
                operation="fetch_content",
                partial_results={"url": url},
                metadata={
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )
            logger.error(f"Error fetching content from {url}: {str(e)}")
            
            # Return error result
            return {
                'url': url,
                'content': '',
                'content_type': 'error',
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': time.time(),
                'fetch_time_ms': 0,
                'success': False
            }
    
    async def fetch_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch content from multiple URLs in parallel.
        
        Args:
            urls: List of URLs to fetch
            
        Returns:
            List of content results
        """
        # Create tasks for each URL
        tasks = [self.fetch_content(url) for url in urls]
        
        # Run tasks concurrently with controlled concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, converting exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Convert exception to error result
                processed_results.append({
                    'url': urls[i],
                    'content': '',
                    'content_type': 'error',
                    'error': str(result),
                    'error_type': type(result).__name__,
                    'timestamp': time.time(),
                    'fetch_time_ms': 0,
                    'success': False
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def fetch_stream(self, urls: List[str]) -> AsyncIterator[Dict[str, Any]]:
        """
        Fetch content from multiple URLs and yield results as they complete.
        
        Args:
            urls: List of URLs to fetch
            
        Yields:
            Content results as they become available
        """
        # Track pending tasks
        pending_tasks = {
            asyncio.create_task(self.fetch_content(url)): url 
            for url in urls
        }
        
        # Yield results as they complete
        while pending_tasks:
            # Wait for the first task to complete
            done, pending = await asyncio.wait(
                pending_tasks.keys(),
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Process completed tasks
            for task in done:
                url = pending_tasks.pop(task)
                try:
                    result = task.result()
                    # Add URL to result (redundant but for clarity)
                    result['url'] = url
                    yield result
                except Exception as e:
                    # Yield error result
                    yield {
                        'url': url,
                        'content': '',
                        'content_type': 'error',
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'timestamp': time.time(),
                        'fetch_time_ms': 0,
                        'success': False
                    }
    
    async def _extract_content(self, raw_content: bytes, content_type: str, url: str) -> str:
        """
        Extract text content from raw content based on content type.
        
        Args:
            raw_content: Raw content bytes
            content_type: Content MIME type
            url: Source URL
            
        Returns:
            Extracted text content
        """
        # Find appropriate extractor function
        extractor = self.supported_content_types.get(content_type)
        
        # If no specific extractor is found, try to guess based on URL or content
        if not extractor:
            # Try to infer content type from URL extension
            url_path = urlparse(url).path.lower()
            if url_path.endswith('.html') or url_path.endswith('.htm'):
                extractor = self._extract_html_content
            elif url_path.endswith('.txt'):
                extractor = self._extract_text_content
            elif url_path.endswith('.json'):
                extractor = self._extract_json_content
            elif url_path.endswith('.xml'):
                extractor = self._extract_xml_content
            else:
                # Try to detect content type from content
                try:
                    # Try decoding as text
                    decoded = raw_content.decode('utf-8', errors='ignore')
                    # Check if it looks like HTML
                    if '<html' in decoded.lower() and ('<body' in decoded.lower() or '<div' in decoded.lower()):
                        extractor = self._extract_html_content
                    # Check if it looks like JSON
                    elif decoded.strip().startswith('{') and decoded.strip().endswith('}'):
                        extractor = self._extract_json_content
                    # Check if it looks like XML
                    elif decoded.strip().startswith('<') and decoded.strip().endswith('>'):
                        extractor = self._extract_xml_content
                    else:
                        # Default to plain text
                        extractor = self._extract_text_content
                except Exception:
                    # Default to plain text if detection fails
                    extractor = self._extract_text_content
        
        # Extract content using appropriate method
        try:
            if extractor:
                content = await extractor(raw_content, url)
                return content
            else:
                # Fallback to plain text
                return raw_content.decode('utf-8', errors='ignore')
        except Exception as e:
            # Handle extraction error
            logger.error(f"Error extracting content from {url}: {str(e)}")
            raise ContentExtractionError(f"Failed to extract content: {str(e)}")
    
    async def _extract_html_content(self, html_content: bytes, url: str) -> str:
        """
        Extract text content from HTML.
        
        Args:
            html_content: Raw HTML content
            url: Source URL
            
        Returns:
            Extracted text content
        """
        try:
            # Decode HTML content
            decoded_html = html_content.decode('utf-8', errors='ignore')
            
            # Parse HTML
            soup = BeautifulSoup(decoded_html, 'html.parser')
            
            # Remove script and style elements
            for script_or_style in soup(['script', 'style', 'iframe', 'noscript']):
                script_or_style.decompose()
            
            # Remove hidden elements
            for hidden in soup.find_all(style=re.compile(r'display:\s*none')):
                hidden.decompose()
            
            # Extract text from remaining HTML
            text = soup.get_text(separator='\n')
            
            # Remove extra whitespace and empty lines
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting HTML content: {str(e)}")
            raise ContentExtractionError(f"HTML extraction error: {str(e)}")
    
    async def _extract_text_content(self, text_content: bytes, url: str) -> str:
        """
        Extract text content from plain text.
        
        Args:
            text_content: Raw text content
            url: Source URL
            
        Returns:
            Extracted text content
        """
        try:
            # Decode text content
            decoded_text = text_content.decode('utf-8', errors='ignore')
            
            # Remove extra whitespace and empty lines
            lines = [line.strip() for line in decoded_text.splitlines() if line.strip()]
            text = '\n'.join(lines)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text content: {str(e)}")
            raise ContentExtractionError(f"Text extraction error: {str(e)}")
    
    async def _extract_json_content(self, json_content: bytes, url: str) -> str:
        """
        Extract text content from JSON.
        
        Args:
            json_content: Raw JSON content
            url: Source URL
            
        Returns:
            Extracted text content
        """
        try:
            # Decode JSON content
            decoded_json = json_content.decode('utf-8', errors='ignore')
            
            # Parse JSON
            data = json.loads(decoded_json)
            
            # Convert to string representation
            if isinstance(data, dict):
                # Try to extract meaningful content from common JSON structures
                if 'content' in data:
                    return str(data['content'])
                elif 'text' in data:
                    return str(data['text'])
                elif 'description' in data:
                    return str(data['description'])
                elif 'body' in data:
                    return str(data['body'])
                else:
                    # Use the entire JSON content
                    return json.dumps(data, indent=2)
            else:
                # Use the entire JSON content
                return json.dumps(data, indent=2)
        except Exception as e:
            logger.error(f"Error extracting JSON content: {str(e)}")
            raise ContentExtractionError(f"JSON extraction error: {str(e)}")
    
    async def _extract_xml_content(self, xml_content: bytes, url: str) -> str:
        """
        Extract text content from XML.
        
        Args:
            xml_content: Raw XML content
            url: Source URL
            
        Returns:
            Extracted text content
        """
        try:
            # Decode XML content
            decoded_xml = xml_content.decode('utf-8', errors='ignore')
            
            # Parse XML
            soup = BeautifulSoup(decoded_xml, 'xml')
            
            # Extract text from XML
            text = soup.get_text(separator='\n')
            
            # Remove extra whitespace and empty lines
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting XML content: {str(e)}")
            raise ContentExtractionError(f"XML extraction error: {str(e)}")
    
    async def _acquire_rate_limit(self, domain: str) -> None:
        """
        Acquire rate limit token for a domain.
        
        Args:
            domain: Domain name
        """
        # Get or create domain semaphore
        if domain not in self.domain_semaphores:
            self.domain_semaphores[domain] = asyncio.Semaphore(
                self.fetcher_config.max_requests_per_domain
            )
        
        # Try to acquire domain semaphore with timeout
        try:
            domain_acquired = False
            domain_semaphore = self.domain_semaphores[domain]
            
            # Try to acquire with timeout
            domain_acquired = await asyncio.wait_for(
                domain_semaphore.acquire(),
                timeout=self.fetcher_config.semaphore_timeout_seconds
            )
            
            if not domain_acquired:
                raise RateLimitExceededError(f"Domain rate limit exceeded for {domain}")
            
            # Schedule semaphore release
            asyncio.create_task(self._release_after_delay(
                domain_semaphore,
                self.fetcher_config.domain_rate_limit_delay_seconds
            ))
        
        except asyncio.TimeoutError:
            raise RateLimitExceededError(f"Timeout acquiring rate limit for {domain}")
    
    async def _release_after_delay(self, semaphore: asyncio.Semaphore, delay: float) -> None:
        """
        Release a semaphore after a delay.
        
        Args:
            semaphore: Semaphore to release
            delay: Delay in seconds
        """
        try:
            await asyncio.sleep(delay)
        finally:
            semaphore.release()
    
    async def _check_cache(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Check if a URL is in the cache and not expired.
        
        Args:
            url: URL to check
            
        Returns:
            Cached content or None
        """
        async with self.cache_lock:
            if url in self.cache:
                cached = self.cache[url]
                # Check if cache entry is still valid
                if time.time() - cached['timestamp'] < self.cache_ttl:
                    return cached
                else:
                    # Remove expired entry
                    del self.cache[url]
        return None
    
    async def _update_cache(self, url: str, content: Dict[str, Any]) -> None:
        """
        Update the cache with new content.
        
        Args:
            url: URL to cache
            content: Content to cache
        """
        async with self.cache_lock:
            self.cache[url] = content
            
            # Clean cache if it's too large
            if len(self.cache) > self.fetcher_config.max_cache_size:
                # Remove oldest entries
                entries = sorted(
                    self.cache.items(),
                    key=lambda x: x[1]['timestamp']
                )
                # Keep only the newest entries
                self.cache = dict(entries[-(self.fetcher_config.max_cache_size // 2):])