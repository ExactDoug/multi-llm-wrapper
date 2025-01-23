# BraveKnowledgeAggregator Testing Strategy

## Overview
This document outlines the testing strategy for the BraveKnowledgeAggregator, focusing on streaming verification, error handling, and web service integration.

## Test Environment

### Local Development (Port 8001)
- Isolated test environment
- Full test coverage
- Mock API responses
- Feature flag support

### Production (Port 8000)
- Live API integration
- Rate limiting
- Error monitoring
- Performance tracking

## Test Categories

### 1. Unit Tests
- Component isolation
- Mock dependencies
- Error handling
- Edge cases

### 2. Integration Tests
- Component interaction
- API integration
- Error propagation
- Data flow

### 3. Streaming Tests
- Response timing
- Chunk sizes
- Error handling
- Load testing

### 4. Web Integration Tests
- Service integration
- UI interaction
- Error display
- Performance

## Test Implementation

### 1. Streaming Verification Tests
```python
@pytest.mark.asyncio
async def test_streaming_response_timing():
    """Test response timing characteristics."""
    start_time = time.time()
    first_chunk_time = None
    last_chunk_time = None
    chunk_count = 0
    
    async for result in aggregator.process_query("test query"):
        if chunk_count == 0:
            first_chunk_time = time.time() - start_time
        last_chunk_time = time.time() - start_time
        chunk_count += 1
    
    assert first_chunk_time < 1.0  # First chunk within 1 second
    assert last_chunk_time < 5.0   # Complete within 5 seconds
    assert chunk_count >= 3        # At least 3 chunks
```

### 2. Error Handling Tests
```python
@pytest.mark.asyncio
async def test_streaming_error_handling():
    """Test error handling during streaming."""
    mock_client.search.side_effect = Exception("API Error")
    
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)
    
    assert len(results) == 1
    assert results[0]['type'] == 'error'
    assert 'API Error' in results[0]['error']
```

### 3. Load Testing
```python
@pytest.mark.asyncio
async def test_streaming_concurrent_load():
    """Test streaming performance under load."""
    concurrent_queries = 5
    tasks = [process_query() for _ in range(concurrent_queries)]
    results = await asyncio.gather(*tasks)
    
    assert all(len(r) >= 3 for r in results)
    assert all(any(item['type'] == 'content' for item in r) for r in results)
```

### 4. Web Integration Tests
```python
@pytest.mark.asyncio
async def test_web_integration():
    """Test web service integration."""
    response = await client.get("/stream/9?query=test")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
```

## Test Coverage Requirements

### 1. Core Functionality
- Query processing: 100%
- Error handling: 100%
- Response formatting: 100%

### 2. Streaming Behavior
- Response timing: 100%
- Chunk handling: 100%
- Error propagation: 100%

### 3. Web Integration
- Service integration: 90%
- Error handling: 100%
- Response formatting: 100%

### 4. Production Features
- Rate limiting: 80%
- Error monitoring: 80%
- Health checks: 80%

## Test Fixtures

### 1. Mock Client
```python
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
    client.search.return_value.__aiter__.return_value = iter(results)
    return client
```

### 2. Mock Error Generator
```python
class ErrorAfterOneResult:
    def __init__(self):
        self.yielded = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.yielded:
            self.yielded = True
            return {'title': 'Test Result', 'url': 'https://example.com', 'description': 'Description'}
        raise Exception("Simulated API Error")
```

## Test Execution

### 1. Development Environment
```bash
# Run all tests
pytest tests/brave_search_aggregator

# Run specific test file
pytest tests/brave_search_aggregator/test_brave_knowledge_aggregator.py

# Run with coverage
pytest --cov=src/brave_search_aggregator
```

### 2. Production Environment
```bash
# Run integration tests
pytest tests/brave_search_aggregator/test_integration.py

# Run load tests
pytest tests/brave_search_aggregator/test_load.py
```

## Test Monitoring

### 1. Coverage Reports
- Generate HTML reports
- Track coverage trends
- Identify gaps

### 2. Test Results
- Track pass/fail rates
- Monitor execution time
- Log error patterns

### 3. Performance Metrics
- Response timing
- Resource usage
- Error rates

## Continuous Integration

### 1. GitHub Actions
- Run tests on push
- Generate coverage reports
- Check code quality

### 2. Production Deployment
- Run integration tests
- Verify streaming behavior
- Check error handling

## Test Documentation

### 1. Test Cases
- Document purpose
- List requirements
- Include examples

### 2. Coverage Reports
- Track metrics
- Identify gaps
- Plan improvements

### 3. Error Logs
- Document patterns
- Track resolutions
- Update tests
