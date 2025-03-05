"""
Tests for the ContentFetcher component of the Brave Search Knowledge Aggregator.
"""
import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

import aiohttp
from aiohttp.client_reqrep import ClientResponse
from aiohttp import StreamReader
from bs4 import BeautifulSoup

from brave_search_aggregator.fetcher.content_fetcher import (
    ContentFetcher, ContentFetchError, RateLimitExceededError, 
    FetchTimeoutError, ContentExtractionError
)
from brave_search_aggregator.utils.config import Config, FetcherConfig


class MockResponse:
    """Mock response for aiohttp.ClientResponse."""
    def __init__(
        self, 
        status: int = 200, 
        content: bytes = b"", 
        content_type: str = "text/html", 
        headers: Dict[str, str] = None
    ):
        self.status = status
        self._content = content
        self.headers = aiohttp.CIMultiDictProxy(
            aiohttp.CIMultiDict(headers or {"Content-Type": content_type})
        )
        
    async def read(self):
        return self._content
        
    async def text(self):
        return self._content.decode("utf-8")
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_session():
    """Provide a mock aiohttp.ClientSession."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    return session


@pytest.fixture
def fetcher_config():
    """Provide a basic FetcherConfig for testing."""
    return FetcherConfig(
        timeout_seconds=5,
        max_content_size_bytes=1024 * 10,  # 10KB for tests
        max_concurrent_fetches=3,
        max_requests_per_domain=2,
        semaphore_timeout_seconds=1.0,
        domain_rate_limit_delay_seconds=0.1,
        cache_ttl_seconds=10  # Short TTL for tests
    )


@pytest.fixture
def config(fetcher_config):
    """Provide a Config object with the test FetcherConfig."""
    config = Config()
    config.fetcher = fetcher_config
    return config


@pytest.fixture
def content_fetcher(mock_session, config):
    """Provide a ContentFetcher instance for testing."""
    return ContentFetcher(mock_session, config)


@pytest.mark.asyncio
async def test_fetch_content_success(content_fetcher, mock_session):
    """Test successful content fetching."""
    # Mock response with HTML content
    html_content = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Test Content</h1>
            <p>This is a test paragraph.</p>
            <script>alert('This should be removed');</script>
            <div style="display:none">This should be hidden.</div>
        </body>
    </html>
    """
    mock_response = MockResponse(
        status=200,
        content=html_content.encode('utf-8'),
        content_type="text/html",
        headers={
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": str(len(html_content))
        }
    )
    
    # Configure mock session to return the response
    mock_session.get.return_value = mock_response
    
    # Fetch content
    url = "https://example.com/test"
    result = await content_fetcher.fetch_content(url)
    
    # Verify mock was called correctly
    mock_session.get.assert_called_once()
    call_args = mock_session.get.call_args[0]
    call_kwargs = mock_session.get.call_args[1]
    assert call_args[0] == url
    assert call_kwargs["timeout"] == content_fetcher.fetcher_config.timeout_seconds
    assert call_kwargs["allow_redirects"] == content_fetcher.fetcher_config.allow_redirects
    
    # Verify result structure
    assert result["url"] == url
    assert result["content_type"] == "text/html; charset=utf-8"
    assert result["status"] == 200
    assert isinstance(result["fetch_time_ms"], int)
    assert isinstance(result["timestamp"], float)
    assert isinstance(result["size_bytes"], int)
    assert isinstance(result["headers"], dict)
    
    # Verify content extraction - should include text but not scripts or hidden content
    assert "Test Content" in result["content"]
    assert "This is a test paragraph" in result["content"]
    assert "alert" not in result["content"]
    assert "This should be hidden" not in result["content"]


@pytest.mark.asyncio
async def test_fetch_content_different_types(content_fetcher, mock_session):
    """Test fetching different content types."""
    # 1. Test JSON content
    json_content = {"title": "Test JSON", "data": {"key": "value"}}
    json_bytes = json.dumps(json_content).encode('utf-8')
    
    mock_session.get.return_value = MockResponse(
        status=200,
        content=json_bytes,
        content_type="application/json",
        headers={"Content-Type": "application/json"}
    )
    
    url = "https://example.com/api/data.json"
    json_result = await content_fetcher.fetch_content(url)
    
    assert json_result["content_type"] == "application/json"
    # Value from data.key should be in the extracted content
    assert "value" in json_result["content"]
    
    # 2. Test Plain Text content
    text_content = "This is a plain text document\nWith multiple lines\nAnd some formatting."
    
    mock_session.get.return_value = MockResponse(
        status=200,
        content=text_content.encode('utf-8'),
        content_type="text/plain",
        headers={"Content-Type": "text/plain"}
    )
    
    url = "https://example.com/text-file.txt"
    text_result = await content_fetcher.fetch_content(url)
    
    assert text_result["content_type"] == "text/plain"
    assert "plain text document" in text_result["content"]
    assert "multiple lines" in text_result["content"]
    
    # 3. Test XML content
    xml_content = """
    <?xml version="1.0" encoding="UTF-8"?>
    <root>
        <item id="1">
            <name>Test Item</name>
            <description>This is a test XML item</description>
        </item>
    </root>
    """
    
    mock_session.get.return_value = MockResponse(
        status=200,
        content=xml_content.encode('utf-8'),
        content_type="application/xml",
        headers={"Content-Type": "application/xml"}
    )
    
    url = "https://example.com/data.xml"
    xml_result = await content_fetcher.fetch_content(url)
    
    assert xml_result["content_type"] == "application/xml"
    assert "Test Item" in xml_result["content"]
    assert "test XML item" in xml_result["content"]


