#!/usr/bin/env python
"""
Minimal test runner for ambiguity detector tests without pytest dependency.
"""
import sys
import os
sys.path.insert(0, 'src')

from brave_search_aggregator.analyzer.ambiguity_detector import (
    AmbiguityDetector,
    AmbiguityType
)

def run_test_linguistic_ambiguity():
    """Test detection of linguistic ambiguity."""
    detector = AmbiguityDetector()
    
    queries = [
        "How do I handle python installation?",
        "What is the best way to learn java?",
        "Can you explain what a shell is?",
    ]
    
    for query in queries:
        result = detector.analyze_ambiguity(query)
        assert result.is_ambiguous, f"Failed: {query} should be ambiguous"
        assert any(instance.type == AmbiguityType.LINGUISTIC 
                  for instance in result.instances), f"Failed: {query} should have linguistic ambiguity"
        assert result.ambiguity_score > 0.0, f"Failed: {query} should have score > 0"
    
    return True

def run_basic_test():
    """Run a basic test to validate the implementation."""
    try:
        detector = AmbiguityDetector()
        result = detector.analyze_ambiguity("How do I handle python installation?")
        
        print(f"Test query: 'How do I handle python installation?'")
        print(f"Is ambiguous: {result.is_ambiguous}")
        print(f"Ambiguity score: {result.ambiguity_score}")
        print(f"Number of instances: {len(result.instances)}")
        
        if result.instances:
            for instance in result.instances:
                print(f"- Type: {instance.type}")
                print(f"  Term: {instance.term}")
                print(f"  Confidence: {instance.confidence}")
                print(f"  Meanings: {instance.possible_meanings}")
                print(f"  Context: {instance.context}")
        
        if result.details:
            print(f"Details:\n{result.details}")
        
        return True
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running basic ambiguity detector test...")
    success = run_basic_test()
    if success:
        print("\nBasic test passed!")
        
        # Try the linguistic ambiguity test
        print("\nRunning linguistic ambiguity test...")
        try:
            run_test_linguistic_ambiguity()
            print("Linguistic ambiguity test passed!")
        except Exception as e:
            print(f"Linguistic ambiguity test failed: {e}")
    else:
        print("Basic test failed!")