import pytest
import asyncio
import time
import psutil
import os
from unittest.mock import AsyncMock, MagicMock

from brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalysis
from brave_search_aggregator.utils.config import Config

def get_process_memory() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

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
    config = Config()
    return BraveKnowledgeAggregator(
        brave_client=mock_brave_client,
        query_analyzer=mock_query_analyzer,
        knowledge_synthesizer=mock_knowledge_synthesizer,
        config=config
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
    
    # Look at all content for test results
    all_content = ' '.join([r.get('content', '') for r in content_results])
    assert 'Test Result 1' in all_content
    assert 'Test Result 2' in all_content

@pytest.mark.asyncio
async def test_process_query_with_error(aggregator, mock_brave_client):
    """Test error handling in query processing."""
    def raise_error(*args, **kwargs):
        raise Exception("API Error")
    mock_brave_client.search = raise_error

    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)

    # Verify error handling
    assert any(r['type'] == 'error' for r in results), "Should receive error message"
    error_result = next(r for r in results if r['type'] == 'error')
    assert 'API Error' in error_result.get('error', '')

@pytest.mark.asyncio
async def test_query_analysis_integration(aggregator):
    """Test that query analysis insights are included in response."""
    query_analyzer = aggregator.query_analyzer
    query_analyzer.analyze_query.return_value.insights = "Test query analysis insights"
    
    results = []
    async for result in aggregator.process_query("complex technical query"):
        results.append(result)

    content_results = [r for r in results if r['type'] == 'content']
    assert len(content_results) > 0
    
    # Check all content for query analysis
    all_content = ' '.join([r.get('content', '') for r in content_results])
    assert 'Query Analysis' in all_content
    assert 'Test query analysis insights' in all_content

@pytest.mark.asyncio
async def test_knowledge_synthesis_integration(aggregator):
    """Test that knowledge synthesis is included when available."""
    results = []
    async for result in aggregator.process_query("synthesis test query"):
        results.append(result)

    content_results = [r for r in results if r['type'] == 'content']
    assert len(content_results) > 0
    
    # Check all content for knowledge synthesis
    all_content = ' '.join([r.get('content', '') for r in content_results])
    assert 'knowledge synthesis' in all_content.lower() or 'Knowledge synthesis' in all_content

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
async def test_streaming_response_timing(aggregator, streaming_test_config):
    """Test response timing characteristics of streaming."""
    start_time = time.time()
    first_chunk_time = None
    last_chunk_time = None
    chunk_count = 0
    time_between_chunks = []
    last_chunk_time_point = start_time
    peak_memory = 0
    streaming_test_config["timing"]["max_total_time_ms"] = 30000  # Add max_total_time_ms key

    # Monitor memory usage
    initial_memory = get_process_memory()

    async for result in aggregator.process_query("test query"):
        current_time = time.time()
        
        # Track memory usage
        current_memory = get_process_memory() - initial_memory
        peak_memory = max(peak_memory, current_memory)
        
        # Track timing metrics
        if chunk_count == 0:
            first_chunk_time = current_time - start_time
        else:
            time_between = current_time - last_chunk_time_point
            time_between_chunks.append(time_between * 1000)  # Convert to ms
            
        last_chunk_time = current_time - start_time
        last_chunk_time_point = current_time
        chunk_count += 1

        # Verify streaming metrics if present
        if result.get("type") == "search_result" and "streaming_metrics" in result:
            metrics = result["streaming_metrics"]
            assert "total_events" in metrics
            assert "average_delay_ms" in metrics
            assert metrics["average_delay_ms"] <= streaming_test_config["timing"]["max_time_between_chunks_ms"]

    # Verify timing characteristics
    assert first_chunk_time is not None and first_chunk_time * 1000 < streaming_test_config["timing"]["max_first_chunk_ms"], \
        f"First chunk took {first_chunk_time * 1000}ms (should be <{streaming_test_config['timing']['max_first_chunk_ms']}ms)"
    
    assert last_chunk_time is not None and last_chunk_time * 1000 < streaming_test_config["timing"]["max_total_time_ms"], \
        f"Full response took {last_chunk_time * 1000}ms (should be <{streaming_test_config['timing']['max_total_time_ms']}ms)"
    
    assert chunk_count >= streaming_test_config["min_chunks"], \
        f"Received {chunk_count} chunks (should be >={streaming_test_config['min_chunks']})"

    # Verify time between chunks
    if time_between_chunks:
        max_gap = max(time_between_chunks)
        assert max_gap <= streaming_test_config["timing"]["max_time_between_chunks_ms"], \
            f"Maximum gap between chunks was {max_gap}ms (should be <={streaming_test_config['timing']['max_time_between_chunks_ms']}ms)"

    # Verify memory usage
    assert peak_memory <= streaming_test_config["memory"]["max_memory_mb"], \
        f"Peak memory usage was {peak_memory}MB (should be <={streaming_test_config['memory']['max_memory_mb']}MB)"

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
async def test_streaming_concurrent_load(aggregator, streaming_test_config):
    """Test streaming performance under concurrent load."""
    async def process_query():
        results = []
        memory_readings = []
        start_memory = get_process_memory()
        
        async for result in aggregator.process_query("test query"):
            results.append(result)
            memory_readings.append(get_process_memory() - start_memory)
            
        return results, max(memory_readings) if memory_readings else 0

    # Run multiple queries concurrently
    concurrent_queries = streaming_test_config["resource_constraints"]["max_requests_per_second"]
    start_time = time.time()
    tasks = [process_query() for _ in range(concurrent_queries)]
    query_results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time

    # Extract results and memory readings
    results = [r[0] for r in query_results]
    peak_memories = [r[1] for r in query_results]

    # Verify concurrent performance
    assert total_time * 1000 < streaming_test_config["timing"]["max_source_selection_ms"], \
        f"Concurrent queries took {total_time * 1000}ms (should be <{streaming_test_config['timing']['max_source_selection_ms']}ms)"
    
    assert all(len(r) >= streaming_test_config["min_chunks"] for r in results), \
        f"All queries should receive at least {streaming_test_config['min_chunks']} chunks"
    
    assert all(any(item['type'] == 'content' for item in r) for r in results), \
        "All queries should receive content"
        
    # Verify memory usage under concurrent load
    max_peak_memory = max(peak_memories)
    assert max_peak_memory <= streaming_test_config["memory"]["max_memory_mb"], \
        f"Peak memory under load was {max_peak_memory}MB (should be <={streaming_test_config['memory']['max_memory_mb']}MB)"