@pytest.mark.asyncio
async def test_content_type_detection(content_fetcher, mock_session):
    """Test content type detection when no explicit type is provided."""
    # HTML content with no content type header
    html_content = "<html><body><h1>Test</h1><p>Paragraph</p></body></html>"
    
    mock_session.get.return_value = MockResponse(
        status=200,
        content=html_content.encode('utf-8'),
        content_type="",  # No content type
        headers={}  # Empty headers
    )
    
    # URL has .html extension to help detection
    url = "https://example.com/test.html"
    result = await content_fetcher.fetch_content(url)
    
    # Should detect HTML from URL extension or content
    assert "Test" in result["content"]
    assert "Paragraph" in result["content"]
    
    # Try JSON with no content type header but .json extension
    json_content = '{"key": "value", "array": [1, 2, 3]}'
    
    mock_session.get.return_value = MockResponse(
        status=200,
        content=json_content.encode('utf-8'),
        content_type="",  # No content type
        headers={}  # Empty headers
    )
    
    url = "https://example.com/data.json"
    result = await content_fetcher.fetch_content(url)
    
    # Should detect JSON from URL extension or content
    assert "value" in result["content"]
    assert "[1, 2, 3]" in result["content"] or "1" in result["content"]
    
    # Try detecting HTML from content only
    mock_session.get.return_value = MockResponse(
        status=200,
        content=html_content.encode('utf-8'),
        content_type="",  # No content type
        headers={}  # Empty headers
    )
    
    url = "https://example.com/no-extension"  # No extension to help
    result = await content_fetcher.fetch_content(url)
    
    # Should detect HTML from content
    assert "Test" in result["content"]
    assert "Paragraph" in result["content"]


@pytest.mark.asyncio
async def test_fetch_error_handling(content_fetcher, mock_session):
    """Test error handling during content fetching."""
    # 1. Test HTTP error status
    mock_session.get.return_value = MockResponse(
        status=404,
        content=b"Not Found",
        content_type="text/plain",
        headers={"Content-Type": "text/plain"}
    )
    
    url = "https://example.com/not-found"
    result = await content_fetcher.fetch_content(url)
    
    # Should return error result
    assert result["content_type"] == "error"
    assert "error" in result
    assert "Failed to fetch content: HTTP 404" in result["error"]
    assert result["url"] == url
    assert result["success"] == False
    
    # 2. Test timeout error
    mock_session.get.side_effect = asyncio.TimeoutError("Connection timed out")
    
    url = "https://example.com/timeout"
    result = await content_fetcher.fetch_content(url)
    
    # Should return error result
    assert result["content_type"] == "error"
    assert "error" in result
    assert "timeout" in result["error"].lower()
    assert result["url"] == url
    assert result["success"] == False
    
    # 3. Test client connection error
    mock_session.get.side_effect = aiohttp.ClientError("Connection refused")
    
    url = "https://example.com/connection-error"
    result = await content_fetcher.fetch_content(url)
    
    # Should return error result
    assert result["content_type"] == "error"
    assert "error" in result
    assert "HTTP client error" in result["error"]
    assert result["url"] == url
    assert result["success"] == False
    
    # 4. Test content too large error
    large_content = b"x" * (content_fetcher.fetcher_config.max_content_size_bytes + 1)
    mock_session.get.side_effect = None
    mock_session.get.return_value = MockResponse(
        status=200,
        content=large_content,
        content_type="text/plain",
        headers={
            "Content-Type": "text/plain",
            "Content-Length": str(len(large_content))
        }
    )
    
    url = "https://example.com/large-content"
    result = await content_fetcher.fetch_content(url)
    
    # Should return error result
    assert result["content_type"] == "error"
    assert "error" in result
    assert "Content too large" in result["error"]
    assert result["url"] == url
    assert result["success"] == False


