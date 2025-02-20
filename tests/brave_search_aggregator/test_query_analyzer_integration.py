"""
Integration tests for QueryAnalyzer with test server.
"""
import pytest
import asyncio
import aiohttp
import json
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer
from brave_search_aggregator.utils.config import Config
from brave_search_aggregator.utils.feature_flags import FeatureFlags

@pytest.fixture
async def test_server():
    """Ensure test server is running and configured."""
    # Check test server health
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://localhost:8001/health') as response:
                assert response.status == 200
                health_data = await response.json()
                assert health_data['status'] == 'healthy'
            
            # Verify feature flags
            async with session.get('http://localhost:8001/config') as response:
                assert response.status == 200
                config = await response.json()
                assert config['features']['streaming'] == True
                assert config['features']['memory_tracking'] == True
                assert config['features']['error_injection'] == True
                
        except (aiohttp.ClientError, AssertionError) as e:
            pytest.skip(f"Test server not available: {e}")

@pytest.mark.asyncio
async def test_streaming_analysis(test_server):
    """Test streaming analysis with test server integration."""
    analyzer = QueryAnalyzer()
    
    # Test with streaming query
    query = "What are the key features of streaming architectures?"
    
    async for result in analyzer:
        assert result.is_suitable_for_search
        assert result.performance_metrics['processing_time_ms'] < 100
        assert 'streaming' in result.search_string.lower()
        
        # Verify streaming-specific insights
        assert any('streaming' in insight.lower() 
                  for insight in result.insights.split('\n')
                  if 'streaming' in insight.lower())

@pytest.mark.asyncio
async def test_memory_tracking_integration(test_server):
    """Test memory tracking integration with test server."""
    analyzer = QueryAnalyzer()
    
    # Generate large query to test memory tracking
    large_query = " ".join([f"test word {i}" for i in range(1000)])
    
    result = await analyzer.analyze_query(large_query)
    
    # Verify memory metrics
    assert 'memory_usage_mb' in result.performance_metrics
    assert result.performance_metrics['memory_usage_mb'] < 10
    
    # Verify memory tracking insights
    assert any('memory' in insight.lower() 
              for insight in result.insights.split('\n')
              if 'memory' in insight.lower())

@pytest.mark.asyncio
async def test_error_injection_handling(test_server):
    """Test handling of injected errors from test server."""
    analyzer = QueryAnalyzer()
    
    # Test with error-triggering query
    error_query = "INJECT_ERROR: connection_timeout"
    
    result = await analyzer.analyze_query(error_query)
    
    # Verify error handling
    assert not result.is_suitable_for_search
    assert 'error' in result.performance_metrics
    assert result.reason_unsuitable is not None
    
    # Verify partial results handling
    assert result.insights is not None
    assert 'partial results' in result.insights.lower()

@pytest.mark.asyncio
async def test_concurrent_server_requests(test_server):
    """Test handling of concurrent requests with server rate limiting."""
    analyzer = QueryAnalyzer()
    
    # Create 25 queries (more than rate limit of 20/sec)
    queries = [f"Test query {i}" for i in range(25)]
    
    # Run queries concurrently
    results = await asyncio.gather(
        *(analyzer.analyze_query(query) for query in queries),
        return_exceptions=True
    )
    
    # Verify rate limiting behavior
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    assert success_count >= 20  # At least rate limit succeeded
    
    # Verify timing
    assert all(
        r.performance_metrics['processing_time_ms'] < 100
        for r in results
        if not isinstance(r, Exception)
    )

@pytest.mark.asyncio
async def test_feature_flag_behavior(test_server):
    """Test behavior with different feature flag configurations."""
    analyzer = QueryAnalyzer()
    
    # Test queries with different feature combinations
    test_cases = [
        {
            'flags': {'streaming': True, 'memory_tracking': True},
            'query': "What is streaming architecture?",
            'expected_insights': ['streaming', 'memory']
        },
        {
            'flags': {'error_injection': True},
            'query': "INJECT_ERROR: timeout",
            'expected_error': True
        },
        {
            'flags': {'memory_tracking': False},
            'query': "Large query test",
            'expected_metrics': ['processing_time_ms']  # memory_usage_mb should be absent
        }
    ]
    
    for test_case in test_cases:
        # Configure feature flags
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:8001/config',
                json={'features': test_case['flags']}
            ) as response:
                assert response.status == 200
        
        # Run analysis
        result = await analyzer.analyze_query(test_case['query'])
        
        # Verify behavior
        if test_case.get('expected_error'):
            assert not result.is_suitable_for_search
            assert result.reason_unsuitable is not None
        else:
            if 'expected_insights' in test_case:
                assert all(
                    any(insight in result.insights.lower() 
                        for insight in test_case['expected_insights'])
                )
            if 'expected_metrics' in test_case:
                assert all(
                    metric in result.performance_metrics
                    for metric in test_case['expected_metrics']
                )

@pytest.mark.asyncio
async def test_cleanup_on_server_error(test_server):
    """Test proper cleanup when server encounters errors."""
    analyzer = QueryAnalyzer()
    
    # Force server error
    error_query = "INJECT_ERROR: server_crash"
    
    # Run query and verify cleanup
    try:
        result = await analyzer.analyze_query(error_query)
    except Exception:
        pass
    
    # Verify cleanup occurred
    assert analyzer._buffer_size == 0
    assert len(analyzer._buffer) == 0
    assert not analyzer._cleanup_required
    
    # Verify can still process new queries
    normal_query = "Test query after error"
    result = await analyzer.analyze_query(normal_query)
    assert result.is_suitable_for_search