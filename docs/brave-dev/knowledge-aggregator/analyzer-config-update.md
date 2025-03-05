# AnalyzerConfig Update Plan

## Historical Context and Issue

### Original Implementation (Feb 20, 2025, ~12:10-12:42 AM)
- Parameter was a core part of the analyzer's configuration
- Used consistently across multiple test files with 0.8 threshold:
  * test_knowledge_aggregator_performance.py
  * test_knowledge_aggregator_integration.py
  * test_server.py
- Designed for strict type detection and quality control
- Critical for performance benchmarking and integration testing

### Current Issue
- Parameter is missing from AnalyzerConfig class
- Test server and other components expect it to be available
- Currently using hardcoded 0.1 threshold in input_detector.py
- System needs the original 0.8 threshold for proper operation

### Parameter Purpose
- Controls confidence threshold for input type detection
- Higher value (0.8) ensures more accurate type classification
- Used in performance metrics and quality assessment
- Critical for maintaining consistent behavior across components

## Implementation Analysis

### 1. Class Usage Analysis
The AnalyzerConfig class is used throughout the system:

1. In QueryAnalyzer:
   - Configures input type detection
   - Controls complexity analysis
   - Manages segmentation behavior
   - Handles performance settings

2. In BraveKnowledgeAggregator:
   - Uses segmentation for relevance calculation
   - Relies on segmentation for source selection
   - Integrates with streaming configuration
   - Manages performance metrics

3. In test_server.py:
   - Configures test environment
   - Sets up analysis parameters
   - Controls segmentation behavior
   - Manages streaming settings

### 2. Segmentation Analysis
The segmentation functionality is a core feature:

1. QuerySegmenter Component:
   - Segments queries by type (questions, code, logs)
   - Provides detailed segment analysis
   - Supports mixed content types
   - Maintains segment relationships

2. Segmentation Configuration Needs:
   - Enable/disable segmentation (enable_segmentation)
   - Control segment limits (max_segments)
   - Performance optimization
   - Feature toggling

### 3. Class Duplication Issue
Current state of config.py:

1. Duplicate Definitions:
   - AnalyzerConfig appears twice (lines ~533 and ~1084)
   - QualityConfig appears twice (lines ~17 and ~568)
   - EnricherConfig appears twice (lines ~54 and ~605)
   - SourceValidationConfig appears three times

2. Resolution Strategy:
   - Keep first instance of each class
   - Remove duplicate definitions
   - Maintain consistent configuration
   - Add proper validation

## Required Changes

1. Clean Up Class Definitions:
   - Remove duplicate class definitions
   - Keep first instance of each class
   - Update any affected imports
   - Add clear file organization

2. Update AnalyzerConfig:
```python
@dataclass
class AnalyzerConfig:
    """Configuration for query analysis components."""
    # Core analysis thresholds
    min_complexity_score: float = 0.8
    min_confidence_score: float = 0.7
    input_type_confidence_threshold: float = 0.8  # Restore this parameter
    required_depth: str = "comprehensive"
    
    # Query segmentation settings
    enable_segmentation: bool = True    # Enable query segmentation
    max_segments: int = 5              # Maximum number of query segments
    
    def __post_init__(self):
        """Initialize and validate configuration."""
        # Validate score thresholds
        for name, value in [
            ('min_complexity_score', self.min_complexity_score),
            ('min_confidence_score', self.min_confidence_score),
            ('input_type_confidence_threshold', self.input_type_confidence_threshold)
        ]:
            try:
                float_val = float(value)
                if not 0 <= float_val <= 1:
                    raise ValueError(f"{name} must be between 0.0 and 1.0")
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid {name}: {e}")
        
        # Validate segmentation settings
        if not isinstance(self.enable_segmentation, bool):
            raise ValueError("enable_segmentation must be a boolean")
            
        try:
            max_segments = int(self.max_segments)
            if max_segments <= 0:
                raise ValueError(f"max_segments must be positive, got {max_segments}")
            self.max_segments = max_segments
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid max_segments: {e}")
```

3. Update InputTypeDetector Integration
- Replace hardcoded 0.1 threshold in input_detector.py
- Pass configuration from AnalyzerConfig through to detector
- Maintain consistent threshold across all components

3. Configuration Validation
- Add validation in __post_init__ for input_type_confidence_threshold
- Ensure value is between 0.0 and 1.0
- Default to 0.8 to match historical behavior

4. Test Suite Updates
- Verify integration with test_server.py
- Confirm performance benchmarks in test_knowledge_aggregator_performance.py
- Validate integration tests in test_knowledge_aggregator_integration.py

## Impact and Usage

1. Test Server Usage:
   - Used in test_server.py for server configuration
   - Sets threshold to 0.8 for strict type detection

2. Performance Testing:
   - Used in test_knowledge_aggregator_performance.py
   - Critical for performance benchmarking
   - Threshold of 0.8 used for consistency

3. Integration Testing:
   - Used in test_knowledge_aggregator_integration.py
   - Part of end-to-end test configuration
   - Maintains 0.8 threshold across tests

4. Query Analysis:
   - Affects input type confidence reporting
   - Used in performance metrics tracking
   - Impacts query segmentation behavior

5. System Benefits:
   - More configurable input type detection
   - Better control over type detection sensitivity
   - Consistent configuration across components
   - Standardized threshold value (0.8)

## Implementation Notes

1. Configuration Changes:
   - Add input_type_confidence_threshold to AnalyzerConfig
   - Default value should be 0.8 to match test server expectations
   - Add validation in __post_init__ to ensure value is between 0.0 and 1.0

2. InputTypeDetector Changes:
   - Update detect_type method to use configurable threshold
   - Replace hardcoded 0.1 value in type detection logic
   - Pass threshold through QueryAnalyzer to InputTypeDetector

3. Test Updates:
   - Add tests for different threshold values
   - Verify behavior with both strict (0.8) and lenient (0.1) thresholds
   - Add validation tests for configuration

4. Migration Steps:
   - Add parameter to AnalyzerConfig
   - Update test_server configuration
   - Update any other code using AnalyzerConfig
   - Add parameter to configuration documentation

5. Verification:
   - Run test suite to verify changes
   - Test with test_server to confirm error is resolved
   - Verify input type detection still works as expected

## Update History

### Feb 21, 2025 1:54 PM
- Added note about parameter name mismatch in test_server.py
- Test server using 'complexity_threshold' instead of 'min_complexity_score'
- This mismatch causes initialization failure
- Need to update test_server.py to use correct parameter names from AnalyzerConfig