@pytest.mark.asyncio
async def test_cache_behavior(content_fetcher, mock_session):
    """Test caching behavior of the content fetcher."""
    # Configure mock response
    html_content = "<html><body><h1>Cached Content</h1></body></html>"
    mock_response = MockResponse(
        status=200,
        content=html_content.encode('utf-8'),
        content_type="text/html",
        headers={"Content-Type": "text/html"}
    )
    mock_session.get.return_value = mock_response
    
    # First request - should call the session
    url = "https://example.com/cached"
    result1 = await content_fetcher.fetch_content(url)
    
    assert "Cached Content" in result1["content"]
    assert mock_session.get.call_count == 1
    
    # Second request to same URL - should use cache
    result2 = await content_fetcher.fetch_content(url)
    
    assert "Cached Content" in result2["content"]
    assert mock_session.get.call_count == 1  # Still 1, indicating cache hit
    
    # Wait for cache to expire
    await asyncio.sleep(content_fetcher.cache_ttl + 0.1)
    
    # Third request - should call the session again
    result3 = await content_fetcher.fetch_content(url)
    
    assert "Cached Content" in result3["content"]
    assert mock_session.get.call_count == 2  # Now 2, indicating cache miss
    
    # Test different URL doesn't use cache
    url2 = "https://example.com/different"
    result4 = await content_fetcher.fetch_content(url2)
    
    assert "Cached Content" in result4["content"]
    assert mock_session.get.call_count == 3  # Now 3, different URL