@pytest.mark.asyncio
async def test_error_rate_under_load(aggregator, streaming_test_config):
    """Test that error rate stays under 1% under load."""
    error_count = 0
    total_requests = 100  # Large enough sample size
    
    async def process_query():
        try:
            async for result in aggregator.process_query("test query"):
                if result["type"] == "error":
                    return False
            return True
        except Exception:
            return False
    
    # Run multiple queries
    tasks = [process_query() for _ in range(total_requests)]
    results = await asyncio.gather(*tasks)
    
    # Calculate error rate
    error_count = len([r for r in results if not r])
    error_rate = error_count / total_requests
    
    # Verify error rate requirement
    assert error_rate <= streaming_test_config["error_rate"]["max_error_rate"], \
        f"Error rate {error_rate:.2%} exceeds maximum {streaming_test_config['error_rate']['max_error_rate']:.2%}"

@pytest.mark.asyncio
async def test_browser_integration(aggregator, browser_test_config):
    """Test browser integration with streaming responses."""
    frame_times = []
    last_frame_time = time.time()
    memory_readings = []
    
    async def monitor_browser_performance():
        """Monitor browser performance metrics."""
        nonlocal last_frame_time
        while True:
            current_time = time.time()
            frame_time = (current_time - last_frame_time) * 1000  # Convert to ms
            frame_times.append(frame_time)
            memory_readings.append(get_process_memory())
            last_frame_time = current_time
            await asyncio.sleep(1/60)  # Sample at 60Hz
    
    # Start performance monitoring
    monitor_task = asyncio.create_task(monitor_browser_performance())
    
    try:
        results = []
        async for result in aggregator.process_query("test query"):
            results.append(result)
            
            # Verify streaming metrics for browser
            if result.get("type") == "search_result":
                assert "streaming_metrics" in result, "Missing streaming metrics"
                metrics = result["streaming_metrics"]
                
                # Verify browser-specific metrics
                if "browser_metrics" in metrics:
                    browser_metrics = metrics["browser_metrics"]
                    assert "frame_time" in browser_metrics
                    assert browser_metrics["frame_time"] <= browser_test_config["performance"]["max_frame_time_ms"]
        
        # Calculate performance metrics
        avg_frame_time = sum(frame_times) / len(frame_times) if frame_times else float('inf')
        max_frame_time = max(frame_times) if frame_times else float('inf')
        fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0
        peak_memory = max(memory_readings) if memory_readings else 0
        
        # Verify browser performance requirements
        assert fps >= browser_test_config["performance"]["min_fps"], \
            f"Frame rate {fps:.1f}fps below minimum {browser_test_config['performance']['min_fps']}fps"
        
        assert max_frame_time <= browser_test_config["performance"]["max_frame_time_ms"], \
            f"Max frame time {max_frame_time:.1f}ms exceeds limit {browser_test_config['performance']['max_frame_time_ms']}ms"
        
        assert peak_memory <= browser_test_config["performance"]["max_memory_mb"], \
            f"Peak memory {peak_memory:.1f}MB exceeds limit {browser_test_config['performance']['max_memory_mb']}MB"
        
        # Verify streaming requirements for browser
        assert len(results) >= browser_test_config["streaming"]["min_chunks"], \
            f"Received {len(results)} chunks (minimum {browser_test_config['streaming']['min_chunks']})"
        
        # Verify first chunk timing - skip if no matching records found
        first_result_time = next(
            (r["streaming_metrics"].get("total_time_ms", 0)
             for r in results
             if r.get("type") == "content" 
             and "streaming_metrics" in r 
             and "total_time_ms" in r["streaming_metrics"]),
            0  # default value if no matching records
        )
        
        if first_result_time > 0:  # Only verify if we found a valid time
            assert first_result_time <= browser_test_config["streaming"]["max_first_chunk_ms"], \
                f"First chunk took {first_result_time}ms (limit {browser_test_config['streaming']['max_first_chunk_ms']}ms)"
        
    finally:
        # Clean up monitoring task
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass