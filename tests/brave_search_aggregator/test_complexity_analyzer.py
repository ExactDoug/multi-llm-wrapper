"""
Tests for the complexity analysis component.
"""
import pytest
from brave_search_aggregator.analyzer.complexity_analyzer import (
    ComplexityAnalyzer,
    ComplexityLevel
)

@pytest.fixture
def analyzer():
    """Create a ComplexityAnalyzer instance for testing."""
    return ComplexityAnalyzer()

def test_simple_query():
    """Test analysis of simple queries."""
    analyzer = ComplexityAnalyzer()
    
    simple_queries = [
        "What is Python?",
        "Show me the weather.",
        "Define algorithm.",
    ]
    
    for query in simple_queries:
        result = analyzer.analyze_complexity(query)
        assert result.level == ComplexityLevel.SIMPLE
        assert result.score < 0.3
        assert len(result.factors) <= 1

def test_moderate_query():
    """Test analysis of moderately complex queries."""
    analyzer = ComplexityAnalyzer()
    
    query = """
    What is the difference between TCP and UDP protocols in networking?
    How do they handle packet delivery differently?
    """
    
    result = analyzer.analyze_complexity(query)
    assert result.level == ComplexityLevel.MODERATE
    assert 0.3 <= result.score < 0.5
    assert result.metrics.technical_term_count >= 2
    assert "Multiple sentences" in result.details

def test_complex_query():
    """Test analysis of complex queries."""
    analyzer = ComplexityAnalyzer()
    
    query = """
    How does inheritance in object-oriented programming compare to composition
    when designing class hierarchies, particularly in terms of code reusability
    and maintaining loose coupling between components? Consider both single
    and multiple inheritance scenarios.
    """
    
    result = analyzer.analyze_complexity(query)
    assert result.level == ComplexityLevel.COMPLEX
    assert 0.5 <= result.score < 0.7
    assert result.metrics.technical_term_count >= 4
    assert result.metrics.cross_references >= 1

def test_very_complex_query():
    """Test analysis of very complex queries."""
    analyzer = ComplexityAnalyzer()
    
    query = """
    When implementing a distributed system using microservices architecture,
    how should we handle transaction management and data consistency across
    services, considering CAP theorem constraints? Specifically, if we have
    services for user authentication, order processing, and inventory management,
    how can we maintain ACID properties while ensuring system scalability?
    Compare different approaches like saga pattern versus two-phase commit
    protocol, considering their impact on system latency and fault tolerance.
    """
    
    result = analyzer.analyze_complexity(query)
    assert result.level == ComplexityLevel.VERY_COMPLEX
    assert result.score >= 0.7
    assert result.metrics.technical_term_count >= 6
    assert result.metrics.distinct_topic_count >= 2
    assert result.metrics.cross_references >= 2

def test_technical_terms():
    """Test detection of technical terms."""
    analyzer = ComplexityAnalyzer()
    
    query = "How do I configure the TCP/IP settings on my router's firewall?"
    
    result = analyzer.analyze_complexity(query)
    assert result.metrics.technical_term_count >= 3
    assert result.metrics.distinct_topic_count >= 1

def test_nested_clauses():
    """Test detection of nested clauses."""
    analyzer = ComplexityAnalyzer()
    
    query = """
    If the database connection fails, try to reconnect, and if that fails,
    check if the server is running, and if it is, then check the firewall
    settings, otherwise restart the server.
    """
    
    result = analyzer.analyze_complexity(query)
    assert result.metrics.nested_clause_count >= 3
    assert "Nested clauses" in str(result.factors)

def test_cross_references():
    """Test detection of cross-references."""
    analyzer = ComplexityAnalyzer()
    
    query = """
    How does CPU cache performance compare to RAM in terms of access speed,
    and how does this relationship affect overall system performance versus
    cost considerations?
    """
    
    result = analyzer.analyze_complexity(query)
    assert result.metrics.cross_references >= 2
    assert "Cross-references" in str(result.factors)

def test_context_depth():
    """Test calculation of context depth."""
    analyzer = ComplexityAnalyzer()
    
    query = """
    When running the system under heavy load, if the memory usage exceeds
    the threshold, and assuming the cache is properly configured, how should
    we handle new incoming requests compared to existing connections?
    """
    
    result = analyzer.analyze_complexity(query)
    assert result.metrics.context_depth >= 3
    assert "Deep context" in str(result.factors)

def test_empty_input():
    """Test handling of empty or whitespace input."""
    analyzer = ComplexityAnalyzer()
    
    empty_queries = ["", "   ", "\n\n"]
    
    for query in empty_queries:
        result = analyzer.analyze_complexity(query)
        assert result.level == ComplexityLevel.SIMPLE
        assert result.score == 0.0
        assert len(result.factors) == 0