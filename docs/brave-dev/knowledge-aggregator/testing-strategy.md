# Testing Strategy

## Overview
This document outlines the testing strategy for the Brave Search Knowledge Aggregator project, with a focus on real-world validation of MVP features while maintaining proper testing of advanced features.

## Current Testing Status

### Successfully Tested
1. Brave Search API Integration
   - Endpoint connectivity verified
   - Rate limiting confirmed working
   - Error handling validated
   - Response processing tested

2. Knowledge Aggregation
   - Parallel processing verified
   - Source attribution working
   - Result formatting validated
   - Feature flags tested

3. Test Infrastructure
   - Separate test server operational
   - Configuration management working
   - Logging system verified
   - Health checks implemented

## Testing Infrastructure

### Production Environment
- Running on port 8000
- Active staff usage
- Must remain uninterrupted
- Production configuration

### Testing Environment
- Separate service on port 8001
- Isolated configuration
- Independent monitoring
- Feature flag controlled
- Test-specific logging

## Testing Components

### 1. BraveSearchClient Testing
```python
async def test_search_functionality():
    """Test basic search functionality"""
    client = BraveSearchClient(session, config)
    results = await client.search("test query")
    assert len(results) > 0
    assert all(r.get('title') and r.get('url') for r in results)

async def test_rate_limiting():
    """Test rate limiting behavior"""
    client = BraveSearchClient(session, config)
    with pytest.raises(BraveSearchError, match="Rate limit exceeded"):
        for _ in range(config.rate_limit + 1):
            await client.search("test")
```

### 2. Knowledge Aggregator Testing
```python
async def test_parallel_processing():
    """Test parallel processing of results"""
    aggregator = KnowledgeAggregator()
    results = await aggregator.process_parallel(
        query="test",
        sources=["brave_search"],
        raw_results=sample_results
    )
    assert results.all_sources_processed
    assert results.content
```

### 3. Test Server Testing
```python
async def test_search_endpoint():
    """Test search endpoint functionality"""
    response = await client.post(
        "/search",
        json={"query": "test query"}
    )
    assert response.status_code == 200
    assert "raw_results" in response.json()
    assert "processed_results" in response.json()
```

## Testing Priorities

### 1. Real-World Testing
- Test with actual Brave Search API
- Verify parallel processing with real queries
- Test grid integration in production environment
- Monitor actual performance characteristics
- Validate error handling with real scenarios

### 2. Feature Flag Testing
- Test basic functionality with advanced features disabled
- Verify advanced features when enabled
- Test fallback mechanisms
- Validate feature flag configuration
- Monitor feature-specific metrics

### 3. Performance Testing
- Monitor response times
- Track resource usage
- Measure parallel processing efficiency
- Validate rate limiting
- Test error recovery times

## Testing Methodology

### 1. Unit Testing
```python
def test_rate_limiter():
    limiter = RateLimiter(max_rate=20)
    assert limiter.tokens == 20
    assert limiter.max_rate == 20
```

### 2. Integration Testing
```python
async def test_end_to_end():
    """Test complete search and processing flow"""
    query = "latest developments in AI"
    results = await client.search(query)
    processed = await aggregator.process_parallel(
        query=query,
        sources=["brave_search"],
        raw_results=results
    )
    assert processed.content
    assert processed.all_sources_processed
```

### 3. Load Testing
```python
async def test_concurrent_requests():
    """Test handling of concurrent requests"""
    tasks = [
        client.search("test query")
        for _ in range(10)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    assert all(not isinstance(r, Exception) for r in results)
```

## Error Handling Testing

### 1. API Errors
```python
async def test_api_errors():
    """Test handling of API errors"""
    with patch.object(session, 'get') as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 500
        with pytest.raises(BraveSearchError):
            await client.search("test")
```

### 2. Rate Limiting
```python
async def test_rate_limit_recovery():
    """Test rate limit recovery"""
    limiter = RateLimiter(max_rate=2)
    await limiter.acquire()  # First request
    await asyncio.sleep(1)   # Wait for token recovery
    await limiter.acquire()  # Should succeed
```

## Monitoring and Metrics

### 1. Performance Metrics
- Response times
- Processing times
- Resource usage
- Error rates
- API quota usage

### 2. Feature Metrics
- Feature flag usage
- Processing success rates
- Source reliability
- Result quality

## Test Environment Setup

### 1. Configuration
```python
TEST_CONFIG = {
    'max_results_per_query': 20,
    'timeout_seconds': 30,
    'rate_limit': 20,
    'feature_flags': {
        'parallel_processing': True,
        'advanced_synthesis': False
    }
}
```

### 2. Test Data
```python
SAMPLE_RESULTS = [
    {
        'title': 'Test Result 1',
        'url': 'https://example.com/1',
        'description': 'Test description 1'
    },
    {
        'title': 'Test Result 2',
        'url': 'https://example.com/2',
        'description': 'Test description 2'
    }
]
```

## Continuous Integration

### 1. Test Execution
```yaml
test:
  script:
    - python -m pytest tests/
    - python -m pytest tests/integration/ --runintegration
```

### 2. Coverage Requirements
- Minimum 80% line coverage
- 100% coverage of error handling
- 100% coverage of API integration
- 90% coverage of processing logic

## Documentation

### 1. Test Results
- Document all test runs
- Track performance metrics
- Record error patterns
- Note feature behavior

### 2. Test Cases
- Maintain test documentation
- Update test scenarios
- Document edge cases
- Track test coverage

## Next Steps

### 1. Additional Testing
- Implement load testing
- Add performance benchmarks
- Expand integration tests
- Add security testing

### 2. Monitoring
- Set up continuous monitoring
- Implement alerting
- Track usage patterns
- Monitor error rates

### 3. Documentation
- Update test documentation
- Add troubleshooting guides
- Document common issues
- Maintain test scenarios
