"""
Pytest configuration and fixtures.
"""
import os
from typing import AsyncGenerator, Generator
import pytest
import psutil
import aiohttp
from dotenv import load_dotenv

from brave_search_aggregator.utils.config import Config
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer
from brave_search_aggregator.synthesizer.knowledge_synthesizer import KnowledgeSynthesizer

def get_process_memory() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

# Load test environment variables
load_dotenv(".env.test", override=True)

@pytest.fixture
def config() -> Config:
    """Provide test configuration."""
    return Config(
        brave_api_key="test_key",
        max_results_per_query=5,
        timeout_seconds=5,
        rate_limit=10,
        enable_streaming_metrics=True,
        streaming_batch_size=3,
        max_event_delay_ms=50,
        enable_progress_tracking=True
    )

@pytest.fixture
async def aiohttp_client() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Provide aiohttp client session."""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture
async def brave_client(
    config: Config,
    aiohttp_client: aiohttp.ClientSession
) -> AsyncGenerator[BraveSearchClient, None]:
    """Provide configured Brave Search client."""
    client = BraveSearchClient(config, aiohttp_client)
    yield client

@pytest.fixture
def query_analyzer() -> QueryAnalyzer:
    """Provide query analyzer instance."""
    return QueryAnalyzer()

@pytest.fixture
def knowledge_synthesizer() -> KnowledgeSynthesizer:
    """Provide knowledge synthesizer instance."""
    return KnowledgeSynthesizer()

@pytest.fixture
def mock_search_results() -> list:
    """Provide mock search results for testing."""
    return [
        {
            "title": "Test Result 1",
            "url": "https://example.com/1",
            "description": "First test result description"
        },
        {
            "title": "Test Result 2",
            "url": "https://example.com/2",
            "description": "Second test result description"
        }
    ]

@pytest.fixture
def mock_processed_content() -> list:
    """Provide mock processed content for testing."""
    return [
        {
            "url": "https://example.com/1",
            "content": "Processed content from first result",
            "metadata": {"source": "Test Source 1"}
        },
        {
            "url": "https://example.com/2",
            "content": "Processed content from second result",
            "metadata": {"source": "Test Source 2"}
        }
    ]

@pytest.fixture(autouse=True)
def setup_test_env() -> Generator[None, None, None]:
    """Set up test environment variables."""
    original_env = dict(os.environ)
    
    # Set test environment variables
    os.environ.update({
        "TESTING": "true",
        "BRAVE_API_KEY": "test_key",
        "MAX_RESULTS_PER_QUERY": "5",
        "TIMEOUT_SECONDS": "5",
        "RATE_LIMIT": "10"
    })
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def azure_credentials() -> dict:
    """Provide test Azure credentials."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "tenant_id": "test_tenant_id"
    }

@pytest.fixture
def browser_test_config() -> dict:
    """Provide browser test configuration."""
    return {
        "viewport": {
            "width": 1280,
            "height": 800
        },
        "performance": {
            "min_fps": 30,
            "max_frame_time_ms": 33,  # ~30fps
            "max_memory_mb": 10  # Critical requirement: 10MB per request
        },
        "streaming": {
            "max_first_chunk_ms": 100,  # Critical requirement: First Status < 100ms
            "max_first_result_ms": 1000,  # Critical requirement: First Result < 1s
            "max_source_selection_ms": 3000,  # Critical requirement: Source Selection < 3s
            "min_chunks": 3
        }
    }

@pytest.fixture
def streaming_test_config() -> dict:
    """Provide streaming test configuration."""
    return {
        "timing": {
            "max_first_chunk_ms": 100,  # Critical requirement: First Status < 100ms
            "max_first_result_ms": 1000,  # Critical requirement: First Result < 1s
            "max_source_selection_ms": 3000,  # Critical requirement: Source Selection < 3s
            "max_time_between_chunks_ms": 50
        },
        "memory": {
            "max_memory_mb": 10,  # Critical requirement: 10MB per request
            "check_interval_ms": 100
        },
        "resource_constraints": {
            "max_requests_per_second": 20,  # Critical requirement: API Rate Limit
            "connection_timeout_sec": 30,  # Critical requirement: Connection Timeout
            "max_results": 20  # Critical requirement: Max Results Per Query
        },
        "error_rate": {
            "max_error_rate": 0.01  # Critical requirement: Error Rate < 1%
        },
        "batch_size": 3,
        "min_chunks": 3
    }

@pytest.fixture
async def mock_llm_response() -> str:
    """Provide mock LLM response for testing."""
    return """
    Based on the search results, here are the key points:

    1. First key point from the analysis [1]
    2. Second key point combining multiple sources [1,2]
    3. Third key point with specific details [2]

    References:
    [1] Test Result 1 (https://example.com/1)
    [2] Test Result 2 (https://example.com/2)
    """