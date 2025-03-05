"""Test server for Brave Search Knowledge Aggregator."""
import logging
import os
import json
from typing import Dict, Any
from contextlib import asynccontextmanager

import aiohttp
import uvicorn
from dotenv import load_dotenv

# Load test environment variables
load_dotenv('.env.test')
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator
from brave_search_aggregator.utils.test_config import TestServerConfig, TestFeatureFlags
from brave_search_aggregator.utils.config import Config, AnalyzerConfig

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize configuration
test_server_config = TestServerConfig.from_env()

# Initialize aggregator config
aggregator_config = Config(
    brave_api_key=test_server_config.brave_api_key,
    max_results_per_query=test_server_config.max_results_per_query,
    timeout_seconds=test_server_config.timeout_seconds,
    rate_limit=test_server_config.rate_limit,
    analyzer=AnalyzerConfig(
        max_memory_mb=10,
        input_type_confidence_threshold=0.8,
        min_complexity_score=0.7,
        min_confidence_score=0.6,
        enable_segmentation=True,
        max_segments=5,
        enable_streaming=True,
        batch_size=3
    )
)

# Initialize session
session: aiohttp.ClientSession = None
client: BraveSearchClient = None
aggregator: BraveKnowledgeAggregator = None

class SearchRequest(BaseModel):
    """Search request model."""
    query: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    global session, client, aggregator
    
    # Startup
    logger.info("Initializing test server components...")
    
    # Create aiohttp session
    session = aiohttp.ClientSession()
    
    # Initialize Brave Search client
    client = BraveSearchClient(session, test_server_config)
    logger.info(f"Initialized Brave Search client with API key: {'*' * 8}{test_server_config.brave_api_key[-4:]}")
    
    # Initialize knowledge aggregator with the client and config
    aggregator = BraveKnowledgeAggregator(
        brave_client=client,
        config=aggregator_config
    )
    
    logger.info("Test server initialization complete")
    
    yield
    
    # Shutdown
    if session:
        await session.close()
        logger.info("Closed aiohttp session")

# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="Brave Search Knowledge Aggregator Test Server",
    lifespan=lifespan
)

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": "test",
        "port": test_server_config.port,
        "feature_flags": test_server_config.features.get_enabled_features(),
        "analyzer_config": {
            "max_memory_mb": aggregator_config.analyzer.max_memory_mb,
            "batch_size": aggregator_config.analyzer.batch_size,
            "streaming_enabled": aggregator_config.analyzer.enable_streaming
        }
    }

@app.get("/config")
async def get_config() -> Dict[str, Any]:
    """Get current configuration."""
    return {
        "max_results_per_query": test_server_config.max_results_per_query,
        "timeout_seconds": test_server_config.timeout_seconds,
        "rate_limit": test_server_config.rate_limit,
        "feature_flags": test_server_config.features.get_enabled_features(),
        "analyzer": {
            "max_memory_mb": aggregator_config.analyzer.max_memory_mb,
            "input_type_confidence_threshold": aggregator_config.analyzer.input_type_confidence_threshold,
            "min_complexity_score": aggregator_config.analyzer.min_complexity_score,
            "min_confidence_score": aggregator_config.analyzer.min_confidence_score,
            "enable_segmentation": aggregator_config.analyzer.enable_segmentation,
            "max_segments": aggregator_config.analyzer.max_segments,
            "enable_streaming": aggregator_config.analyzer.enable_streaming,
            "batch_size": aggregator_config.analyzer.batch_size
        }
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
            
            # Stream results through the aggregator
            async for result in aggregator.process_query(request.query):
                yield f"data: {json.dumps(result)}\n\n"
            
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
        host=test_server_config.host,
        port=test_server_config.port,
        reload=test_server_config.reload,
        log_level=test_server_config.log_level,
        workers=test_server_config.workers
    )

if __name__ == "__main__":
    main()