@pytest.mark.asyncio
async def test_rate_limiting(content_fetcher, mock_session):
    """Test rate limiting functionality."""
    # Configure mock to return valid response
    mock_response = MockResponse(
        status=200,
        content=b"Test content",
        content_type="text/plain"
    )
    mock_session.get.return_value = mock_response
    
    # Patch the _acquire_rate_limit method to track calls
    original_acquire = content_fetcher._acquire_rate_limit
    acquire_calls = []
    
    async def track_acquire(domain):
        acquire_calls.append(domain)
        await original_acquire(domain)
    
    content_fetcher._acquire_rate_limit = track_acquire
    
    # Make requests to different domains
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.org/page1",
        "https://example.net/page1"
    ]
    
    # Fetch concurrently
    tasks = [content_fetcher.fetch_content(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    # Verify all succeeded
    assert all(r["content_type"] != "error" for r in results)
    
    # Verify rate limiting was applied per domain
    assert "example.com" in acquire_calls
    assert "example.org" in acquire_calls
    assert "example.net" in acquire_calls
    
    # Count occurrences of each domain
    domain_counts = {}
    for domain in acquire_calls:
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    # example.com should be called twice (for two different URLs)
    assert domain_counts["example.com"] == 2
    
    # Reset the method
    content_fetcher._acquire_rate_limit = original_acquire


@pytest.mark.asyncio
async def test_fetch_multiple(content_fetcher, mock_session):
    """Test fetching multiple URLs concurrently."""
    # Configure mock to return different content for different URLs
    async def mock_get(url, **kwargs):
        if "success" in url:
            return MockResponse(
                status=200,
                content=f"Content for {url}".encode('utf-8'),
                content_type="text/plain"
            )
        elif "error" in url:
            return MockResponse(
                status=404,
                content=b"Not Found",
                content_type="text/plain"
            )
        elif "timeout" in url:
            raise asyncio.TimeoutError("Connection timed out")
        else:
            return MockResponse(
                status=200,
                content=b"Default content",
                content_type="text/plain"
            )
    
    mock_session.get.side_effect = mock_get
    
    # Create list of URLs
    urls = [
        "https://example.com/success1",
        "https://example.org/success2",
        "https://example.net/error",
        "https://example.com/timeout"
    ]
    
    # Fetch multiple
    results = await content_fetcher.fetch_multiple(urls)
    
    # Verify correct number of results
    assert len(results) == len(urls)
    
    # Verify success results
    success_results = [r for r in results if r["url"] == "https://example.com/success1" or r["url"] == "https://example.org/success2"]
    assert len(success_results) == 2
    assert all("Content for" in r["content"] for r in success_results)
    
    # Verify error result
    error_result = next(r for r in results if r["url"] == "https://example.net/error")
    assert error_result["content_type"] == "error"
    assert "HTTP 404" in error_result["error"]
    
    # Verify timeout result
    timeout_result = next(r for r in results if r["url"] == "https://example.com/timeout")
    assert timeout_result["content_type"] == "error"
    assert "timeout" in timeout_result["error"].lower()


@pytest.mark.asyncio
async def test_fetch_stream(content_fetcher, mock_session):
    """Test streaming results from multiple URLs."""
    # Configure mock to return different content for different URLs
    async def mock_get(url, **kwargs):
        if "fast" in url:
            return MockResponse(
                status=200,
                content=f"Fast content for {url}".encode('utf-8'),
                content_type="text/plain"
            )
        elif "slow" in url:
            # Delay to simulate slow response
            await asyncio.sleep(0.2)
            return MockResponse(
                status=200,
                content=f"Slow content for {url}".encode('utf-8'),
                content_type="text/plain"
            )
        elif "error" in url:
            return MockResponse(
                status=500,
                content=b"Server Error",
                content_type="text/plain"
            )
        else:
            return MockResponse(
                status=200,
                content=b"Default content",
                content_type="text/plain"
            )
    
    mock_session.get.side_effect = mock_get
    
    # Create list of URLs
    urls = [
        "https://example.com/fast1",
        "https://example.org/slow1",
        "https://example.net/error",
        "https://example.com/fast2",
        "https://example.org/slow2"
    ]
    
    # Collect streamed results
    results = []
    async for result in content_fetcher.fetch_stream(urls):
        results.append(result)
    
    # Verify all URLs have results
    assert len(results) == len(urls)
    
    # Verify all URLs are represented
    result_urls = [r["url"] for r in results]
    for url in urls:
        assert url in result_urls
    
    # Verify fast results come before slow results
    # This isn't guaranteed due to async nature, but likely with our mock delays
    fast_indexes = [i for i, r in enumerate(results) if "fast" in r["url"]]
    slow_indexes = [i for i, r in enumerate(results) if "slow" in r["url"]]
    if fast_indexes and slow_indexes:
        assert min(fast_indexes) < max(slow_indexes)
    
    # Verify errors are handled properly
    error_results = [r for r in results if "error" in r["url"]]
    assert len(error_results) == 1
    assert error_results[0]["content_type"] == "error"


@pytest.mark.asyncio
async def test_duplicate_requests(content_fetcher, mock_session):
    """Test handling of duplicate requests for the same URL."""
    # Configure mock response with delay to test simultaneous requests
    html_content = "<html><body><h1>Duplicate Test</h1></body></html>"
    
    call_count = 0
    
    async def delayed_response(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.2)  # Add delay
        return MockResponse(
            status=200,
            content=html_content.encode('utf-8'),
            content_type="text/html"
        )
    
    mock_session.get.side_effect = delayed_response
    
    # Make concurrent requests to the same URL
    url = "https://example.com/duplicate"
    tasks = [content_fetcher.fetch_content(url) for _ in range(3)]
    results = await asyncio.gather(*tasks)
    
    # Verify all requests succeeded
    assert all("Duplicate Test" in r["content"] for r in results)
    
    # The session.get should only be called once due to deduplication
    assert call_count == 1


@pytest.mark.asyncio
async def test_content_extraction_error_handling(content_fetcher, mock_session):
    """Test handling of content extraction errors."""
    # Mock response with valid status but corrupted content
    corrupted_content = b"\x80\x81\xFF\xFE"  # Invalid UTF-8
    
    mock_session.get.return_value = MockResponse(
        status=200,
        content=corrupted_content,
        content_type="text/html"
    )
    
    # Fetch should not raise but return error result
    url = "https://example.com/corrupted"
    result = await content_fetcher.fetch_content(url)
    
    # Result should indicate error but not crash
    assert result["url"] == url
    assert result["success"] == False
    assert result["content_type"] == "error"
    assert "error" in result


@pytest.mark.asyncio
async def test_cache_size_management(content_fetcher, mock_session):
    """Test management of cache size."""
    # Set a very small max cache size
    content_fetcher.fetcher_config.max_cache_size = 3
    
    # Mock response generator
    def create_mock_response(index):
        return MockResponse(
            status=200,
            content=f"Content {index}".encode('utf-8'),
            content_type="text/plain"
        )
    
    # Fetch content for multiple URLs to fill cache
    mock_session.get.return_value = create_mock_response(1)
    await content_fetcher.fetch_content("https://example.com/page1")
    
    mock_session.get.return_value = create_mock_response(2)
    await content_fetcher.fetch_content("https://example.com/page2")
    
    mock_session.get.return_value = create_mock_response(3)
    await content_fetcher.fetch_content("https://example.com/page3")
    
    # Cache should have 3 items now
    assert len(content_fetcher.cache) == 3
    
    # Add a 4th item to trigger cache cleanup
    mock_session.get.return_value = create_mock_response(4)
    await content_fetcher.fetch_content("https://example.com/page4")
    
    # Cache should still have max items (newer ones)
    assert len(content_fetcher.cache) <= content_fetcher.fetcher_config.max_cache_size
    
    # The oldest item should be removed (page1)
    assert "https://example.com/page1" not in content_fetcher.cache
    
    # Re-fetch page1 to verify it's not in cache (should call session.get again)
    mock_session.get.reset_mock()
    mock_session.get.return_value = create_mock_response(1)
    await content_fetcher.fetch_content("https://example.com/page1")
    
    # Should have made a new request since page1 was removed from cache
    mock_session.get.assert_called_once()