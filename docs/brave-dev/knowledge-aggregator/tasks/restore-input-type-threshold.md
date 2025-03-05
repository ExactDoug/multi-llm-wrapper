# Task: Restore Input Type Confidence Threshold Parameter

## Critical Context Files

### 1. Current Implementation Files
- @/src/brave_search_aggregator/utils/config.py - Current config implementation missing the parameter
- @/src/brave_search_aggregator/analyzer/input_detector.py - Contains hardcoded 0.1 threshold
- @/src/brave_search_aggregator/test_server.py - Currently failing due to missing parameter

### 2. Test Files Requiring Parameter
- @/tests/brave_search_aggregator/test_knowledge_aggregator_performance.py - Uses 0.8 threshold
- @/tests/brave_search_aggregator/test_knowledge_aggregator_integration.py - Uses 0.8 threshold
- @/tests/brave_search_aggregator/test_input_detector.py - Tests input type detection

### 3. Documentation and Planning
- @/docs/brave-dev/knowledge-aggregator/analyzer-config-update.md - Current analysis and plan
- @/docs/brave-dev/knowledge-aggregator/query-analyzer-design.md - Original analyzer design
- @/docs/brave-dev/knowledge-aggregator/configuration.md - Configuration documentation

### 4. Historical Context
- @/docs/brave-dev/recent-history/project-state-technical-2025-02-20.md - Recent technical state
- @/docs/brave-dev/recent-history/project-state-development-2025-02-20.md - Recent development state

### 5. Integration Documentation
- @/docs/brave-dev/knowledge-aggregator/component-interactions.md - Component interaction details
- @/docs/brave-dev/knowledge-aggregator/implementation.md - Implementation details

## Required Steps

1. Configuration Update
   - ✓ Add input_type_confidence_threshold to AnalyzerConfig in config.py
   - ✓ Set default value to 0.8 (matches historical implementation)
   - ✓ Add validation in __post_init__ for 0.0 to 1.0 range
   - ❌ Update configuration documentation

2. Input Detector Integration
   - ✓ Replace hardcoded 0.1 threshold in input_detector.py
   - ✓ Add configurable threshold parameter
   - ❌ Update detector tests to use configurable threshold
   - ❌ Verify type detection behavior

3. Test Suite Updates
   - ❌ Fix test_server.py configuration (CRITICAL - Currently Failing)
   - ❌ Verify performance test thresholds
   - ❌ Confirm integration test behavior
   - ❌ Add new tests for threshold validation

4. Critical Next Steps
   - Fix test_server.py initialization error by properly integrating the parameter
   - Verify InputTypeDetector changes work with the configuration
   - Run test suite to validate changes
   - Update all affected documentation

4. Documentation Updates
   - Update configuration guides
   - Document threshold's purpose and impact
   - Add validation requirements
   - Update component interaction docs

5. Verification Process
   - Run all affected test suites
   - Verify test server operation
   - Check performance metrics
   - Validate type detection accuracy

6. Additional Test Suite Verification
   - Run test_content_enrichment.py to verify no regressions
   - Run test_knowledge_aggregator.py with restored threshold
   - Run test_quality_scoring.py to ensure scoring still works
   - Run test_source_validation.py to verify source validation
   - Document any test modifications needed

## Success Criteria

1. All tests pass with restored parameter:
   ```bash
   pytest tests/brave_search_aggregator/test_knowledge_aggregator_performance.py
   pytest tests/brave_search_aggregator/test_knowledge_aggregator_integration.py
   pytest tests/brave_search_aggregator/test_input_detector.py
   ```

2. Test server starts successfully:
   ```bash
   python -m brave_search_aggregator.test_server
   ```

3. Type detection accuracy matches historical behavior:
   - Strict detection with 0.8 threshold
   - Consistent with early morning (12:10-12:42 AM) test runs
   - No regressions in related functionality

4. Documentation is complete and accurate:
   - Configuration guides updated
   - Validation requirements documented
   - Component interactions described
   - Historical context preserved

5. Additional Test Suite Verification:
   ```bash
   # Run content enrichment tests
   pytest tests/brave_search_aggregator/test_content_enrichment.py
   
   # Run knowledge aggregator tests
   pytest tests/brave_search_aggregator/test_knowledge_aggregator.py
   
   # Run quality scoring tests
   pytest tests/brave_search_aggregator/test_quality_scoring.py
   
   # Run source validation tests
   pytest tests/brave_search_aggregator/test_source_validation.py
   ```

## Important Notes

1. DO NOT modify other threshold values in AnalyzerConfig
2. Maintain backward compatibility with existing tests
3. Preserve historical behavior from early morning implementation
4. Document any deviations from original implementation
5. Update all relevant configuration examples
6. Verify no test modifications were made to work around missing parameter
7. Document any test adjustments needed after restoration

## Current Status

1. Implementation Progress:
   - ✓ Added parameter to AnalyzerConfig
   - ✓ Added validation logic
   - ✓ Updated InputTypeDetector
   - ❌ Test server integration failing
   - ❌ Documentation updates pending
   - ❌ Test verification pending

2. Critical Issues:
   - Test server initialization failing due to parameter integration
   - Documentation not reflecting current changes
   - Tests not yet verified with new implementation
   - Configuration examples need updating

3. Next Actions Required:
   - Fix test server parameter integration
   - Run full test suite verification
   - Update all documentation
   - Verify historical behavior maintained

## Related Issues

- Test server initialization failing (CRITICAL - Blocking Progress)
- Performance tests need verification with 0.8 threshold
- Integration tests need verification with parameter
- Documentation requires comprehensive update
- Test modifications need review and potential adjustment

## Mode Requirements

1. Start in Architect mode to:
   - Review all documentation
   - Verify implementation plan
   - Confirm all file dependencies

2. Switch to Code mode to:
   - Implement configuration changes
   - Update test files
   - Fix test server initialization

3. Return to Architect mode to:
   - Update documentation
   - Verify implementation
   - Document any changes

## Test Suite Dependencies

1. Content Enrichment Tests:
   - May have been modified to work without threshold
   - Verify proper threshold usage
   - Check for hardcoded values
   - Look for test modifications that bypassed validation
   - Ensure tests use proper configuration

2. Knowledge Aggregator Tests:
   - Check for threshold bypass code
   - Verify proper configuration usage
   - Test with restored threshold
   - Validate error handling
   - Confirm streaming behavior

3. Quality Scoring Tests:
   - Verify scoring with threshold
   - Check for workarounds
   - Test proper integration
   - Validate quality metrics
   - Ensure consistent behavior

4. Source Validation Tests:
   - Check validation logic
   - Verify threshold impact
   - Test with restored value
   - Confirm source scoring
   - Validate integration points

## Verification Steps

1. Pre-Restoration Test Run:
   ```bash
   # Run all tests to document current state
   pytest tests/brave_search_aggregator/
   ```

2. Post-Restoration Verification:
   ```bash
   # Run core functionality tests
   pytest tests/brave_search_aggregator/test_input_detector.py
   pytest tests/brave_search_aggregator/test_knowledge_aggregator_performance.py
   pytest tests/brave_search_aggregator/test_knowledge_aggregator_integration.py
   
   # Run potentially affected test suites
   pytest tests/brave_search_aggregator/test_content_enrichment.py
   pytest tests/brave_search_aggregator/test_knowledge_aggregator.py
   pytest tests/brave_search_aggregator/test_quality_scoring.py
   pytest tests/brave_search_aggregator/test_source_validation.py
   ```

3. Document Changes:
   - Record any test modifications required
   - Note any configuration adjustments
   - Document any behavioral changes
   - Update test documentation