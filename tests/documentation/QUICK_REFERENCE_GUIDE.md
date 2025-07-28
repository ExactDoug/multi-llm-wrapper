# Quick Reference Guide: Common Test Improvements

**Purpose**: Rapid developer reference for implementing RAG analysis recommendations  
**Format**: Cheat sheet with copy-paste code examples and patterns  
**Based on**: Analysis of 38 test files with proven orchestration approach  

---

## 🚀 Quick Start Checklist

### Before You Start
- [ ] **Locate RAG analysis** for your test: `find tests/documentation/rag-research -name "*your_test*"`
- [ ] **Read current state** assessment in the analysis file
- [ ] **Check priority level** in Cross-Reference Index
- [ ] **Install dependencies**: `pip install pytest-asyncio aioresponses`

### Implementation Order
1. **Async migration** (if needed) → pytest-asyncio patterns
2. **HTTP mocking** (if needed) → aioresponses implementation  
3. **Error handling** → comprehensive error scenarios
4. **Framework modernization** → pytest fixtures and parametrization

---

## 🔧 Common Code Patterns

### Async Testing with pytest-asyncio

#### ❌ Current Pattern (from RAG analysis)
```python
import asyncio

def test_async_operation():
    async def run_test():
        result = await async_operation()
        print(f"Result: {result}")
    
    asyncio.run(run_test())
```

