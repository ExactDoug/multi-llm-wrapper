#!/usr/bin/env python
"""
Test script for Brave Search Knowledge Aggregator.
This script tests the async iterator pattern and error handling.
"""
import asyncio
import os
import logging
from dotenv import load_dotenv
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_brave_search():
    """Test the BraveKnowledgeAggregator."""
    try:
        from brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator
        from brave_search_aggregator.utils.config import Config
        from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
        
        # Load API key from environment
        api_key = os.getenv("BRAVE_API_KEY")
        if not api_key:
            logger.error("No BRAVE_API_KEY found in environment")
            return
            
        logger.info(f"Using API key: {api_key[:4]}****")
        
        # Create configuration
        config = Config(
            brave_api_key=api_key,
            max_results_per_query=20,
            timeout_seconds=30,
            rate_limit=20,
            enable_streaming=True
        )
        
        # Create session and client
        session = aiohttp.ClientSession()
        try:
            brave_client = BraveSearchClient(session, config)
            
            # Create aggregator
            aggregator = BraveKnowledgeAggregator(
                brave_client=brave_client,
                config=config
            )
            
            # Process a test query
            query = "Python async iterator pattern"
            logger.info(f"Processing query: {query}")
            
            # Test with async for
            logger.info("Testing with async for loop...")
            results = []
            async for result in aggregator.process_query(query):
                logger.info(f"Received result type: {result.get('type')}")
                results.append(result)
                
            logger.info(f"Total results: {len(results)}")
            
            # Verify results
            content_results = [r for r in results if r.get('type') == 'content']
            error_results = [r for r in results if r.get('type') == 'error']
            
            logger.info(f"Content results: {len(content_results)}")
            logger.info(f"Error results: {len(error_results)}")
            
            if content_results:
                # Show a sample of content
                sample = content_results[0].get('content', '')[:100]
                logger.info(f"Sample content: {sample}...")
        finally:
            await session.close()
            
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_brave_search())
