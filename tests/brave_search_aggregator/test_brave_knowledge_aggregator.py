import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

from brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalysis

class AsyncIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            item = self.items[self.index]
            self.index += 1
            return item
        except IndexError:
            raise StopAsyncIteration

class SearchMock:
    def __init__(self, items):
        self.items = items

    def __call__(self, *args, **kwargs):
        return AsyncIterator(self.items)

@pytest.fixture
def mock_brave_client():
    client = AsyncMock(spec=BraveSearchClient)
    results = [
        {
            'title': 'Test Result 1',
            'url': 'https://example.com/1',
            'description': 'Description 1'
        },
        {
            'title': 'Test Result 2',
            'url': 'https://example.com/2',
            'description': 'Description 2'
        }
    ]
    # Make search return an async iterator when called
    client.search = SearchMock(results)
    return client

@pytest.fixture
def mock_query_analyzer():
    analyzer = AsyncMock()
    analyzer.analyze.return_value = "Test query analysis insights"
    return analyzer

@pytest.fixture
def mock_knowledge_synthesizer():
    synthesizer = AsyncMock()
    synthesizer.synthesize.return_value = "Test knowledge synthesis"
    return synthesizer

@pytest.fixture
def aggregator(mock_brave_client, mock_query_analyzer, mock_knowledge_synthesizer):
    return BraveKnowledgeAggregator(
        brave_client=mock_brave_client,
        query_analyzer=mock_query_analyzer,
        knowledge_synthesizer=mock_knowledge_synthesizer
    )

@pytest.mark.asyncio
async def test_process_query_success(aggregator):
    """Test successful query processing with proper response format."""
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)

    # Verify response structure
    assert len(results) >= 3  # Initial content, search results, and final content
    assert all(r['type'] in ['content', 'error'] for r in results)

    # Verify content format
    content_results = [r for r in results if r['type'] == 'content']
    assert len(content_results) > 0
    content = content_results[-1]['content']
    assert 'Test Result 1' in content
    assert 'Test Result 2' in content
    assert 'Knowledge synthesis' in content

@pytest.mark.asyncio
async def test_process_query_with_error(aggregator, mock_brave_client):
    """Test error handling in query processing."""
    def raise_error(*args, **kwargs):
        raise Exception("API Error")
    mock_brave_client.search = raise_error
    
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)

    assert len(results) == 1
    assert results[0]['type'] == 'error'
    assert 'API Error' in results[0]['error']

@pytest.mark.asyncio
async def test_query_analysis_integration(aggregator):
    """Test that query analysis insights are included in response."""
    results = []
    async for result in aggregator.process_query("complex technical query"):
        results.append(result)

    content_results = [r for r in results if r['type'] == 'content']
    assert len(content_results) > 0
    content = content_results[0]['content']
    assert 'Query analysis' in content
    assert 'Test query analysis insights' in content

@pytest.mark.asyncio
async def test_knowledge_synthesis_integration(aggregator):
    """Test that knowledge synthesis is included when available."""
    results = []
    async for result in aggregator.process_query("synthesis test query"):
        results.append(result)

    content_results = [r for r in results if r['type'] == 'content']
    assert len(content_results) > 0
    content = content_results[-1]['content']
    assert 'Knowledge synthesis' in content
    assert 'Test knowledge synthesis' in content

@pytest.mark.asyncio
async def test_streaming_response_format(aggregator):
    """Test that streaming response follows expected format."""
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)

    # Verify all results follow expected format
    for result in results:
        assert 'type' in result
        assert result['type'] in ['content', 'error']
        if result['type'] == 'content':
            assert isinstance(result['content'], str)
        elif result['type'] == 'error':
            assert isinstance(result['error'], str)

@pytest.mark.asyncio
async def test_streaming_response_timing(aggregator):
    """Test response timing characteristics of streaming."""
    start_time = time.time()
    first_chunk_time = None
    last_chunk_time = None
    chunk_count = 0
    
    async for result in aggregator.process_query("test query"):
        if chunk_count == 0:
            first_chunk_time = time.time() - start_time
        last_chunk_time = time.time() - start_time
        chunk_count += 1
    
    # Verify timing characteristics
    assert first_chunk_time is not None and first_chunk_time < 1.0, "First chunk should arrive within 1 second"
    assert last_chunk_time is not None and last_chunk_time < 5.0, "Full response should complete within 5 seconds"
    assert chunk_count >= 3, "Should receive at least 3 chunks"

@pytest.mark.asyncio
async def test_streaming_chunk_size(aggregator):
    """Test chunk size characteristics of streaming response."""
    chunks = []
    total_size = 0
    
    async for result in aggregator.process_query("test query"):
        if result['type'] == 'content':
            chunk_size = len(result['content'].encode('utf-8'))
            chunks.append(chunk_size)
            total_size += chunk_size
    
    # Verify chunk sizes
    assert all(size < 16384 for size in chunks), "All chunks should be under 16KB"
    assert total_size > 0, "Should receive non-empty content"

@pytest.mark.asyncio
async def test_streaming_error_handling(aggregator, mock_brave_client):
    """Test error handling during streaming."""
    # Simulate API error after partial results
    class ErrorAfterOneResult:
        def __init__(self):
            self.items = [{
                'title': 'Test Result 1',
                'url': 'https://example.com/1',
                'description': 'Description 1'
            }]
            self.yielded = False

        def __call__(self, *args, **kwargs):
            return self

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self.yielded:
                self.yielded = True
                return self.items[0]
            raise Exception("Simulated API Error")

    mock_brave_client.search = ErrorAfterOneResult()
    
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)
    
    # Verify error handling
    assert any(r['type'] == 'error' for r in results), "Should receive error message"
    assert any(r['type'] == 'content' for r in results), "Should receive partial content before error"

@pytest.mark.asyncio
async def test_streaming_concurrent_load(aggregator):
    """Test streaming performance under concurrent load."""
    async def process_query():
        results = []
        async for result in aggregator.process_query("test query"):
            results.append(result)
        return results
    
    # Run multiple queries concurrently
    concurrent_queries = 5
    start_time = time.time()
    tasks = [process_query() for _ in range(concurrent_queries)]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    # Verify concurrent performance
    assert total_time < 10.0, f"Concurrent queries should complete within 10 seconds"
    assert all(len(r) >= 3 for r in results), "All queries should receive complete responses"
    assert all(any(item['type'] == 'content' for item in r) for r in results), "All queries should receive content"