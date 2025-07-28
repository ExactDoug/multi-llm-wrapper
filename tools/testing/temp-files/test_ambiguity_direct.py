#!/usr/bin/env python3
"""
Direct test execution for ambiguity detector without dependencies.
"""
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import only the specific module we need
try:
    # Import directly without going through the package __init__.py
    ambiguity_module_path = os.path.join(os.path.dirname(__file__), 'src', 'brave_search_aggregator', 'analyzer', 'ambiguity_detector.py')
    
    import importlib.util
    spec = importlib.util.spec_from_file_location("ambiguity_detector", ambiguity_module_path)
    ambiguity_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ambiguity_module)
    
    AmbiguityDetector = ambiguity_module.AmbiguityDetector
    AmbiguityType = ambiguity_module.AmbiguityType
    
    print("✓ Direct module import successful")
    
except Exception as e:
    print(f"✗ Module import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def test_basic_functionality():
    """Test basic functionality of ambiguity detector."""
    print("\n--- Testing Basic Functionality ---")
    
    try:
        detector = AmbiguityDetector()
        print("✓ AmbiguityDetector instantiated successfully")
        
        # Test with a simple ambiguous query
        query = "How do I handle python installation?"
        result = detector.analyze_ambiguity(query)
        
        print(f"Query: {query}")
        print(f"Is ambiguous: {result.is_ambiguous}")
        print(f"Ambiguity score: {result.ambiguity_score}")
        print(f"Number of instances: {len(result.instances)}")
        
        if result.instances:
            for i, instance in enumerate(result.instances):
                print(f"Instance {i+1}:")
                print(f"  Type: {instance.type}")
                print(f"  Term: {instance.term}")
                print(f"  Confidence: {instance.confidence}")
                print(f"  Context: {instance.context}")
                print(f"  Meanings: {instance.possible_meanings}")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases."""
    print("\n--- Testing Edge Cases ---")
    
    try:
        detector = AmbiguityDetector()
        
        # Test empty string
        result = detector.analyze_ambiguity("")
        print(f"Empty string - Ambiguous: {result.is_ambiguous}, Score: {result.ambiguity_score}")
        
        # Test whitespace only
        result = detector.analyze_ambiguity("   ")
        print(f"Whitespace only - Ambiguous: {result.is_ambiguous}, Score: {result.ambiguity_score}")
        
        # Test unambiguous query
        result = detector.analyze_ambiguity("What is the current time?")
        print(f"Unambiguous query - Ambiguous: {result.is_ambiguous}, Score: {result.ambiguity_score}")
        
        return True
        
    except Exception as e:
        print(f"✗ Edge cases test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Direct Ambiguity Detector Test")
    print("==============================")
    
    start_time = time.time()
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Edge Cases", test_edge_cases),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    end_time = time.time()
    
    print("\n" + "="*40)
    print("EXECUTION SUMMARY")
    print("="*40)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    print(f"Execution time: {end_time - start_time:.3f}s")
    
    return 0 if total_passed == len(results) else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)