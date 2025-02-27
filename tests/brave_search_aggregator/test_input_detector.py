"""
Tests for the input type detection component.
"""
import pytest
from brave_search_aggregator.analyzer.input_detector import InputTypeDetector, InputType

@pytest.fixture
def detector():
    """Create an InputTypeDetector instance for testing."""
    return InputTypeDetector()

def test_detect_code():
    """Test detection of code input."""
    detector = InputTypeDetector()
    
    code_samples = [
        """
        <div class="container">
            <h1>Hello World</h1>
        </div>
        """,
        """
        def calculate_sum(a, b):
            return a + b
        """,
        "```python\nx = 5\ny = 10\n```",
        "const myVar = 'test'",
    ]
    
    for sample in code_samples:
        result = detector.detect_type(sample)
        assert result.primary_type == InputType.CODE
        assert result.confidence > 0.6
        assert InputType.CODE in result.detected_types

def test_detect_logs():
    """Test detection of log input."""
    detector = InputTypeDetector()
    
    log_samples = [
        "2025-02-19 11:23:45 ERROR: Failed to connect to database",
        """
        Exception: Division by zero
            at calculate_average (math.py:45)
            at process_data (main.py:123)
        """,
        "2025-02-19T11:23:45 DEBUG: Processing request",
        "[ERROR] Critical system failure in module xyz",
    ]
    
    for sample in log_samples:
        result = detector.detect_type(sample)
        assert result.primary_type == InputType.LOG
        assert result.confidence > 0.6
        assert InputType.LOG in result.detected_types

def test_detect_natural_language():
    """Test detection of natural language input."""
    detector = InputTypeDetector()
    
    nl_samples = [
        "What is the capital of France?",
        "I think we should consider the implications.",
        "The quick brown fox jumps over the lazy dog.",
        "Can you help me understand how this works?",
    ]
    
    for sample in nl_samples:
        result = detector.detect_type(sample)
        assert result.primary_type == InputType.NATURAL_LANGUAGE
        assert result.confidence > 0.6
        assert InputType.NATURAL_LANGUAGE in result.detected_types

def test_detect_mixed_input():
    """Test detection of mixed input types."""
    detector = InputTypeDetector()
    
    mixed_sample = """
    Here's an error I encountered in my code:
    
    2025-02-19 11:23:45 ERROR: Null pointer exception
    
    ```python
    def process_data(data):
        return data.process()
    ```
    
    Can someone help me understand what's wrong?
    """
    
    result = detector.detect_type(mixed_sample)
    assert result.primary_type == InputType.MIXED
    assert len(result.detected_types) > 1
    assert InputType.CODE in result.detected_types
    assert InputType.LOG in result.detected_types
    assert InputType.NATURAL_LANGUAGE in result.detected_types

def test_empty_input():
    """Test handling of empty or whitespace input."""
    detector = InputTypeDetector()
    
    empty_samples = ["", "   ", "\n\n"]
    
    for sample in empty_samples:
        result = detector.detect_type(sample)
        assert result.primary_type == InputType.NATURAL_LANGUAGE
        assert result.confidence == 0.5
        assert len(result.detected_types) == 1

def test_confidence_levels():
    """Test confidence level calculations."""
    detector = InputTypeDetector()
    
    # Strong code signal
    heavy_code = """
    class TestClass:
        def __init__(self):
            self.value = 0
            
        def increment(self):
            self.value += 1
            
    def main():
        test = TestClass()
        test.increment()
    """
    code_result = detector.detect_type(heavy_code)
    assert code_result.confidence > 0.8
    
    # Strong log signal
    heavy_logs = """
    2025-02-19 11:23:45 ERROR: Database connection failed
    2025-02-19 11:23:46 INFO: Retrying connection
    2025-02-19 11:23:47 WARNING: Connection attempt 2 failed
    2025-02-19 11:23:48 ERROR: Max retries exceeded
    """
    log_result = detector.detect_type(heavy_logs)
    assert log_result.confidence > 0.8