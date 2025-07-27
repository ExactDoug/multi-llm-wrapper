# Parallel Testing Infrastructure

## Overview
This document outlines the infrastructure and procedures for conducting real-world testing of the Brave Search Knowledge Aggregator while maintaining separation from the production service.

## Current Production Environment
- Running via multi_llm_wrapper.web.run
- Port 8000 in use
- Active staff usage
- Must remain uninterrupted
- Launched via PowerShell script

## Testing Infrastructure

### Server Configuration
```python
# test_server_config.py
TEST_SERVER_CONFIG = {
    'host': '0.0.0.0',
    'port': 8001,  # Different from production port 8000
    'reload': True,
    'workers': 1,  # Single worker for testing
    'log_level': 'debug'
}
```

### Environment Separation
1. Port Allocation
   - Production: Port 8000
   - Testing: Port 8001
   - Ensures no interference between services

2. Configuration Isolation
   - Separate .env file for testing
   - Test-specific feature flags
   - Isolated logging configuration
   - Separate monitoring metrics

3. Resource Management
   - Controlled API rate limiting
   - Separate connection pools
   - Independent caching
   - Isolated error tracking

## Testing Components

### 1. Server Launch Script
```powershell
# test-server.ps1
& $env:DEV_ROOT\venvs\multi-llm-wrapper\Scripts\Activate.ps1
$env:TEST_ENV="true"
uvicorn brave_search_aggregator.test_server:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Test Environment Variables
```plaintext
# .env.test
BRAVE_API_KEY=your_test_key
MAX_RESULTS_PER_QUERY=20
TIMEOUT_SECONDS=30
RATE_LIMIT=20
TEST_MODE=true
```

### 3. Feature Flag Configuration
```python
TEST_FEATURE_FLAGS = {
    'FEATURE_ADVANCED_SYNTHESIS': False,
    'FEATURE_PARALLEL_PROCESSING': True,
    'FEATURE_MOE_ROUTING': False,
    'FEATURE_TASK_VECTORS': False,
    'FEATURE_SLERP_MERGING': False
}
```

## Real-World Testing Procedures

### 1. API Integration Testing
- Test actual Brave Search API calls
- Verify rate limiting behavior
- Validate error handling
- Document real response patterns

### 2. Parallel Processing Testing
- Test with real workloads
- Monitor resource usage
- Verify error recovery
- Document performance characteristics

### 3. Grid Integration Testing
- Verify display functionality
- Test user interactions
- Validate error states
- Check responsiveness

## Monitoring and Metrics

### 1. Test-Specific Logging
```python
TEST_LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'test_server.log',
            'level': 'DEBUG'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO'
        }
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'DEBUG'
    }
}
```

### 2. Performance Metrics
- Response times
- Resource usage
- Error rates
- API quota usage
- Parallel processing efficiency

## Test Result Documentation

### 1. Performance Metrics Template
```markdown
## Test Results [Date]

### API Performance
- Average response time: X ms
- Error rate: X%
- Rate limit utilization: X%

### Parallel Processing
- Average processing time: X ms
- Resource usage: X MB
- Concurrent request handling: X req/s

### Grid Integration
- Display render time: X ms
- User interaction latency: X ms
- Error recovery time: X ms
```

### 2. Issue Tracking
- Document discovered issues
- Track performance bottlenecks
- Note feature limitations
- Record error patterns

## Safety Measures

### 1. Production Protection
- Separate port ensures no interference
- Independent configuration prevents conflicts
- Isolated logging avoids confusion
- Separate monitoring prevents metric pollution

### 2. Resource Management
- Controlled API usage
- Memory usage monitoring
- CPU utilization tracking
- Network bandwidth management

### 3. Rollback Procedures
- Feature flag disabling
- Process termination
- Log rotation
- Metric cleanup

## Implementation Checklist

- [ ] Create test server configuration
- [ ] Set up isolated environment
- [ ] Configure test-specific logging
- [ ] Implement monitoring
- [ ] Create launch scripts
- [ ] Document test procedures
- [ ] Set up result templates
- [ ] Configure safety measures

## Next Steps

1. Implementation Phase
   - Create test server setup
   - Configure monitoring
   - Set up logging
   - Prepare launch scripts

2. Testing Phase
   - Execute API tests
   - Run parallel processing tests
   - Perform grid integration tests
   - Document results

3. Documentation Phase
   - Update test results
   - Document limitations
   - Record performance metrics
   - Update implementation guides