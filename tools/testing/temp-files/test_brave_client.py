"""Test script to verify the BraveSearchClient's async iterator implementation."""
import asyncio
import logging
import aiohttp
import os
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.utils.config import Config
from dotenv import load_dotenv

async def test_brave_client():
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("BRAVE_API_KEY", "")
    if not api_key:
        logger.error("No Brave API key found in environment")
        return
    
    logger.info(f"Using API key: ***{api_key[-4:]}")
    
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
            logger.info("Getting search iterator...")
            search_iterator = brave_client.search("test query")
            
            logger.info(f"Type of search_iterator: {type(search_iterator)}")
            logger.info(f"Has __aiter__ method: {hasattr(search_iterator, '__aiter__')}")
            logger.info(f"Has __anext__ method: {hasattr(search_iterator, '__anext__')}")
            
            # Iterate through the results (without await)
            logger.info("Starting iteration...")
            result_count = 0
            
            async for result in search_iterator:
                logger.info(f"Result {result_count+1}: Received")
                if "title" in result:
                    logger.info(f"Title: {result['title'][:30]}...")
                result_count += 1
                
            logger.info(f"Total results: {result_count}")
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_brave_client())
