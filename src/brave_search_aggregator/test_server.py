"""Test server for Brave Search Knowledge Aggregator."""
import logging
import os
import json
from typing import Dict, Any

import aiohttp
import uvicorn
from dotenv import load_dotenv

# Load test environment variables
load_dotenv('.env.test')
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
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
async def search(request: SearchRequest):
    """
    Execute a search query and stream results.
    
    Args:
        request: SearchRequest containing the query
        
    Returns:
        Streamed search results and synthesized knowledge
    """
    async def generate_stream():
        try:
            logger.info(f"Processing search request - Query: {request.query}")
            
            # Get search iterator
            search_iterator = client.search(request.query)
            collected_results = []
            
            # Stream results as they come in
            async for result in search_iterator:
                collected_results.append(result)
                
                # Stream each result immediately
                stream_response = {
                    "type": "result",
                    "query": request.query,
                    "result": result,
                    "total_so_far": len(collected_results)
                }
                yield f"data: {json.dumps(stream_response)}\n\n"
            
            # Process collected results
            processed_results = await aggregator.process_parallel(
                query=request.query,
                sources=["brave_search"],
                preserve_nuances=True,
                raw_results=collected_results
            )
            
            # Stream final synthesized knowledge
            final_response = {
                "type": "synthesis",
                "query": request.query,
                "processed_results": {
                    "content": processed_results.content,
                    "all_sources_processed": processed_results.all_sources_processed,
                    "conflicts_resolved": processed_results.conflicts_resolved,
                    "nuances_preserved": processed_results.nuances_preserved,
                    "source_metrics": processed_results.source_metrics,
                    "processing_time": processed_results.processing_time
                }
            }
            yield f"data: {json.dumps(final_response)}\n\n"
            
        except Exception as e:
            logger.error(f"Error processing search request: {str(e)}", exc_info=True)
            error_response = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    try:
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )
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