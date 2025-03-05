"""Test script to verify the async iterator pattern implementation."""
import asyncio
import logging
import aiohttp
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.utils.config import Config

async def test_async_iterator():
    """Test the async iterator pattern with BraveSearchClient."""
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Create a session
    async with aiohttp.ClientSession() as session:
        # Create a config
        config = Config(
            brave_api_key="test_key",
            max_results_per_query=5,
            timeout_seconds=5,
            rate_limit=5
        )
        
        # Create the client
        client = BraveSearchClient(session, config)
        
        # Print attributes to help with debugging
        logger.info(f"BraveSearchClient attributes: {dir(client)}")
        
        # Check the api_key attribute
        logger.info(f"BraveSearchClient.api_key: {client.api_key}")
        
        try:
            # Get a search iterator
            search_iterator = client.search("test query")
            
            # Check the type of search_iterator
            logger.info(f"Type of search_iterator: {type(search_iterator)}")
            
            # Check if search_iterator has __aiter__
            logger.info(f"Has __aiter__: {hasattr(search_iterator, '__aiter__')}")
            
            # Check if search_iterator has __anext__
            logger.info(f"Has __anext__: {hasattr(search_iterator, '__anext__')}")
            
            # Try to iterate through the search_iterator (will fail without a valid API key)
            try:
                async for result in search_iterator:
                    logger.info(f"Result: {result}")
            except Exception as e:
                logger.error(f"Error during iteration: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_async_iterator())