#### ✅ Recommended Pattern
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test async operation with proper assertions."""
    result = await async_operation()
    
    # Proper assertions instead of print statements
    assert result is not None
    assert hasattr(result, 'expected_attribute')
    assert len(result.data) > 0
```

#### 🔄 Quick Migration Template
```python
# Replace this pattern:
# asyncio.run(some_async_function())

# With this pattern:
@pytest.mark.asyncio
async def test_name():
    result = await some_async_function()
    assert result is not None  # Add proper assertion
```

### HTTP Mocking with aioresponses

#### ❌ Current Pattern (from RAG analysis)
```python
@pytest.mark.asyncio
async def test_http_request():
    # Makes real HTTP request - slow and unreliable
    client = HTTPClient()
    response = await client.get("https://api.brave.com/search")
    assert response.status == 200
```

#### ✅ Recommended Pattern
```python
import pytest
from aioresponses import aioresponses

@pytest.mark.asyncio
async def test_http_request():
    """Test HTTP request with proper mocking."""
    with aioresponses() as m:
        # Mock the HTTP response
        m.get(
            "https://api.brave.com/search",
            payload={
                "results": [{"title": "Test", "url": "https://example.com"}]
            },
            status=200
        )
        
        client = HTTPClient()
        response = await client.get("https://api.brave.com/search")
        
        assert response.status == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Test"
```

#### 🔄 Quick Migration Template
```python
# Replace HTTP calls with this wrapper:
with aioresponses() as m:
    m.get("YOUR_URL", payload={"key": "value"}, status=200)
    # Your existing test code here
```

### Error Handling Enhancement

#### ❌ Limited Error Testing (from RAG analysis)
```python
@pytest.mark.asyncio
async def test_basic_functionality():
    result = await operation()
    assert result is not None
```

#### ✅ Comprehensive Error Testing
```python
import pytest
import asyncio
import aiohttp
from aioresponses import aioresponses

@pytest.mark.asyncio
async def test_comprehensive_error_scenarios():
    """Test all error scenarios identified in RAG analysis."""
    
    # Test timeout scenarios
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_operation(), timeout=0.001)
    
    # Test network failure scenarios
    with aioresponses() as m:
        m.get("https://api.example.com", exception=aiohttp.ClientError("Network error"))
        
        with pytest.raises(aiohttp.ClientError):
            await network_operation()
    
    # Test malformed response scenarios
    with aioresponses() as m:
        m.get("https://api.example.com", payload="invalid json", headers={"Content-Type": "application/json"})
        
        with pytest.raises((json.JSONDecodeError, ValueError)):
            await json_parsing_operation()
    
    # Test rate limiting
    with aioresponses() as m:
        m.get("https://api.example.com", status=429, payload={"error": "Rate limited"})
        
        with pytest.raises(RateLimitError):
            await rate_limited_operation()
```

#### 🔄 Quick Error Testing Template
```python
# Add these error scenarios to your tests:

# Timeout testing
with pytest.raises(asyncio.TimeoutError):
    await asyncio.wait_for(your_operation(), timeout=0.001)

# Network error testing  
with aioresponses() as m:
    m.get("YOUR_URL", exception=aiohttp.ClientError())
    with pytest.raises(aiohttp.ClientError):
        await your_http_operation()

# Bad response testing
with aioresponses() as m:
    m.get("YOUR_URL", status=500)
    with pytest.raises(HTTPError):
        await your_http_operation()
```

### pytest Fixtures and Parametrization

#### ❌ Manual Setup/Teardown (from RAG analysis)
```python
def test_multiple_scenarios():
    # Manual setup for each scenario
    config1 = create_config(param1="value1")
    result1 = test_operation(config1)
    assert result1.status == "success"
    
    config2 = create_config(param1="value2")  
    result2 = test_operation(config2)
    assert result2.status == "success"
```

#### ✅ Modern pytest Patterns
```python
import pytest

@pytest.fixture
def base_config():
    """Provide base configuration for tests."""
    return {
        "api_key": "test_key",
        "timeout": 30,
        "retries": 3
    }

@pytest.fixture
async def async_client(base_config):
    """Provide async HTTP client with cleanup."""
    client = AsyncHTTPClient(base_config)
    yield client
    await client.close()

@pytest.mark.parametrize("input_value,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
async def test_parametrized_scenarios(async_client, input_value, expected):
    """Test multiple scenarios with parametrization."""
    result = await async_client.process(input_value)
    assert result == expected
```

#### 🔄 Quick Fixture Template
```python
# Add to conftest.py or test file:
@pytest.fixture
def your_resource():
    resource = create_resource()
    yield resource
    resource.cleanup()

# Use in tests:
def test_with_fixture(your_resource):
    result = your_resource.do_something()
    assert result is not None
```

---

## 📋 Framework-Specific Quick Fixes

### Converting to pytest-asyncio

#### Find and Replace Patterns
```python
# Pattern 1: Replace asyncio.run
# Find: asyncio.run(your_async_function())
# Replace with:
@pytest.mark.asyncio
async def test_name():
    await your_async_function()

# Pattern 2: Replace manual async context
# Find: 
def test_async():
    async def inner():
        # test code
    asyncio.run(inner())

# Replace with:
@pytest.mark.asyncio  
async def test_async():
    # test code (move inner content here)
```

#### Common Imports to Add
```python
import pytest
import pytest_asyncio  # If using pytest-asyncio fixtures

# At top of test file:
pytestmark = pytest.mark.asyncio  # Mark entire file as async
```

### Adding HTTP Mocking

#### Basic aioresponses Setup
```python
# Add to imports:
from aioresponses import aioresponses
import aiohttp

# Basic pattern:
@pytest.mark.asyncio
async def test_with_http_mock():
    with aioresponses() as m:
        m.get("YOUR_URL", payload={"data": "test"})
        # Your test code here
```

#### Common HTTP Mock Patterns
```python
# GET request with JSON response
m.get("https://api.example.com/data", payload={"result": "success"})

# POST request with status code
m.post("https://api.example.com/submit", status=201)

# Error response
m.get("https://api.example.com/fail", status=500, payload={"error": "Server error"})

# Network exception
m.get("https://api.example.com/timeout", exception=aiohttp.ClientError("Connection timeout"))

# Multiple responses (for retries)
m.get("https://api.example.com/retry", [
    aiohttp.web.Response(status=503),  # First call fails
    aiohttp.web.Response(status=200, payload={"data": "success"})  # Second succeeds
])
```

### Performance Testing Patterns

#### Basic Benchmark Setup
```python
import time
import pytest

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_performance_benchmark():
    """Benchmark critical operation performance."""
    start_time = time.perf_counter()
    
    result = await performance_critical_operation()
    
    execution_time = time.perf_counter() - start_time
    
    # Assert performance requirements
    assert execution_time < 1.0, f"Operation took {execution_time:.3f}s, expected < 1.0s"
    assert result is not None
```

#### Memory Usage Testing
```python
import psutil
import os

@pytest.mark.asyncio
async def test_memory_usage():
    """Test memory usage stays within bounds."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    result = await memory_intensive_operation()
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Assert memory usage (example: max 100MB increase)
    assert memory_increase < 100 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB"
    assert result is not None
```

---

## 🛠️ Copy-Paste Code Snippets

### Standard Test Function Template
```python
@pytest.mark.asyncio
async def test_operation_name():
    """
    Test [describe what this tests].
    
    This test addresses RAG analysis recommendations:
    - [list specific recommendations being implemented]
    """
    # Arrange
    with aioresponses() as m:
        m.get("https://api.example.com/data", payload={"status": "success"})
        
    # Act  
    result = await your_operation()
    
    # Assert
    assert result is not None
    assert result.status == "success"
    assert hasattr(result, 'expected_attribute')
