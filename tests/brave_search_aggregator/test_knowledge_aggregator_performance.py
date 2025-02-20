"""Performance tests for BraveKnowledgeAggregator."""
import pytest
import asyncio
import time
import gc
import psutil
import os
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

from brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer, QueryAnalysis
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.synthesizer.knowledge_synthesizer import KnowledgeSynthesizer
from brave_search_aggregator.utils.config import Config, AnalyzerConfig

def get_process_memory() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        brave_api_key="test_key",
        max_results_per_query=10,
        timeout_seconds=30,
        rate_limit=20,
        analyzer=AnalyzerConfig(
            max_memory_mb=10,
            input_type_confidence_threshold=0.8,
            complexity_threshold=0.7,
            ambiguity_threshold=0.6,
            enable_segmentation=True,
            max_segments=5,
            enable_streaming_analysis=True,
            analysis_batch_size=3
        )
    )

@pytest.fixture
def mock_components():
    """Create mock components optimized for performance testing."""
    brave_client = Mock(spec=BraveSearchClient)
    query_analyzer = Mock(spec=QueryAnalyzer)
    knowledge_synthesizer = Mock(spec=KnowledgeSynthesizer)
    
    # Configure mock responses
    async def mock_search(query: str):
        results = [
            {
                "title": f"Result {i}",
                "description": f"Description {i}",
                "url": f"https://example.com/result{i}"
            }
            for i in range(10)
        ]
        for result in results:
            yield result
            
    brave_client.search = mock_search
    query_analyzer.analyze_query = AsyncMock(return_value=QueryAnalysis(
        is_suitable_for_search=True,
        search_string="test query",
        complexity="moderate",
        is_ambiguous=False,
        insights="Test insights",
        performance_metrics={
            "processing_time_ms": 50,
            "memory_usage_mb": 5
        }
    ))
    knowledge_synthesizer.synthesize = AsyncMock(return_value="Test synthesis")
    
    return brave_client, query_analyzer, knowledge_synthesizer

@pytest.mark.asyncio
async def test_first_status_timing(config, mock_components):
    """Test that first status is received within 100ms."""
    brave_client, query_analyzer, knowledge_synthesizer = mock_components
    aggregator = BraveKnowledgeAggregator(
        brave_client=brave_client,
        config=config,
        query_analyzer=query_analyzer,
        knowledge_synthesizer=knowledge_synthesizer
    )
    
    start_time = time.time()
    first_status = None
    
    async for result in aggregator.process_query("test query"):
        if result["type"] == "status" and result["stage"] == "analysis_complete":
            first_status = result
            break
            
    response_time = (time.time() - start_time) * 1000
    
    assert first_status is not None
    assert response_time < 100, f"First status took {response_time}ms (should be <100ms)"

@pytest.mark.asyncio
async def test_memory_usage(config, mock_components):
    """Test that memory usage stays under 10MB per request."""
    brave_client, query_analyzer, knowledge_synthesizer = mock_components
    aggregator = BraveKnowledgeAggregator(
        brave_client=brave_client,
        config=config,
        query_analyzer=query_analyzer,
        knowledge_synthesizer=knowledge_synthesizer
    )
    
    # Force garbage collection before test
    gc.collect()
    start_memory = get_process_memory()
    
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)
        current_memory = get_process_memory()
        memory_used = current_memory - start_memory
        assert memory_used < 10, f"Memory usage {memory_used}MB exceeds 10MB limit"
    
    # Verify cleanup
    gc.collect()
    end_memory = get_process_memory()
    memory_diff = end_memory - start_memory
    assert memory_diff < 1, f"Memory leak detected: {memory_diff}MB not released"

@pytest.mark.asyncio
async def test_error_rate_under_load(config, mock_components):
    """Test error rate stays under 1% under load."""
    brave_client, query_analyzer, knowledge_synthesizer = mock_components
    aggregator = BraveKnowledgeAggregator(
        brave_client=brave_client,
        config=config,
        query_analyzer=query_analyzer,
        knowledge_synthesizer=knowledge_synthesizer
    )
    
    total_requests = 100
    error_count = 0
    
    # Run multiple queries concurrently
    async def process_query(query: str) -> bool:
        try:
            async for result in aggregator.process_query(query):
                if result["type"] == "error":
                    return False
            return True
        except Exception:
            return False
    
    tasks = [process_query(f"test query {i}") for i in range(total_requests)]
    results = await asyncio.gather(*tasks)
    error_count = len([r for r in results if not r])
    
    error_rate = (error_count / total_requests) * 100
    assert error_rate < 1, f"Error rate {error_rate}% exceeds 1% limit"

@pytest.mark.asyncio
async def test_streaming_performance(config, mock_components):
    """Test streaming performance metrics."""
    brave_client, query_analyzer, knowledge_synthesizer = mock_components
    aggregator = BraveKnowledgeAggregator(
        brave_client=brave_client,
        config=config,
        query_analyzer=query_analyzer,
        knowledge_synthesizer=knowledge_synthesizer
    )
    
    result_times = []
    last_time = time.time()
    
    async for result in aggregator.process_query("test query"):
        current_time = time.time()
        if result["type"] == "search_result":
            result_times.append((current_time - last_time) * 1000)
        last_time = current_time
    
    # Analyze streaming performance
    avg_time_between_results = sum(result_times) / len(result_times)
    max_time_between_results = max(result_times)
    
    assert avg_time_between_results < 50, f"Average streaming delay {avg_time_between_results}ms too high"
    assert max_time_between_results < 200, f"Maximum streaming delay {max_time_between_results}ms too high"

@pytest.mark.asyncio
async def test_batch_processing_performance(config, mock_components):
    """Test performance of batch processing."""
    brave_client, query_analyzer, knowledge_synthesizer = mock_components
    aggregator = BraveKnowledgeAggregator(
        brave_client=brave_client,
        config=config,
        query_analyzer=query_analyzer,
        knowledge_synthesizer=knowledge_synthesizer
    )
    
    batch_times = []
    current_batch = []
    last_time = time.time()
    
    async for result in aggregator.process_query("test query"):
        if result["type"] == "search_result":
            current_batch.append(result)
            if len(current_batch) >= config.analyzer.analysis_batch_size:
                current_time = time.time()
                batch_times.append((current_time - last_time) * 1000)
                current_batch = []
                last_time = current_time
    
    # Analyze batch processing performance
    avg_batch_time = sum(batch_times) / len(batch_times)
    max_batch_time = max(batch_times)
    
    assert avg_batch_time < 100, f"Average batch processing time {avg_batch_time}ms too high"
    assert max_batch_time < 300, f"Maximum batch processing time {max_batch_time}ms too high"

@pytest.mark.asyncio
async def test_resource_cleanup(config, mock_components):
    """Test resource cleanup after processing."""
    brave_client, query_analyzer, knowledge_synthesizer = mock_components
    aggregator = BraveKnowledgeAggregator(
        brave_client=brave_client,
        config=config,
        query_analyzer=query_analyzer,
        knowledge_synthesizer=knowledge_synthesizer
    )
    
    # Force garbage collection
    gc.collect()
    start_memory = get_process_memory()
    
    # Process multiple queries
    for _ in range(5):
        async for _ in aggregator.process_query("test query"):
            pass
        
        # Force garbage collection
        gc.collect()
        current_memory = get_process_memory()
        memory_diff = current_memory - start_memory
        
        assert memory_diff < 1, f"Memory not properly cleaned up: {memory_diff}MB retained"