"""
Simple script to test the BraveKnowledgeAggregator's async iterator pattern.
This is a standalone test script that creates a BraveKnowledgeAggregator 
and runs a test query against it.
"""
import asyncio
import logging
import aiohttp
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Add src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Import the necessary modules
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator
from brave_search_aggregator.utils.config import Config, AnalyzerConfig

async def test_aggregator():
    """Test the BraveKnowledgeAggregator with a simple query."""
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Log startup
    logger.info("Starting test at %s", datetime.now().isoformat())
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("BRAVE_API_KEY", "")
    if not api_key:
        logger.error("No Brave API key found in environment")
        return
    
    logger.info(f"Using API key: ***{api_key[-4:]} from environment")
    
    # Create a configuration
    config = Config(
        brave_api_key=api_key,
        max_results_per_query=5,
        timeout_seconds=30,
        rate_limit=20,
        enable_streaming=True,
        analyzer=AnalyzerConfig(
            enable_segmentation=True,
            max_segments=5,
            enable_streaming=True
        )
    )
    
    # Create a session
    async with aiohttp.ClientSession() as session:
        # Create the client
        logger.info("Creating BraveSearchClient...")
        brave_client = BraveSearchClient(session, config)
        logger.info("BraveSearchClient created successfully")
        
        try:
            # Create the aggregator
            logger.info("Creating BraveKnowledgeAggregator...")
            aggregator = BraveKnowledgeAggregator(
                brave_client=brave_client,
                config=config
            )
            logger.info("BraveKnowledgeAggregator created successfully")
        except Exception as e:
            logger.error(f"Error creating aggregator: {e}", exc_info=True)
            return
            
        # Get the results generator
        logger.info("Getting results generator...")
        start_time = time.time()
        results_generator = aggregator.process_query("python programming")
        
        logger.info(f"Type of results_generator: {type(results_generator)}")
        
        # Iterate through the results using async for (preferred method)
        logger.info("Starting iteration...")
        result_count = 0
        
        try:
            async for result in results_generator:
                # Process the result
                result_count += 1
                now = time.time()
                elapsed = now - start_time
                logger.info(f"Result {result_count} received after {elapsed:.2f}s: Type={result.get('type', 'unknown')}")
                
                if result.get('type') == "content":
                    content = result.get('content')
                    # Handle SynthesisResult objects
                    if hasattr(content, 'content'):
                        content = content.content
                    elif hasattr(content, 'get'):
                        content = content.get('content', str(content))
                    else:
                        content = str(content)
                    logger.info(f"Content: {content[:100]}...")
                    
                    # Check for additional information
                    if 'result' in result:
                        result_info = result.get('result', {})
                        title = result_info.get('title', 'No title')
                        url = result_info.get('url', 'No URL')
                        logger.info(f"Title: {title}")
                        logger.info(f"URL: {url}")
                        
                elif result.get('type') == "error":
                    logger.error(f"Error in response: {result.get('error', 'Unknown error')}")
            
            end_time = time.time()
            total_time = end_time - start_time
            logger.info(f"Total results processed: {result_count}")
            logger.info(f"Total processing time: {total_time:.2f}s")
            logger.info(f"Average time per result: {total_time/max(1, result_count):.2f}s")
            
        except Exception as e:
            logger.error(f"Error during iteration: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_aggregator())