```

### Error Testing Snippet
```python
@pytest.mark.asyncio
async def test_error_scenarios():
    """Test error handling as recommended in RAG analysis."""
    
    # Test network timeout
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(your_operation(), timeout=0.001)
    
    # Test HTTP error response
    with aioresponses() as m:
        m.get("https://api.example.com", status=500)
        with pytest.raises(HTTPError):
            await your_http_operation()
    
    # Test malformed data
    with aioresponses() as m:
        m.get("https://api.example.com", payload="not json")
        with pytest.raises((json.JSONDecodeError, ValueError)):
            await your_json_operation()
```

### Fixture Setup Snippet
```python
# Add to conftest.py
@pytest.fixture
async def async_test_client():
    """Provide configured async client for testing."""
    config = TestConfig(
        api_key="test_key",
        base_url="https://api.example.com",
        timeout=30
    )
    client = AsyncClient(config)
    yield client
    await client.close()

@pytest.fixture
def mock_responses():
    """Provide common mock responses."""
    return {
        "success": {"status": "success", "data": "test"},
        "error": {"status": "error", "message": "Test error"},
        "empty": {"status": "success", "data": []}
    }
```

### Parametrized Test Snippet
```python
@pytest.mark.parametrize("input_data,expected_result", [
    ({"query": "test1"}, "result1"),
    ({"query": "test2"}, "result2"), 
    ({"query": "test3"}, "result3"),
])
@pytest.mark.asyncio
async def test_multiple_scenarios(async_test_client, input_data, expected_result):
    """Test multiple input scenarios."""
    with aioresponses() as m:
        m.post("https://api.example.com/process", payload={"result": expected_result})
        
    result = await async_test_client.process(input_data)
    assert result["result"] == expected_result
```

---

## 🔍 RAG Analysis Integration

### Reading Analysis Files
```bash
# Find your test's analysis
find tests/documentation/rag-research -name "*your_test_name*_rag_analysis.md"

# Key sections to focus on:
grep -A 10 "Recommended Improvements" path/to/analysis.md
grep -A 10 "Technical Recommendations" path/to/analysis.md
grep -A 5 "Modern Best Practices" path/to/analysis.md
```

### Validating Implementation
```python
# Use this checklist in your tests:
"""
RAG Analysis Compliance Checklist:
[ ] Async patterns: @pytest.mark.asyncio implemented
[ ] HTTP mocking: aioresponses used for external calls  
[ ] Error handling: Timeout, network, and data errors tested
[ ] Assertions: Proper assert statements replace print()
[ ] Framework: Modern pytest patterns adopted
[ ] Performance: Benchmarks added if recommended
"""
```

### Cross-Reference with Improvements
```bash
# Check if your test is in high-priority list
grep -n "your_test_name" tests/documentation/CROSS_REFERENCE_INDEX.md

# Find related tests that might be affected
grep -B 5 -A 5 "your_test_category" tests/documentation/CROSS_REFERENCE_INDEX.md
```

---

## ⚡ Performance Optimization Quick Wins

### HTTP Mocking Performance
```python
# Before: Real HTTP calls (slow)
response = await client.get("https://api.brave.com/search?q=test")

# After: Mocked HTTP calls (10x faster)
with aioresponses() as m:
    m.get("https://api.brave.com/search", payload={"results": []})
    response = await client.get("https://api.brave.com/search?q=test")
```

### Async Test Performance
```python
# Before: Sequential async operations
results = []
for item in items:
    result = await process_item(item)
    results.append(result)

# After: Parallel async operations  
tasks = [process_item(item) for item in items]
results = await asyncio.gather(*tasks)
```

### Fixture Performance
```python
# Before: Create expensive resources in each test
def test_operation():
    database = create_test_database()  # Expensive
    result = operation(database)
    assert result is not None

# After: Use session-scoped fixtures
@pytest.fixture(scope="session")
def test_database():
    db = create_test_database()
    yield db
    db.cleanup()

def test_operation(test_database):
    result = operation(test_database)
    assert result is not None
```

---

## 📝 Common Migration Commands

### Install Dependencies
```bash
# Install required testing packages
pip install pytest pytest-asyncio aioresponses

# For performance testing
pip install pytest-benchmark pytest-profiling

