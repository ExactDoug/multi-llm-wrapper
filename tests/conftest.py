"""
Pytest configuration and fixtures.
"""
import os
from typing import AsyncGenerator, Generator
import pytest
import aiohttp
from dotenv import load_dotenv

from brave_search_aggregator.utils.config import Config
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer
from brave_search_aggregator.synthesizer.knowledge_synthesizer import KnowledgeSynthesizer

# Load test environment variables
load_dotenv(".env.test", override=True)

@pytest.fixture
def config() -> Config:
    """Provide test configuration."""
    return Config(
        brave_api_key="test_key",
        max_results_per_query=5,
        timeout_seconds=5,
        rate_limit=10
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