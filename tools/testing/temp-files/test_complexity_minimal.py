#!/usr/bin/env python3
"""
Minimal test runner for complexity analyzer without external dependencies.
"""
import sys
import os
sys.path.insert(0, 'src')

# Import only the specific module we need
from brave_search_aggregator.analyzer.complexity_analyzer import (
    ComplexityAnalyzer,
    ComplexityLevel
)

def run_basic_test():
    """Run basic functionality test."""
    print("Running basic complexity analyzer test...")
    
    analyzer = ComplexityAnalyzer()
    
    # Test simple query
    simple_query = "What is Python?"
    result = analyzer.analyze_complexity(simple_query)
    
    print(f"Simple query: '{simple_query}'")
    print(f"Level: {result.level}")
    print(f"Score: {result.score:.3f}")
    print(f"Factors: {result.factors}")
    print()
    
    # Test complex query
    complex_query = """
    When implementing a distributed system using microservices architecture,
    how should we handle transaction management and data consistency across
    services, considering CAP theorem constraints? Specifically, if we have
    services for user authentication, order processing, and inventory management,
    how can we maintain ACID properties while ensuring system scalability?
    """
    
    result2 = analyzer.analyze_complexity(complex_query)
    
    print(f"Complex query preview: '{complex_query.strip()[:50]}...'")
    print(f"Level: {result2.level}")
    print(f"Score: {result2.score:.3f}")
    print(f"Factors: {result2.factors}")
    print()
    
    # Basic assertions
    assert result.level == ComplexityLevel.SIMPLE, f"Expected SIMPLE, got {result.level}"
    assert result.score < 0.3, f"Expected score < 0.3, got {result.score}"
    
    assert result2.level in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX], f"Expected high complexity, got {result2.level}"
    assert result2.score >= 0.5, f"Expected score >= 0.5, got {result2.score}"
    
    print("✓ Basic tests passed!")
    return True

if __name__ == "__main__":
    try:
        run_basic_test()
        print("SUCCESS: Complexity analyzer is working!")
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)