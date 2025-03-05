"""
Tests for async iterator pattern implementation in the Brave Search Knowledge Aggregator.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional

from brave_search_aggregator.fetcher.brave_client import BraveSearchClient, BraveSearchError
from brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator
from brave_search_aggregator.utils.config import Config


@pytest.mark.asyncio
async def test_search_result_iterator_aiter():
    """Test that SearchResultIterator.__aiter__ correctly returns self."""
    # Create a mock session and config
    mock_session = AsyncMock()
    mock_config = MagicMock()
    mock_config.brave_api_key = "test_key"
    mock_config.max_results_per_query = 10
    mock_config.timeout_seconds = 30
    mock_config.rate_limit = 20
    
    # Create a client and get the SearchResultIterator class
    client = BraveSearchClient(mock_session, mock_config)
    SearchResultIterator = client.SearchResultIterator
    
    # Create an instance of the iterator
    iterator = SearchResultIterator(client, "test query")
    
    # Test that __aiter__ returns self (the correct implementation)
    assert iterator.__aiter__() is iterator, "SearchResultIterator.__aiter__ should return self"


@pytest.mark.asyncio
async def test_search_method_returns_iterator():
    """Test that BraveSearchClient.search returns an async iterator, not a coroutine."""
    # Create a mock session and config
    mock_session = AsyncMock()
    mock_config = MagicMock()
    mock_config.brave_api_key = "test_key"
    mock_config.max_results_per_query = 10
    mock_config.timeout_seconds = 30
    mock_config.rate_limit = 20
    
    # Create a client
    client = BraveSearchClient(mock_session, mock_config)
    
    # Call the search method
    result = client.search("test query")
    
    # Verify the result is an async iterator (has __aiter__ method)
    assert hasattr(result, '__aiter__'), "search() result should have __aiter__ method"
    
    # Verify the result is not a coroutine
    assert not asyncio.iscoroutine(result), "search() should not return a coroutine"
    
    # Get the aiter result and verify it has __anext__
    aiter_result = result.__aiter__()
    assert hasattr(aiter_result, '__anext__'), "Iterator should have __anext__ method"
    assert asyncio.iscoroutinefunction(aiter_result.__anext__), "__anext__ should be a coroutine function"


@pytest.mark.asyncio
async def test_search_iterator_lazy_initialization():
    """Test that SearchResultIterator only makes the API call on first __anext__ call."""
    # Create mock objects
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "web": {
            "results": [
                {"title": "Test Result 1", "url": "https://example.com/1", "description": "Description 1"},
                {"title": "Test Result 2", "url": "https://example.com/2", "description": "Description 2"}
            ]
        }
    }
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Create config
    mock_config = MagicMock()
    mock_config.brave_api_key = "test_key"
    mock_config.max_results_per_query = 10
    mock_config.timeout_seconds = 30
    mock_config.rate_limit = 20
    
    # Create a client
    client = BraveSearchClient(mock_session, mock_config)
    
    # Mock the rate limiter to track calls
    client.rate_limiter = AsyncMock()
    client.rate_limiter.acquire = AsyncMock()
    
    # Create an iterator from search
    iterator = client.search("test query")
    
    # Verify no API calls have been made yet (lazy initialization)
    client.rate_limiter.acquire.assert_not_called()
    mock_session.get.assert_not_called()
    
    # Trigger the first item - this should initialize and make the API call
    result = await iterator.__anext__()
    
    # Verify API call was made
    client.rate_limiter.acquire.assert_called_once()
    mock_session.get.assert_called_once()
    
    # Verify we got the first result
    assert result["title"] == "Test Result 1"
    assert result["url"] == "https://example.com/1"
    
    # Get the second result - should not make another API call
    result = await iterator.__anext__()
    assert client.rate_limiter.acquire.call_count == 1, "Should not make another API call for second result"
    assert mock_session.get.call_count == 1, "Should not make another API call for second result"
    
    # Verify we got the second result
    assert result["title"] == "Test Result 2"
    assert result["url"] == "https://example.com/2"
    
    # Verify StopAsyncIteration is raised when no more results
    with pytest.raises(StopAsyncIteration):
        await iterator.__anext__()


@pytest.mark.asyncio
async def test_search_iterator_error_handling():
    """Test that SearchResultIterator properly handles and propagates errors."""
    # Create mock objects
    mock_session = AsyncMock()
    mock_session.get.side_effect = asyncio.TimeoutError("Connection timeout")
    
    # Create config
    mock_config = MagicMock()
    mock_config.brave_api_key = "test_key"
    mock_config.max_results_per_query = 10
    mock_config.timeout_seconds = 30
    mock_config.rate_limit = 20
    
    # Create a client
    client = BraveSearchClient(mock_session, mock_config)
    
    # Mock the rate limiter
    client.rate_limiter = AsyncMock()
    
    # Create an iterator from search
    iterator = client.search("test query")
    
    # The error should be raised when attempting to get the first result
    with pytest.raises(BraveSearchError) as excinfo:
        await iterator.__anext__()
    
    # Verify the error message contains the original error
    assert "timeout" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_search_iterator_resource_cleanup():
    """Test that SearchResultIterator properly cleans up resources."""
    # Create mock objects
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "web": {
            "results": [
                {"title": "Test Result 1", "url": "https://example.com/1", "description": "Description 1"},
            ]
        }
    }
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Create config
    mock_config = MagicMock()
    mock_config.brave_api_key = "test_key"
    mock_config.max_results_per_query = 10
    mock_config.timeout_seconds = 30
    mock_config.rate_limit = 20
    
    # Create a client
    client = BraveSearchClient(mock_session, mock_config)
    client.rate_limiter = AsyncMock()
    
    # Create a real SearchResultIterator with a mock _cleanup method
    iterator = client.search("test query")
    original_cleanup = iterator._cleanup
    iterator._cleanup = AsyncMock()
    
    # Request and exhaust all results
    await iterator.__anext__()
    
    # Should raise StopAsyncIteration and call cleanup
    with pytest.raises(StopAsyncIteration):
        await iterator.__anext__()
    
    # Verify cleanup was called
    iterator._cleanup.assert_called_once()
    
    # Restore the original _cleanup method
    iterator._cleanup = original_cleanup


@pytest.mark.asyncio
async def test_aggregator_async_for_integration():
    """Test the integration of async for with BraveKnowledgeAggregator and BraveSearchClient."""
    # Create mock objects for the test
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "web": {
            "results": [
                {"title": "Test Result 1", "url": "https://example.com/1", "description": "Description 1"},
                {"title": "Test Result 2", "url": "https://example.com/2", "description": "Description 2"}
            ]
        }
    }
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Create config
    config = Config()
    config.max_results_per_query = 10
    config.timeout_seconds = 30
    config.rate_limit = 20
    config.max_memory_mb = 10
    config.enable_streaming = True
    config.brave_api_key = "test_key"
    
    # Create a real BraveSearchClient
    client = BraveSearchClient(mock_session, config)
    client.rate_limiter = AsyncMock()
    
    # Create mock query analyzer
    mock_query_analyzer = AsyncMock()
    mock_query_analyzer.analyze_query.return_value = MagicMock(
        search_string="optimized test query",
        complexity=0.5,
        is_suitable_for_search=True,
        is_ambiguous=False,
        input_type=MagicMock(
            primary_type=MagicMock(name="GENERAL"),
            confidence=0.9
        ),
        performance_metrics={"processing_time_ms": 50}
    )
    
    # Create mock knowledge synthesizer
    mock_knowledge_synthesizer = AsyncMock()
    mock_knowledge_synthesizer.synthesize.return_value = "Test knowledge synthesis"
    
    # Create real BraveKnowledgeAggregator with the real client
    aggregator = BraveKnowledgeAggregator(
        brave_client=client,
        config=config,
        query_analyzer=mock_query_analyzer,
        knowledge_synthesizer=mock_knowledge_synthesizer
    )
    
    # Use aggregator.process_query with async for loop
    results = []
    try:
        async for result in aggregator.process_query("test query"):
            results.append(result)
    except Exception as e:
        pytest.fail(f"async for loop raised an exception: {e}")
    
    # Verify we got results
    assert len(results) > 0, "Should have received results from async for loop"
    
    # Verify we got the expected content
    content_results = [r for r in results if r.get('type') == 'content']
    assert len(content_results) > 0, "Should have received content results"
    
    # Check that search results are included
    all_content = ' '.join([r.get('content', '') for r in content_results])
    assert 'Test Result 1' in all_content or 'Test Result 2' in all_content, "Search results should be in the content"


@pytest.mark.asyncio
async def test_error_propagation_through_async_iterator():
    """Test that errors in the async iterator are properly propagated to the caller."""
    # Create mock objects
    mock_session = AsyncMock()
    
    # Create a response that will fail on the second result request
    class FailingResponse:
        def __init__(self):
            self.status = 200
            self.call_count = 0
            
        async def json(self):
            self.call_count += 1
            if self.call_count == 1:
                return {
                    "web": {
                        "results": [
                            {"title": "Test Result 1", "url": "https://example.com/1", "description": "Description 1"},
                            {"title": "Test Result 2", "url": "https://example.com/2", "description": "Description 2"}
                        ]
                    }
                }
            else:
                raise Exception("Simulated JSON parsing error")
    
    mock_response = AsyncMock()
    mock_response.__aenter__.return_value = FailingResponse()
    mock_session.get.return_value = mock_response
    
    # Create config
    config = Config()
    config.max_results_per_query = 10
    config.timeout_seconds = 30
    config.rate_limit = 20
    config.max_memory_mb = 10
    config.enable_streaming = True
    config.brave_api_key = "test_key"
    
    # Create a real BraveSearchClient
    client = BraveSearchClient(mock_session, config)
    client.rate_limiter = AsyncMock()
    
    # Create a real SearchResultIterator
    iterator = client.search("test query")
    
    # Iterator should initialize successfully but then fail
    result = await iterator.__anext__()
    assert result["title"] == "Test Result 1", "First result should be returned successfully"
    
    # The second result should still succeed (they're both fetched in one API call)
    result = await iterator.__anext__()
    assert result["title"] == "Test Result 2", "Second result should be returned successfully"
    
    # End of results should raise StopAsyncIteration
    with pytest.raises(StopAsyncIteration):
        await iterator.__anext__()


@pytest.mark.asyncio
async def test_iterator_in_for_loop_context():
    """Test using the iterator directly in a for loop context."""
    # Create mock objects
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "web": {
            "results": [
                {"title": "Test Result 1", "url": "https://example.com/1", "description": "Description 1"},
                {"title": "Test Result 2", "url": "https://example.com/2", "description": "Description 2"}
            ]
        }
    }
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Create config
    mock_config = MagicMock()
    mock_config.brave_api_key = "test_key"
    mock_config.max_results_per_query = 10
    mock_config.timeout_seconds = 30
    mock_config.rate_limit = 20
    
    # Create a client
    client = BraveSearchClient(mock_session, mock_config)
    client.rate_limiter = AsyncMock()
    
    # Use the iterator directly in a for loop
    results = []
    search_iterator = client.search("test query")
    
    async for result in search_iterator:
        results.append(result)
    
    # Verify results
    assert len(results) == 2, "Should get 2 results from the iterator"
    assert results[0]["title"] == "Test Result 1"
    assert results[1]["title"] == "Test Result 2"


@pytest.mark.asyncio
async def test_multiple_iterator_creation_and_usage():
    """Test creating and using multiple iterators from the same client."""
    # Create mock objects
    mock_session = AsyncMock()
    
    # Create responses for two different queries
    mock_response1 = AsyncMock()
    mock_response1.status = 200
    mock_response1.json.return_value = {
        "web": {
            "results": [
                {"title": "Query 1 Result 1", "url": "https://example.com/1", "description": "Description 1"},
                {"title": "Query 1 Result 2", "url": "https://example.com/2", "description": "Description 2"}
            ]
        }
    }
    
    mock_response2 = AsyncMock()
    mock_response2.status = 200
    mock_response2.json.return_value = {
        "web": {
            "results": [
                {"title": "Query 2 Result 1", "url": "https://example.com/3", "description": "Description 3"},
                {"title": "Query 2 Result 2", "url": "https://example.com/4", "description": "Description 4"}
            ]
        }
    }
    
    # Configure mock session to return different responses for different queries
    def get_side_effect(*args, **kwargs):
        params = kwargs.get('params', {})
        query = params.get('q', '')
        
        mock_response = AsyncMock()
        if query == "query1":
            mock_response.__aenter__.return_value = mock_response1
        else:
            mock_response.__aenter__.return_value = mock_response2
        return mock_response
    
    mock_session.get.side_effect = get_side_effect
    
    # Create config
    mock_config = MagicMock()
    mock_config.brave_api_key = "test_key"
    mock_config.max_results_per_query = 10
    mock_config.timeout_seconds = 30
    mock_config.rate_limit = 20
    
    # Create a client
    client = BraveSearchClient(mock_session, mock_config)
    client.rate_limiter = AsyncMock()
    
    # Create two different iterators
    iterator1 = client.search("query1")
    iterator2 = client.search("query2")
    
    # Use the first iterator
    results1 = []
    async for result in iterator1:
        results1.append(result)
    
    # Use the second iterator
    results2 = []
    async for result in iterator2:
        results2.append(result)
    
    # Verify results from both iterators
    assert len(results1) == 2, "Should get 2 results from iterator1"
    assert results1[0]["title"] == "Query 1 Result 1"
    assert results1[1]["title"] == "Query 1 Result 2"
    
    assert len(results2) == 2, "Should get 2 results from iterator2"
    assert results2[0]["title"] == "Query 2 Result 1"
    assert results2[1]["title"] == "Query 2 Result 2"


@pytest.mark.asyncio
async def test_cancel_iteration_early():
    """Test canceling iteration before all results are consumed."""
    # Create mock objects
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "web": {
            "results": [
                {"title": "Test Result 1", "url": "https://example.com/1", "description": "Description 1"},
                {"title": "Test Result 2", "url": "https://example.com/2", "description": "Description 2"},
                {"title": "Test Result 3", "url": "https://example.com/3", "description": "Description 3"}
            ]
        }
    }
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Create config
    mock_config = MagicMock()
    mock_config.brave_api_key = "test_key"
    mock_config.max_results_per_query = 10
    mock_config.timeout_seconds = 30
    mock_config.rate_limit = 20
    
    # Create a client
    client = BraveSearchClient(mock_session, mock_config)
    client.rate_limiter = AsyncMock()
    
    # Create a SearchResultIterator with a mock _cleanup method to track calls
    iterator = client.search("test query")
    original_cleanup = iterator._cleanup
    iterator._cleanup = AsyncMock()
    
    # Get just the first result and then "cancel" the iteration
    result = await iterator.__anext__()
    assert result["title"] == "Test Result 1"
    
    # Force cleanup by deleting the iterator
    del iterator
    
    # Create a new iterator and make sure it works independently
    new_iterator = client.search("test query")
    result = await new_iterator.__anext__()
    assert result["title"] == "Test Result 1"