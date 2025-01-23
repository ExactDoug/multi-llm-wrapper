# Testing Strategy

## Overview
This document outlines the testing strategy for the Brave Search Knowledge Aggregator project, with a focus on ensuring reliability, maintainability, and proper isolation of components.

## Core Testing Principles

### 1. Middleware Testing
- Test middleware components in isolation from actual LLM services
- Use both SDK-level and HTTP-level mocking for complete request interception
- Maintain consistent mock responses that match real API formats
- Test error handling and retry logic thoroughly

### 2. Test Categories

#### Unit Tests
- Test individual components in isolation
- Mock all external dependencies
- Focus on business logic and data transformations
- Use dependency injection for better testability

#### Integration Tests
- Test interaction between components
- Use controlled test environments
- Mock external services but test real internal interactions
- Verify configuration loading and validation

#### End-to-End Tests
- Test complete workflows
- Use real configurations when possible
- Test actual API interactions in controlled environment
- Verify error handling and recovery

### 3. Mocking Strategy

#### HTTP-Level Mocking
- Intercept requests at the HTTP client level
- Match real API response formats
- Test different response scenarios
- Verify request formatting and authentication

#### SDK-Level Mocking
- Mock high-level SDK functions
- Test SDK-specific functionality
- Handle SDK-specific error cases
- Verify configuration parsing

### 4. Configuration Testing
- Test configuration loading from different sources
- Verify environment variable handling
- Test configuration validation
- Ensure proper defaults
- Test configuration copying and immutability

### 5. Error Handling
- Test all error scenarios
- Verify error propagation
- Test retry logic
- Validate error messages and types

## Testing Tools

### Primary Tools
- pytest for test running and assertions
- pytest-asyncio for async testing
- pytest-cov for coverage reporting
- httpx for HTTP client mocking
- unittest.mock for general mocking

### Helper Fixtures
- Configuration factories
- Mock response generators
- HTTP client mockers
- Environment setup/teardown

## Best Practices

### 1. Test Organization
- Group tests by component
- Use clear test names
- Maintain test isolation
- Use appropriate markers

### 2. Mock Response Management
- Keep mock responses in separate files
- Match real API formats
- Include all required fields
- Handle edge cases

### 3. Configuration Management
- Use factory functions for test configs
- Avoid global state
- Reset state between tests
- Mock environment variables

### 4. Async Testing
- Use proper async fixtures
- Handle event loops correctly
- Test streaming responses
- Verify async error handling

## Implementation Guidelines

### 1. Test File Structure
```python
# test_component.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_http_client(monkeypatch):
    """Mock HTTP client for all tests"""
    async def mock_request(*args, **kwargs):
        # Return appropriate mock response
        pass
    monkeypatch.setattr('httpx.AsyncClient.post', AsyncMock(side_effect=mock_request))

@pytest.fixture
def test_config():
    """Create test configuration"""
    return create_test_config()

class TestComponent:
    async def test_success_case(self, mock_http_client, test_config):
        # Test happy path
        pass

    async def test_error_case(self, mock_http_client, test_config):
        # Test error handling
        pass
```

### 2. Mock Response Structure
```python
def create_mock_response(provider: str, content: str):
    """Create provider-specific mock response"""
    if provider == "openai":
        return {
            "choices": [{
                "message": {"content": content}
            }],
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20
            }
        }
    elif provider == "anthropic":
        return {
            "content": [{
                "text": content
            }],
            "model": "claude-3",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20
            }
        }
```

## Coverage Goals
- Minimum 80% line coverage
- 100% coverage of error handling paths
- 100% coverage of configuration parsing
- 90% coverage of utility functions

## Continuous Integration
- Run tests on every PR
- Enforce coverage requirements
- Run integration tests in staging
- Verify configuration validation

## Key Learnings
1. Mocking LLM APIs requires both SDK and HTTP-level interception to ensure complete isolation
2. Provider selection should follow strict priority order to maintain consistent behavior
3. Configuration copying needs special handling for nested objects to prevent shared state
4. Test isolation is critical for middleware testing to prevent cross-test contamination
5. Mock responses should exactly match real API formats to catch integration issues early
