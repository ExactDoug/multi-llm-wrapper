"""Check Python path and import mechanisms."""
import sys
import os
import inspect

# Print Python version
print(f"Python version: {sys.version}")

# Print sys.path
print("\nPython import path (sys.path):")
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")

# Check for the brave_search_aggregator package
package_name = "brave_search_aggregator"
print(f"\nLooking for {package_name} package...")

# Search in sys.path
found = False
for path in sys.path:
    package_path = os.path.join(path, package_name)
    if os.path.exists(package_path):
        print(f"Found at: {package_path}")
        
        # Check for the fetcher module
        fetcher_path = os.path.join(package_path, "fetcher")
        if os.path.exists(fetcher_path):
            print(f"  fetcher module found at: {fetcher_path}")
            
            # Check for brave_client.py
            client_path = os.path.join(fetcher_path, "brave_client.py")
            if os.path.exists(client_path):
                print(f"    brave_client.py found at: {client_path}")
                
                # Read the first few lines of the file
                with open(client_path, 'r') as f:
                    first_lines = [next(f) for _ in range(10)]
                print("\nFirst few lines of brave_client.py:")
                for i, line in enumerate(first_lines):
                    print(f"{i+1}: {line.rstrip()}")
                    
                # Look for the SearchResultIterator class
                with open(client_path, 'r') as f:
                    content = f.read()
                    if "class SearchResultIterator" in content:
                        print("\nSearchResultIterator class found in the file!")
                        # Find the class definition line
                        for i, line in enumerate(content.splitlines()):
                            if "class SearchResultIterator" in line:
                                print(f"Line {i+1}: {line}")
                                break
                    else:
                        print("\nSearchResultIterator class NOT found in the file!")
                
                found = True
                break
        
if not found:
    print(f"{package_name} package not found in sys.path")

# Try importing the module and check its file path
try:
    import brave_search_aggregator.fetcher.brave_client as brave_client
    print(f"\nSuccessfully imported brave_client module")
    print(f"Module file path: {inspect.getfile(brave_client)}")
    
    # Check if SearchResultIterator exists in the module
    if hasattr(brave_client, "SearchResultIterator"):
        print("SearchResultIterator class found in the imported module!")
    else:
        print("SearchResultIterator class NOT found in the imported module!")
        
except ImportError as e:
    print(f"\nFailed to import brave_client module: {e}")
