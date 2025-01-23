"""Test server for Brave Search Knowledge Aggregator."""
import logging
import os
from typing import Dict, Any

import aiohttp
import uvicorn
from dotenv import load_dotenv

# Load test environment variables
load_dotenv('.env.test')
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.synthesizer.knowledge_aggregator import KnowledgeAggregator
from brave_search_aggregator.utils.test_config import TestServerConfig, TestFeatureFlags

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Brave Search Knowledge Aggregator Test Server")

# Initialize configuration
config = TestServerConfig.from_env()

# Initialize session
session: aiohttp.ClientSession = None
client: BraveSearchClient = None
aggregator: KnowledgeAggregator = None

class SearchRequest(BaseModel):
    """Search request model."""
    query: str

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global session, client, aggregator
    
    logger.info("Initializing test server components...")
    
    # Create aiohttp session
    session = aiohttp.ClientSession()
    
    # Initialize Brave Search client
    client = BraveSearchClient(session, config)
    logger.info(f"Initialized Brave Search client with API key: {'*' * 8}{config.brave_api_key[-4:]}")
    
    # Initialize knowledge aggregator
    aggregator = KnowledgeAggregator()
    
    logger.info("Test server initialization complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global session
    if session:
        await session.close()
        logger.info("Closed aiohttp session")

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": "test",
        "port": config.port,
        "feature_flags": config.features.get_enabled_features()
    }

@app.get("/config")
async def get_config() -> Dict[str, Any]:
    """Get current configuration."""
    return {
        "max_results_per_query": config.max_results_per_query,
        "timeout_seconds": config.timeout_seconds,
        "rate_limit": config.rate_limit,
        "feature_flags": config.features.get_enabled_features()
    }

@app.post("/search")
async def search(request: SearchRequest) -> Dict[str, Any]:
    """
    Execute a search query.
    
    Args:
        request: SearchRequest containing the query
        
    Returns:
        Search results and synthesized knowledge
    """
    try:
        logger.info(f"Processing search request - Query: {request.query}")
        
        # Execute search
        results = await client.search(request.query)
        logger.info(f"Received {len(results)} results from Brave Search API")
        
        # Process results using parallel processing
        processed_results = await aggregator.process_parallel(
            query=request.query,
            sources=["brave_search"],  # For now, just use Brave Search
            preserve_nuances=True,
            raw_results=results  # Pass raw results to the aggregator
        )
        logger.info("Successfully processed search results")
        
        # Format response
        response = {
            "query": request.query,
            "raw_results": results[:3],  # Limit raw results in response
            "processed_results": {
                "content": processed_results.content,
                "all_sources_processed": processed_results.all_sources_processed,
                "conflicts_resolved": processed_results.conflicts_resolved,
                "nuances_preserved": processed_results.nuances_preserved,
                "source_metrics": processed_results.source_metrics,
                "processing_time": processed_results.processing_time
            }
        }
        
        logger.debug(f"Returning response with {len(results)} raw results and processed content")
        return response
        
    except Exception as e:
        logger.error(f"Error processing search request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Run the test server."""
    uvicorn.run(
        "brave_search_aggregator.test_server:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
        log_level=config.log_level,
        workers=config.workers
    )

if __name__ == "__main__":
    main()