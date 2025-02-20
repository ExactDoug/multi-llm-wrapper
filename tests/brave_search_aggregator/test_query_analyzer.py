"""
Tests for the QueryAnalyzer component.
"""
import pytest
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer
from brave_search_aggregator.analyzer.input_detector import InputType
from brave_search_aggregator.analyzer.complexity_analyzer import ComplexityLevel

@pytest.fixture
def analyzer():
    """Create a QueryAnalyzer instance for testing."""
    return QueryAnalyzer()

@pytest.mark.asyncio
async def test_simple_query():
    """Test analysis of simple queries."""
    analyzer = QueryAnalyzer()
    
    query = "What is Python programming?"
    
    result = await analyzer.analyze_query(query)
    assert result.is_suitable_for_search
    assert result.complexity == "simple"
    assert result.input_type.primary_type == InputType.NATURAL_LANGUAGE
    assert result.complexity_analysis.level == ComplexityLevel.SIMPLE
    assert result.ambiguity_analysis.is_ambiguous  # "python" is ambiguous
    assert len(result.sub_queries) == 1  # One question
    assert "What is Python programming?" in result.sub_queries

@pytest.mark.asyncio
async def test_complex_query():
    """Test analysis of complex queries."""
    analyzer = QueryAnalyzer()
    
    query = """
    How does inheritance in object-oriented programming compare to composition
    when designing class hierarchies, particularly in terms of code reusability
    and maintaining loose coupling between components? Consider both single
    and multiple inheritance scenarios.
    """
    
    result = await analyzer.analyze_query(query)
    assert result.is_suitable_for_search
    assert result.complexity in ["complex", "very complex"]
    assert result.input_type.primary_type == InputType.NATURAL_LANGUAGE
    assert result.complexity_analysis.level in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]
    assert len(result.complexity_analysis.factors) > 2

@pytest.mark.asyncio
async def test_code_query():
    """Test analysis of code-containing queries."""
    analyzer = QueryAnalyzer()
    
    query = """
    Why doesn't this code work?
    
    ```python
    def calculate_sum(a, b):
        return a + b
    
    result = calculate_sum('1', 2)
    ```
    
    I get a TypeError.
    """
    
    result = await analyzer.analyze_query(query)
    assert not result.is_suitable_for_search  # Code queries aren't suitable
    assert result.input_type.primary_type == InputType.CODE
    assert result.segmentation.has_mixed_types
    assert any(segment.type == InputType.CODE for segment in result.input_type.detected_types)

@pytest.mark.asyncio
async def test_error_log_query():
    """Test analysis of error log queries."""
    analyzer = QueryAnalyzer()
    
    query = """
    2025-02-19 11:23:45 ERROR: Failed to connect to database
        at DatabaseConnection.connect():123
        at Main.main():45
    
    How do I fix this error?
    """
    
    result = await analyzer.analyze_query(query)
    assert not result.is_suitable_for_search  # Error logs aren't suitable
    assert result.input_type.primary_type == InputType.LOG
    assert result.segmentation.has_mixed_types
    assert len(result.sub_queries) == 1  # One question at the end

@pytest.mark.asyncio
async def test_ambiguous_query():
    """Test analysis of ambiguous queries."""
    analyzer = QueryAnalyzer()
    
    query = "What's the difference between Python and Java?"
    
    result = await analyzer.analyze_query(query)
    assert result.is_suitable_for_search
    assert result.is_ambiguous
    assert len(result.possible_interpretations) >= 4  # Both terms are ambiguous
    assert result.ambiguity_analysis.ambiguity_score > 0.5

@pytest.mark.asyncio
async def test_arithmetic_query():
    """Test analysis of arithmetic queries."""
    analyzer = QueryAnalyzer()
    
    query = "What is 2 + 2?"
    
    result = await analyzer.analyze_query(query)
    assert not result.is_suitable_for_search
    assert result.complexity == "basic"
    assert result.reason_unsuitable == "basic arithmetic query"

@pytest.mark.asyncio
async def test_empty_query():
    """Test analysis of empty queries."""
    analyzer = QueryAnalyzer()
    
    for query in ["", "   ", "\n\n"]:
        with pytest.raises(ValueError, match="Empty query"):
            await analyzer.analyze_query(query)

@pytest.mark.asyncio
async def test_long_query():
    """Test analysis of queries that exceed length limit."""
    analyzer = QueryAnalyzer()
    
    query = "x" * (analyzer.MAX_QUERY_LENGTH + 1)
    
    with pytest.raises(ValueError, match="Query too long"):
        await analyzer.analyze_query(query)

@pytest.mark.asyncio
async def test_mixed_content_query():
    """Test analysis of queries with mixed content types."""
    analyzer = QueryAnalyzer()
    
    query = """
    I have a question about error handling in Python.
    
    Here's my code:
    ```python
    try:
        result = process_data()
    except Exception as e:
        print(f"Error: {e}")
    ```
    
    And here's the error I get:
    2025-02-19 11:23:45 ERROR: Invalid data format
        at process_data():89
    
    What am I doing wrong?
    """
    
    result = await analyzer.analyze_query(query)
    assert not result.is_suitable_for_search  # Contains code and error log
    assert result.segmentation.has_mixed_types
    assert result.input_type.confidence < 0.8  # Mixed content types
    assert len(result.segmentation.segments) >= 4  # Natural language, code, error log, question

@pytest.mark.asyncio
async def test_performance_metrics():
    """Test that performance metrics are properly tracked."""
    analyzer = QueryAnalyzer()
    
    query = "What is Python programming?"
    
    result = await analyzer.analyze_query(query)
    assert 'processing_time_ms' in result.performance_metrics
    assert 'memory_usage_mb' in result.performance_metrics
    assert 'input_type_confidence' in result.performance_metrics
    assert 'ambiguity_score' in result.performance_metrics
    assert 'complexity_score' in result.performance_metrics
    
    # Check performance requirements
    assert result.performance_metrics['processing_time_ms'] < 100  # < 100ms
    assert result.performance_metrics['memory_usage_mb'] < 10  # < 10MB