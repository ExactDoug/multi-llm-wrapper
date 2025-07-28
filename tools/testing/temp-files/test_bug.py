"""Minimal test to reproduce and fix the 'async for' bug."""
import sys
import asyncio
import importlib
import logging
import aiohttp
import os
from dotenv import load_dotenv

# Force reload of the brave_client module
modules_to_remove = [
    "brave_search_aggregator.fetcher.brave_client",
    "brave_search_aggregator.fetcher", 
    "brave_search_aggregator"
]

for module_name in modules_to_remove:
    if module_name in sys.modules:
        print(f"Removing {module_name} from sys.modules")
        del sys.modules[module_name]

importlib.invalidate_caches()

# Now import the modules from scratch
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.utils.config import Config

# Inspect the SearchResultIterator class if it exists
if hasattr(sys.modules["brave_search_aggregator.fetcher.brave_client"], "SearchResultIterator"):
    print("SearchResultIterator class found in the module!")
    SearchResultIterator = sys.modules["brave_search_aggregator.fetcher.brave_client"].SearchResultIterator
    print(f"__aiter__ method: {SearchResultIterator.__aiter__}")
    print(f"__anext__ method: {SearchResultIterator.__anext__}")
else:
    print("SearchResultIterator class NOT found in the module!")

async def test_search():
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("BRAVE_API_KEY", "")
    if not api_key:
        logger.error("No Brave API key found in environment")
        return
    
    # Create a configuration
    config = Config(
        brave_api_key=api_key,
        max_results_per_query=5,
        timeout_seconds=30,
        rate_limit=20
    )
    
    # Create a session
    async with aiohttp.ClientSession() as session:
        # Create the client
        brave_client = BraveSearchClient(session, config)
        
        try:
            # Get the search iterator
            search_iterator = brave_client.search("test query")
            print(f"Type of search_iterator: {type(search_iterator)}")
            print(f"Has __aiter__ method: {hasattr(search_iterator, '__aiter__')}")
            
            # Try the iterator manually
            aiter = search_iterator.__aiter__()
            print(f"aiter type: {type(aiter)}")
            
            # Try async for
            print("Starting async for loop...")
            count = 0
            async for result in search_iterator:
                print(f"Got result {count+1}")
                count += 1
                if count >= 3:
                    break
                
            print(f"Successfully iterated through {count} results")
            
        except Exception as e:
            print(f"Error: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(test_search())
