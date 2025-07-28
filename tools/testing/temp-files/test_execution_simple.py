#!/usr/bin/env python3
"""
Simple test execution script for ambiguity detector.
Runs tests without requiring pytest installation.
"""
import sys
import os
import time
import traceback

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from brave_search_aggregator.analyzer.ambiguity_detector import (
        AmbiguityDetector,
        AmbiguityType
    )
    print("✓ Module import successful")
except ImportError as e:
    print(f"✗ Module import failed: {e}")
    sys.exit(1)

def run_test_linguistic_ambiguity():
    """Test detection of linguistic ambiguity."""
    print("\n--- Testing Linguistic Ambiguity ---")
    detector = AmbiguityDetector()
    
    queries = [
        "How do I handle python installation?",
        "What is the best way to learn java?",
        "Can you explain what a shell is?",
    ]
    
    results = []
    for query in queries:
        try:
            start_time = time.time()
            result = detector.analyze_ambiguity(query)
            execution_time = time.time() - start_time
            
            passed = (
                result.is_ambiguous and
                any(instance.type == AmbiguityType.LINGUISTIC for instance in result.instances) and
                result.ambiguity_score > 0.0
            )
            
            print(f"Query: {query}")
            print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
            print(f"  Ambiguous: {result.is_ambiguous}")
            print(f"  Score: {result.ambiguity_score:.3f}")
            print(f"  Instances: {len(result.instances)}")
            print(f"  Execution time: {execution_time:.3f}s")
            
            results.append(passed)
            
        except Exception as e:
            print(f"Query: {query}")
            print(f"  Result: ✗ ERROR - {e}")
            print(f"  Traceback: {traceback.format_exc()}")
            results.append(False)
    
    return all(results)

def run_test_structural_ambiguity():
    """Test detection of structural ambiguity."""
    print("\n--- Testing Structural Ambiguity ---")
    detector = AmbiguityDetector()
    
    queries = [
        "Compare Python, Java, and Ruby with C++ and JavaScript",
        "It crashed when running the process",
        "Should I use MySQL or PostgreSQL and MongoDB or Redis?",
    ]
    
    results = []
    for query in queries:
        try:
            start_time = time.time()
            result = detector.analyze_ambiguity(query)
            execution_time = time.time() - start_time
            
            passed = (
                result.is_ambiguous and
                any(instance.type == AmbiguityType.STRUCTURAL for instance in result.instances) and
                result.ambiguity_score > 0.0
            )
            
            print(f"Query: {query}")
            print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
            print(f"  Ambiguous: {result.is_ambiguous}")
            print(f"  Score: {result.ambiguity_score:.3f}")
            print(f"  Instances: {len(result.instances)}")
            print(f"  Execution time: {execution_time:.3f}s")
            
            results.append(passed)
            
        except Exception as e:
            print(f"Query: {query}")
            print(f"  Result: ✗ ERROR - {e}")
            print(f"  Traceback: {traceback.format_exc()}")
            results.append(False)
    
    return all(results)

def run_test_unambiguous_input():
    """Test handling of unambiguous input."""
    print("\n--- Testing Unambiguous Input ---")
    detector = AmbiguityDetector()
    
    queries = [
        "What is the current time?",
        "Show me today's weather forecast.",
        "Calculate 2 plus 2.",
    ]
    
    results = []
    for query in queries:
        try:
            start_time = time.time()
            result = detector.analyze_ambiguity(query)
            execution_time = time.time() - start_time
            
            passed = (
                not result.is_ambiguous and
                len(result.instances) == 0 and
                result.ambiguity_score == 0.0
            )
            
            print(f"Query: {query}")
            print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
            print(f"  Ambiguous: {result.is_ambiguous}")
            print(f"  Score: {result.ambiguity_score:.3f}")
            print(f"  Instances: {len(result.instances)}")
            print(f"  Execution time: {execution_time:.3f}s")
            
            results.append(passed)
            
        except Exception as e:
            print(f"Query: {query}")
            print(f"  Result: ✗ ERROR - {e}")
            print(f"  Traceback: {traceback.format_exc()}")
            results.append(False)
    
    return all(results)

def main():
    """Run all tests and report results."""
    print("Ambiguity Detector Test Execution")
    print("=================================")
    
    overall_start = time.time()
    
    # Run tests
    tests = [
        ("Linguistic Ambiguity", run_test_linguistic_ambiguity),
        ("Structural Ambiguity", run_test_structural_ambiguity),
        ("Unambiguous Input", run_test_unambiguous_input),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ Test suite '{test_name}' failed with exception: {e}")
            results[test_name] = False
    
    overall_time = time.time() - overall_start
    
    # Summary
    print("\n" + "="*50)
    print("TEST EXECUTION SUMMARY")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")
    print(f"Total execution time: {overall_time:.3f}s")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)