"""
Performance tests for the QueryAnalyzer component.
"""
import pytest
import asyncio
import time
import psutil
import os
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer

@pytest.fixture
def analyzer():
    """Create a QueryAnalyzer instance for testing."""
    return QueryAnalyzer()

@pytest.mark.asyncio
async def test_first_status_timing():
    """Test that first status is returned within 100ms."""
    analyzer = QueryAnalyzer()
    
    # Test with various query types
    queries = [
        "What is Python?",
        "How does inheritance work in object-oriented programming?",
        """
        Here's my code:
        ```python
        def example():
            pass
        ```
        Why doesn't it work?
        """,
        "2025-02-19 11:23:45 ERROR: Connection failed\nHow do I fix this?"
    ]
    
    for query in queries:
        start_time = time.time()
        result = await analyzer.analyze_query(query)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms < 100, f"First status took {elapsed_ms}ms (should be <100ms)"
        assert 'processing_time_ms' in result.performance_metrics
        assert result.performance_metrics['processing_time_ms'] < 100

@pytest.mark.asyncio
async def test_memory_usage():
    """Test that memory usage stays under 10MB per request."""
    analyzer = QueryAnalyzer()
    process = psutil.Process(os.getpid())
    
    # Test with a large, complex query
    query = """
    Here's a complex question about system architecture:
    
    When implementing a distributed system using microservices,
    how should we handle transaction management and data consistency
    across services, considering CAP theorem constraints? Specifically,
    if we have services for user authentication, order processing,
    and inventory management, how can we maintain ACID properties
    while ensuring system scalability?
    
    Here's my current implementation:
    ```python
    class TransactionManager:
        def __init__(self):
            self.services = []
            self.state = {}
            
        def register_service(self, service):
            self.services.append(service)
            
        async def begin_transaction(self):
            for service in self.services:
                await service.prepare()
                
        async def commit(self):
            try:
                for service in self.services:
                    await service.commit()
            except Exception as e:
                await self.rollback()
                raise
    ```
    
    And here's the error I'm getting:
    2025-02-19 11:23:45 ERROR: Transaction deadlock detected
        at TransactionManager.commit():123
        at OrderService.process():456
        at InventoryService.update():789
    
    How can I improve this implementation to handle:
    1. Partial failures
    2. Network latency
    3. Service unavailability
    4. Data consistency
    5. Performance optimization
    """
    
    # Get initial memory
    initial_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    
    # Run analysis
    result = await analyzer.analyze_query(query)
    
    # Get final memory
    final_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    
    # Check memory usage
    memory_used = final_memory - initial_memory
    assert memory_used < 10, f"Memory usage was {memory_used}MB (should be <10MB)"
    assert result.performance_metrics['memory_usage_mb'] < 10

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling of concurrent requests within rate limits."""
    analyzer = QueryAnalyzer()
    
    # Create 20 concurrent requests (max rate limit)
    queries = [f"What is test query {i}?" for i in range(20)]
    
    start_time = time.time()
    
    # Run queries concurrently
    results = await asyncio.gather(
        *(analyzer.analyze_query(query) for query in queries)
    )
    
    elapsed_time = time.time() - start_time
    
    # Verify all requests completed successfully
    assert len(results) == 20
    assert all(result.is_suitable_for_search for result in results)
    
    # Check that total time is reasonable (< 1s for all 20 requests)
    assert elapsed_time < 1.0
    
    # Verify memory usage stayed within limits
    assert all(
        result.performance_metrics['memory_usage_mb'] < 10
        for result in results
    )
    
    # Verify timing for each request
    assert all(
        result.performance_metrics['processing_time_ms'] < 100
        for result in results
    )

@pytest.mark.asyncio
async def test_error_rate():
    """Test that error rate stays under 1%."""
    analyzer = QueryAnalyzer()
    
    # Run 1000 queries with various types
    total_queries = 1000
    queries = []
    
    # Generate mix of query types
    for i in range(total_queries):
        if i % 4 == 0:
            queries.append(f"What is test query {i}?")
        elif i % 4 == 1:
            queries.append(f"```python\ndef test_{i}(): pass\n```")
        elif i % 4 == 2:
            queries.append(f"2025-02-19 11:23:{i} ERROR: Test error {i}")
        else:
            queries.append(f"Complex query {i} with multiple\nlines and special $#@ characters")
    
    # Run all queries
    results = await asyncio.gather(
        *(analyzer.analyze_query(query) for query in queries),
        return_exceptions=True
    )
    
    # Count errors (excluding expected unsuitable queries)
    errors = sum(
        1 for result in results
        if isinstance(result, Exception) or (
            hasattr(result, 'reason_unsuitable') and
            result.reason_unsuitable not in [
                "basic arithmetic query",
                "code query",
                "error log query"
            ]
        )
    )
    
    error_rate = errors / total_queries
    assert error_rate < 0.01, f"Error rate was {error_rate:.2%} (should be <1%)"