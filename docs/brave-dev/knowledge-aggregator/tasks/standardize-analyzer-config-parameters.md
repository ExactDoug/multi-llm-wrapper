# Task: Standardize AnalyzerConfig Parameter Names

## Context

### Critical Files
1. Configuration Files:
   - @/src/brave_search_aggregator/utils/config.py - Contains AnalyzerConfig class definition
   - @/src/brave_search_aggregator/utils/test_config.py - Test configuration settings
   - @/.env.test - Test environment configuration

2. Implementation Files:
   - @/src/brave_search_aggregator/test_server.py - Using outdated parameter names
   - @/src/brave_search_aggregator/analyzer/input_detector.py - Input type detection implementation
   - @/src/brave_search_aggregator/analyzer/query_analyzer.py - Query analysis implementation

3. Test Files:
   - @/tests/brave_search_aggregator/test_input_detector.py - Input detector tests
   - @/tests/brave_search_aggregator/test_knowledge_aggregator_performance.py - Performance tests
   - @/tests/brave_search_aggregator/test_knowledge_aggregator_integration.py - Integration tests

4. Documentation Files:
   - @/docs/brave-dev/knowledge-aggregator/analyzer-config-update.md - Documents parameter history
   - @/docs/brave-dev/knowledge-aggregator/configuration.md - Configuration guide
   - @/docs/brave-dev/knowledge-aggregator/query-analyzer-design.md - Analyzer design

## Current Issue
Test server initialization fails with:
```
TypeError: AnalyzerConfig.__init__() got an unexpected keyword argument 'complexity_threshold'
```

This occurs because test_server.py uses outdated parameter names that don't match AnalyzerConfig:
- 'complexity_threshold' instead of 'min_complexity_score'
- 'enable_streaming_analysis' instead of 'enable_streaming'
- 'analysis_batch_size' instead of 'batch_size'

## Required Changes

### 1. Parameter Name Standardization
Current vs. Standard Names:
```python
# Old Names (in test_server.py)
analyzer=AnalyzerConfig(
    max_memory_mb=10,
    input_type_confidence_threshold=0.8,
    complexity_threshold=0.7,          # Non-standard
    ambiguity_threshold=0.6,          # Non-standard
    enable_streaming_analysis=True,    # Non-standard
    max_segments=5,
    enable_streaming_analysis=True,    # Non-standard
    analysis_batch_size=3             # Non-standard
)

# Standard Names (from AnalyzerConfig)
analyzer=AnalyzerConfig(
    max_memory_mb=10,
    input_type_confidence_threshold=0.8,
    min_complexity_score=0.7,        # Standard
    min_confidence_score=0.6,        # Standard
    enable_streaming=True,           # Standard
    max_segments=5,
    batch_size=3                     # Standard
)
```

### 2. Implementation Steps
1. Update test_server.py:
   - Replace outdated parameter names
   - Maintain existing values
   - Verify configuration loads
   - Test server starts successfully

2. Verify Test Coverage:
   - Run input detector tests
   - Check performance tests
   - Validate integration tests
   - Ensure no regressions

3. Update Documentation:
   - Configuration guide updated
   - Parameter changes logged
   - Migration notes added
   - Test requirements updated

### 3. Verification Steps
1. Test Server:
   ```bash
   python -m brave_search_aggregator.test_server
   ```
   - Should start without errors
   - Verify configuration loaded
   - Check server responds
   - Monitor performance

2. Test Suite:
   ```bash
   pytest tests/brave_search_aggregator/
   ```
   - All tests should pass
   - No parameter errors
   - Performance maintained
   - Coverage preserved

## Success Criteria

### 1. Functionality
- Test server starts successfully
- All tests pass
- No parameter errors
- Configuration loads correctly

### 2. Performance
- Response time < 100ms
- Memory usage < 10MB
- Error rate < 1%
- No performance regression

### 3. Documentation
- Changes documented
- Migration notes clear
- Parameters explained
- Examples updated

## Dependencies

### 1. System Requirements
- Python 3.11+
- pytest for testing
- Development environment
- Test server access

### 2. Configuration Requirements
- AnalyzerConfig class
- Test environment variables
- Server configuration
- Test configuration

### 3. Documentation Requirements
- Parameter documentation
- Migration guides
- Test requirements
- Performance baselines

## Related Tasks
- @/docs/brave-dev/knowledge-aggregator/tasks/monitor-threshold-performance.md
- @/docs/brave-dev/knowledge-aggregator/tasks/verify-threshold-production.md
- @/docs/brave-dev/knowledge-aggregator/tasks/maintain-threshold-docs.md

## Notes

### 1. Important Considerations
- Do not change parameter values
- Maintain existing behavior
- Preserve test coverage
- Document all changes

### 2. Future Implications
- Parameter names now standardized
- Configuration more maintainable
- Documentation clearer
- Testing more reliable

### 3. Risk Mitigation
- Backup configuration
- Test thoroughly
- Document changes
- Monitor performance

## Implementation Notes

### 1. Code Changes
- Focus on parameter names only
- Keep existing values
- Maintain type safety
- Preserve comments

### 2. Testing Strategy
- Run specific tests first
- Then full test suite
- Monitor performance
- Document results

### 3. Documentation Updates
- Note parameter changes
- Update examples
- Add migration notes
- Document verification

### 4. Rollback Plan
- Keep original code
- Document changes
- Test rollback
- Monitor impact