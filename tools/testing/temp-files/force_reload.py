"""Force reload of the brave_client module."""
import sys
import importlib

# First, print out all currently loaded modules related to our project
print("Currently loaded modules:")
for name in list(sys.modules.keys()):
    if "brave" in name:
        print(f"  {name}")

# Remove the brave_client module from sys.modules
modules_to_remove = [
    "brave_search_aggregator.fetcher.brave_client",
    "brave_search_aggregator.fetcher", 
    "brave_search_aggregator"
]

for module_name in modules_to_remove:
    if module_name in sys.modules:
        print(f"Removing {module_name} from sys.modules")
        del sys.modules[module_name]

# Also check for and remove multi_llm_wrapper.web.brave_search
if "multi_llm_wrapper.web.brave_search" in sys.modules:
    print("Removing multi_llm_wrapper.web.brave_search from sys.modules")
    del sys.modules["multi_llm_wrapper.web.brave_search"]

# Now reload the modules
print("\nReloading modules...")
importlib.invalidate_caches()

try:
    brave_client = importlib.import_module("brave_search_aggregator.fetcher.brave_client")
    print("Successfully reloaded brave_search_aggregator.fetcher.brave_client")
    print(f"BraveSearchClient class: {brave_client.BraveSearchClient}")
    print(f"SearchResultIterator class: {brave_client.SearchResultIterator if hasattr(brave_client, 'SearchResultIterator') else 'Not found!'}")
except Exception as e:
    print(f"Error reloading brave_client: {e}")

print("\nAfter reload, modules:")
for name in list(sys.modules.keys()):
    if "brave" in name:
        print(f"  {name}")

print("\nDone!")
