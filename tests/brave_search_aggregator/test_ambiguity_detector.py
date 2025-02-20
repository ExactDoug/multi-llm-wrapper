"""
Tests for the ambiguity detection component.
"""
import pytest
from brave_search_aggregator.analyzer.ambiguity_detector import (
    AmbiguityDetector,
    AmbiguityType
)

@pytest.fixture
def detector():
    """Create an AmbiguityDetector instance for testing."""
    return AmbiguityDetector()

def test_linguistic_ambiguity():
    """Test detection of linguistic ambiguity."""
    detector = AmbiguityDetector()
    
    # Test known ambiguous terms
    queries = [
        "How do I handle python installation?",
        "What is the best way to learn java?",
        "Can you explain what a shell is?",
    ]
    
    for query in queries:
        result = detector.analyze_ambiguity(query)
        assert result.is_ambiguous
        assert any(instance.type == AmbiguityType.LINGUISTIC 
                  for instance in result.instances)
        assert result.ambiguity_score > 0.0

def test_structural_ambiguity():
    """Test detection of structural ambiguity."""
    detector = AmbiguityDetector()
    
    queries = [
        "Compare Python, Java, and Ruby with C++ and JavaScript",
        "It crashed when running the process",
        "Should I use MySQL or PostgreSQL and MongoDB or Redis?",
    ]
    
    for query in queries:
        result = detector.analyze_ambiguity(query)
        assert result.is_ambiguous
        assert any(instance.type == AmbiguityType.STRUCTURAL 
                  for instance in result.instances)
        assert result.ambiguity_score > 0.0

def test_technical_ambiguity():
    """Test detection of technical ambiguity."""
    detector = AmbiguityDetector()
    
    queries = [
        "How do I create a new thread?",
        "What is the best way to handle memory management?",
        "Can you explain how the cache works?",
    ]
    
    for query in queries:
        result = detector.analyze_ambiguity(query)
        assert result.is_ambiguous
        assert any(instance.type == AmbiguityType.TECHNICAL 
                  for instance in result.instances)
        assert result.ambiguity_score > 0.0

def test_multiple_ambiguity_types():
    """Test detection of multiple types of ambiguity."""
    detector = AmbiguityDetector()
    
    query = """
    Should I use Python or Java for building a shell application
    that handles multiple threads and memory management?
    """
    
    result = detector.analyze_ambiguity(query)
    assert result.is_ambiguous
    
    # Check for presence of different ambiguity types
    ambiguity_types = {instance.type for instance in result.instances}
    assert len(ambiguity_types) > 1
    
    # Score should be higher for multiple ambiguities
    assert result.ambiguity_score > 0.5

def test_context_extraction():
    """Test extraction of context around ambiguous terms."""
    detector = AmbiguityDetector()
    
    query = "I'm having trouble with Python. The code runs fine but sometimes crashes."
    
    result = detector.analyze_ambiguity(query)
    assert result.is_ambiguous
    
    # Check context for the term "Python"
    python_instances = [i for i in result.instances if i.term.lower() == "python"]
    assert len(python_instances) > 0
    assert "code" in python_instances[0].context.lower()

def test_confidence_levels():
    """Test confidence levels for different types of ambiguity."""
    detector = AmbiguityDetector()
    
    # Technical ambiguity should have high confidence
    technical_query = "How do I manage thread priority?"
    technical_result = detector.analyze_ambiguity(technical_query)
    technical_instances = [i for i in technical_result.instances 
                         if i.type == AmbiguityType.TECHNICAL]
    assert any(i.confidence > 0.8 for i in technical_instances)
    
    # Linguistic ambiguity should have medium-high confidence
    linguistic_query = "What is the best python for beginners?"
    linguistic_result = detector.analyze_ambiguity(linguistic_query)
    linguistic_instances = [i for i in linguistic_result.instances 
                          if i.type == AmbiguityType.LINGUISTIC]
    assert any(i.confidence > 0.7 for i in linguistic_instances)

def test_unambiguous_input():
    """Test handling of unambiguous input."""
    detector = AmbiguityDetector()
    
    queries = [
        "What is the current time?",
        "Show me today's weather forecast.",
        "Calculate 2 plus 2.",
    ]
    
    for query in queries:
        result = detector.analyze_ambiguity(query)
        assert not result.is_ambiguous
        assert len(result.instances) == 0
        assert result.ambiguity_score == 0.0

def test_empty_input():
    """Test handling of empty or whitespace input."""
    detector = AmbiguityDetector()
    
    queries = ["", "   ", "\n\n"]
    
    for query in queries:
        result = detector.analyze_ambiguity(query)
        assert not result.is_ambiguous
        assert len(result.instances) == 0
        assert result.ambiguity_score == 0.0

def test_detailed_analysis():
    """Test generation of detailed analysis."""
    detector = AmbiguityDetector()
    
    query = """
    I need help with python and java development.
    The application needs to handle multiple threads
    and manage memory efficiently. It should also
    provide a shell interface.
    """
    
    result = detector.analyze_ambiguity(query)
    assert result.details is not None
    assert "Ambiguity Analysis:" in result.details
    
    # Check for different types in details
    assert "LINGUISTIC" in result.details
    assert "TECHNICAL" in result.details
    
    # Check for term details
    assert "Term:" in result.details
    assert "Context:" in result.details
    assert "Possible meanings:" in result.details