# For coverage tracking
pip install pytest-cov
```

### Run Specific Test Categories
```bash
# Run only async tests
pytest -m asyncio tests/

# Run only HTTP mocking tests
pytest -k "http or client or fetch" tests/

# Run with coverage
pytest --cov=src tests/

# Run with performance benchmarks
pytest --benchmark-only tests/
```

### File Organization Commands
```bash
# Find tests needing async migration
grep -r "asyncio.run" tests/ --include="*.py"

# Find tests with HTTP calls
grep -r "aiohttp\|requests\|urllib" tests/ --include="*.py"

# Find tests without proper assertions
grep -r "print(" tests/ --include="*.py"
```

---

## 🚨 Common Pitfalls and Solutions

### Async/Await Issues
```python
# ❌ Common mistake: Missing await
result = async_function()  # Returns coroutine, not result

# ✅ Correct usage
result = await async_function()

# ❌ Common mistake: Mixing sync and async
def test_mixed():  # Missing async
    result = await async_function()  # Error: await in non-async function

# ✅ Correct usage
@pytest.mark.asyncio
async def test_async():
    result = await async_function()
```

### HTTP Mocking Issues
```python
# ❌ Common mistake: Wrong URL pattern
with aioresponses() as m:
    m.get("https://api.example.com", payload={"data": "test"})
    # Test calls https://api.example.com/specific/path (won't match)

# ✅ Correct usage: Use URL patterns or exact URLs
with aioresponses() as m:
    m.get(re.compile(r'https://api\.example\.com/.*'), payload={"data": "test"})
    # OR
    m.get("https://api.example.com/specific/path", payload={"data": "test"})
```

### Assertion Problems
```python
# ❌ Common mistake: Weak assertions
assert result  # True for any non-empty value

# ✅ Correct usage: Specific assertions
assert result is not None
assert len(result) > 0
assert result.status == "expected_status"
assert hasattr(result, 'required_attribute')
```

### Fixture Scope Issues
```python
# ❌ Common mistake: Wrong fixture scope
@pytest.fixture  # Default: function scope, recreated each test
def expensive_resource():
    return create_expensive_resource()  # Slow

# ✅ Correct usage: Appropriate scope
@pytest.fixture(scope="module")  # Created once per module
def expensive_resource():
    return create_expensive_resource()
```

---

## 📊 Quick Quality Checklist

### Before Submitting Changes
- [ ] **RAG analysis reviewed**: Read corresponding analysis file
- [ ] **Async patterns**: All async operations use `@pytest.mark.asyncio`
- [ ] **HTTP mocking**: No real external API calls in tests
- [ ] **Error coverage**: Timeout, network, and data errors tested
- [ ] **Proper assertions**: No print statements, specific assert conditions
- [ ] **Performance**: Test execution time reasonable (<2s per test)
- [ ] **Documentation**: Test docstrings explain purpose and RAG compliance

### Code Review Checklist
- [ ] **Framework compliance**: Uses recommended pytest patterns
- [ ] **Mock quality**: Realistic mock data that matches API contracts
- [ ] **Error scenarios**: Comprehensive error condition testing
- [ ] **Resource cleanup**: Proper cleanup of async resources and fixtures
- [ ] **Test isolation**: Tests don't depend on external state
- [ ] **Coverage**: Test covers main functionality and edge cases

---

## 🔗 Quick Links

### Key Files
- **RAG Research Directory**: `tests/documentation/rag-research/`
- **Master Report**: `tests/documentation/RAG_RESEARCH_COMPREHENSIVE_REPORT.md`
- **Cross-Reference**: `tests/documentation/CROSS_REFERENCE_INDEX.md`
- **Implementation Roadmap**: `tests/documentation/TEST_IMPROVEMENT_ROADMAP.md`

### Common Commands
```bash
# Find analysis for test
find tests/documentation/rag-research -name "*test_name*"

# Run improved tests
pytest tests/test_name.py -v

# Check test performance
time pytest tests/test_name.py

# Validate against analysis
./scripts/validate-test-against-analysis.sh tests/test_name.py
```

### Documentation Sections
- **Executive Summary**: Business value and ROI analysis
- **Implementation Roadmap**: Phased approach with timelines
- **Developer Templates**: Step-by-step implementation guides
- **Cross-Reference Index**: Category and theme mappings

---

**This quick reference guide provides immediate, actionable guidance for implementing RAG analysis recommendations. Keep it open while coding for rapid access to proven patterns and solutions.**