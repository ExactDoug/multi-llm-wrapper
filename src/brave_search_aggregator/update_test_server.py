"""
Update test server to use the enhanced components for Phase 2 of the Brave Search Knowledge Aggregator.
This script should be run to modify the test_server.py to use the new components for Phase 2 testing.
"""
import os
import logging
import asyncio
import aiohttp
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Phase 2 components
from brave_search_aggregator.synthesizer.enhanced_brave_knowledge_aggregator import EnhancedBraveKnowledgeAggregator
from brave_search_aggregator.synthesizer.content_analyzer import ContentAnalyzer
from brave_search_aggregator.synthesizer.enhanced_knowledge_synthesizer import EnhancedKnowledgeSynthesizer
from brave_search_aggregator.fetcher.content_fetcher import ContentFetcher
from brave_search_aggregator.utils.config import Config, FetcherConfig
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer

async def update_test_server():
    """
    Update the test server to use enhanced components for Phase 2 testing.
    This function initializes all necessary components and updates the test server endpoints.
    """
    logger.info("Updating test server for Phase 2 of Brave Search Knowledge Aggregator...")
    
    try:
        # Load configurations
        logger.info("Loading configurations...")
        config = Config()
        
        # Configure fetcher
        config.fetcher = FetcherConfig(
            timeout_seconds=30,
            max_content_size_bytes=1024 * 1024,  # 1MB
            max_concurrent_fetches=5,
            max_requests_per_domain=2,
            cache_ttl_seconds=300  # 5 minutes
        )
        
        # Create aiohttp session
        logger.info("Creating aiohttp session...")
        session = aiohttp.ClientSession()
        
        # Initialize Brave Search client
        logger.info("Initializing Brave Search client...")
        brave_api_key = os.getenv("BRAVE_API_KEY", "")
        if not brave_api_key:
            logger.warning("BRAVE_API_KEY not found in environment variables.")
        
        brave_client = BraveSearchClient(
            api_key=brave_api_key,
            session=session,
            base_url="https://api.search.brave.com/res/v1/web/search",
            max_results=config.max_results_per_query,
            timeout=config.timeout_seconds
        )
        
        # Initialize Phase 2 components
        logger.info("Initializing Phase 2 components...")
        query_analyzer = QueryAnalyzer(config)
        content_fetcher = ContentFetcher(session, config)
        content_analyzer = ContentAnalyzer(config)
        knowledge_