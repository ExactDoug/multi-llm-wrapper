"""
Test fixtures for Brave Search Knowledge Aggregator tests.
"""
import pytest
from typing import AsyncGenerator, Dict
import aiohttp
from unittest.mock import AsyncMock, MagicMock

from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer, QueryAnalysis
from brave_search_aggregator.utils.config import Config, AnalyzerConfig

class AsyncIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            item = self.items[self.index]
            self.index += 1
            return item
        except IndexError:
            raise StopAsyncIteration

class SearchMock:
    def __init__(self, items):
        self.items = items

    def __call__(self, *args, **kwargs):
        return AsyncIterator(self.items)

@pytest.fixture
def mock_brave_client():
    client = AsyncMock(spec=BraveSearchClient)
    results = [
        {
            'title': 'Test Result 1',
            'url': 'https://example.com/1',
            'description': 'Description 1'
        },
        {
            'title': 'Test Result 2',
            'url': 'https://example.com/2',
            'description': 'Description 2'
        }
    ]
    # Make search return an async iterator when called
    client.search = SearchMock(results)
    return client

@pytest.fixture
def mock_query_analyzer():
    analyzer = AsyncMock()
    analyzer.analyze_query.return_value = QueryAnalysis(
        search_string="test query",
        complexity=0.8,
        is_suitable_for_search=True,
        is_ambiguous=False,
        insights="Test query analysis insights",
        performance_metrics={"processing_time_ms": 50},
        input_type=MagicMock(
            primary_type=MagicMock(name="GENERAL"),
            confidence=0.9
        )
    )
    return analyzer

@pytest.fixture
def mock_knowledge_synthesizer():
    synthesizer = AsyncMock()
    synthesizer.synthesize.return_value = "Knowledge synthesis from Test Result 1 and Test Result 2: Test knowledge synthesis"
    return synthesizer

@pytest.fixture
def browser_test_config():
    """Provide browser test configuration."""
    return {
        "viewport": {
            "width": 1280,
            "height": 800
        },
        "performance": {
            "min_fps": 30,
            "max_frame_time_ms": 33,  # ~30fps
            "max_memory_mb": 100  # Critical requirement: 10MB per request
        },
        "streaming": {
            "max_first_chunk_ms": 100,  # Critical requirement: First Status < 100ms
            "max_first_result_ms": 1000,  # Critical requirement: First Result < 1s
            "max_source_selection_ms": 3000,  # Critical requirement: Source Selection < 3s
            "min_chunks": 3
        }
    }

@pytest.fixture
def streaming_test_config():
    """Provide streaming test configuration."""
    return {
        "timing": {
            "max_first_chunk_ms": 100,  # Critical requirement: First Status < 100ms
            "max_first_result_ms": 1000,  # Critical requirement: First Result < 1s
            "max_source_selection_ms": 3000,  # Critical requirement: Source Selection < 3s
            "max_time_between_chunks_ms": 70,
            "max_total_time_ms": 10000
        },
        "memory": {
            "max_memory_mb": 100,  # Critical requirement: 10MB per request
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
