"""
Tests for the EnhancedBraveKnowledgeAggregator component of the Brave Search Knowledge Aggregator.
"""
import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from typing import Dict, List, Any, AsyncGenerator

import aiohttp

from brave_search_aggregator.synthesizer.enhanced_brave_knowledge_aggregator import (
    EnhancedBraveKnowledgeAggregator
)
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.fetcher.content_fetcher import ContentFetcher
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer, QueryAnalysis
from brave_search_aggregator.synthesizer.content_analyzer import ContentAnalyzer, AnalysisResult
from brave_search_aggregator.synthesizer.enhanced_knowledge_synthesizer import (
    EnhancedKnowledgeSynthesizer, SynthesisResult
)
from brave_search_aggregator.utils.config import Config, AnalyzerConfig
from brave_search_aggregator.utils.error_handler import ErrorHandler


class AsyncIteratorMock:
    """Mock for async iterator that yields a sequence of values."""
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


@pytest.fixture
def config():
    """Provide a Config object for testing."""
    config = Config()
    config.analyzer = AnalyzerConfig()
    config.batch_size = 3
    config.max_results_per_query = 10
    config.enable_streaming_metrics = True
    config.max_event_delay_ms = 0  # No delay for testing
    return config


@pytest.fixture
def mock_query_analysis():
    """Provide a mock QueryAnalysis for testing."""
    return QueryAnalysis(
        query="test query",
        search_string="test query enhanced",
        complexity_score=0.8,
        confidence_score=0.9,
        input_type="search",
        segments=[
            {"text": "test", "type": "keyword", "confidence": 0.9},
            {"text": "query", "type": "keyword", "confidence": 0.9}
        ],
        insights="This is a test query about testing.",
        search_parameters={
            "count": 10,
            "offset": 0,
            "safe_search": "moderate"
        }
    )


@pytest.fixture
def mock_search_results():
    """Provide mock search results for testing."""
    return [
        {
            "title": "Test Result 1",
            "description": "This is the first test result about testing.",
            "link": "https://example.com/test1",
            "display_link": "example.com/test1",
            "age": "2d",
            "favicon": "https://example.com/favicon.ico"
        },
        {
            "title": "Test Result 2",
            "description": "This is the second test result about testing.",
            "link": "https://example.org/test2",
            "display_link": "example.org/test2",
            "age": "3d",
            "favicon": "https://example.org/favicon.ico"
        },
        {
            "title": "Test Result 3",
            "description": "This is the third test result with different content.",
            "link": "https://example.net/test3",
            "display_link": "example.net/test3",
            "age": "1w",
            "favicon": "https://example.net/favicon.ico"
        }
    ]


@pytest.fixture
def mock_fetch_results():
    """Provide mock fetch results for testing."""
    return [
        {
            "url": "https://example.com/test1",
            "content": "This is the content from the first test result. It contains detailed information about testing.",
            "content_type": "text/html",
            "fetch_time_ms": 150,
            "timestamp": time.time(),
            "size_bytes": 2000,
            "headers": {"Content-Type": "text/html; charset=utf-8"},
            "status": 200
        },
        {
            "url": "https://example.org/test2",
            "content": "Content from the second test result with more specific information about testing methodologies.",
            "content_type": "text/html",
            "fetch_time_ms": 180,
            "timestamp": time.time(),
            "size_bytes": 2500,
            "headers": {"Content-Type": "text/html; charset=utf-8"},
            "status": 200
        },
        {
            "url": "https://example.net/test3",
            "content": "Third result content with different information.",
            "content_type": "text/html",
            "fetch_time_ms": 120,
            "timestamp": time.time(),
            "size_bytes": 1800,
            "headers": {"Content-Type": "text/html; charset=utf-8"},
            "status": 200
        }
    ]


@pytest.fixture
def mock_analysis_results():
    """Provide mock content analysis results for testing."""
    return [
        AnalysisResult(
            source_url="https://example.com/test1",
            quality_score=0.85,
            relevance_score=0.9,
            key_points=[
                "Key point 1 about testing.",
                "Important information about test methodologies.",
                "Relevant testing context for the query."
            ],
            entities=["Testing", "Methodology", "Context"],
            sentiment="positive",
            category="technical",
            tags=["testing", "technical", "methodology"],
            summary="Summary of the first test result with relevant information about testing.",
            processing_time_ms=120,
            content_type="text/html",
            word_count=200,
            is_reliable=True,
            processing_metadata={"timestamp": time.time()}
        ),
        AnalysisResult(
            source_url="https://example.org/test2",
            quality_score=0.8,
            relevance_score=0.85,
            key_points=[
                "Second result key point about testing specifics.",
                "Details about test implementation strategies.",
                "Resource requirements for testing."
            ],
            entities=["Testing", "Implementation", "Resources"],
            sentiment="neutral",
            category="technical",
            tags=["testing", "implementation", "resources"],
            summary="Summary of the second test result with details about testing implementation.",
            processing_time_ms=130,
            content_type="text/html",
            word_count=250,
            is_reliable=True,
            processing_metadata={"timestamp": time.time()}
        ),
        AnalysisResult(
            source_url="https://example.net/test3",
            quality_score=0.7,
            relevance_score=0.6,
            key_points=[
                "Third result key point with different information.",
                "Less relevant information for the query.",
                "General context not specific to testing."
            ],
            entities=["Information", "Context"],
            sentiment="neutral",
            category="general",
            tags=["information", "general"],
            summary="Summary of the third test result with less relevant information.",
            processing_time_ms=100,
            content_type="text/html",
            word_count=180,
            is_reliable=True,
            processing_metadata={"timestamp": time.time()}
        )
    ]


@pytest.fixture
def mock_synthesis_result():
    """Provide a mock synthesis result for testing."""
    return SynthesisResult(
        content="Synthesized knowledge from test results about testing methodologies and implementation.",
        sources=["https://example.com/test1", "https://example.org/test2", "https://example.net/test3"],
        key_insights=[
            "Testing methodologies are important for effective testing.",
            "Implementation strategies vary based on test context.",
            "Resource requirements should be considered for testing."
        ],
        source_quality={
            "https://example.com/test1": 0.85,
            "https://example.org/test2": 0.8,
            "https://example.net/test3": 0.7
        },
        entity_map={
            "Testing": ["https://example.com/test1", "https://example.org/test2"],
            "Methodology": ["https://example.com/test1"],
            "Implementation": ["https://example.org/test2"],
            "Resources": ["https://example.org/test2"],
            "Information": ["https://example.net/test3"],
            "Context": ["https://example.com/test1", "https://example.net/test3"]
        },
        synthesis_time_ms=250,
        confidence_score=0.85,
        processing_metadata={
            "timestamp": time.time(),
            "synthesizer_version": "0.1.0"
        }
    )


@pytest.fixture
def mock_brave_client():
    """Provide a mock BraveSearchClient for testing."""
    client = AsyncMock(spec=BraveSearchClient)
    
    # Mock the session property
    session_mock = AsyncMock(spec=aiohttp.ClientSession)
    type(client).session = PropertyMock(return_value=session_mock)
    
    return client


@pytest.fixture
def mock_content_fetcher():
    """Provide a mock ContentFetcher for testing."""
    fetcher = AsyncMock(spec=ContentFetcher)
    return fetcher


@pytest.fixture
def mock_content_analyzer():
    """Provide a mock ContentAnalyzer for testing."""
    analyzer = AsyncMock(spec=ContentAnalyzer)
    return analyzer


@pytest.fixture
def mock_knowledge_synthesizer():
    """Provide a mock EnhancedKnowledgeSynthesizer for testing."""
    synthesizer = AsyncMock(spec=EnhancedKnowledgeSynthesizer)
    return synthesizer


@pytest.fixture
def mock_query_analyzer():
    """Provide a mock QueryAnalyzer for testing."""
    analyzer = AsyncMock(spec=QueryAnalyzer)
    return analyzer


@pytest.fixture
def aggregator(
    config,
    mock_brave_client,
    mock_content_fetcher,
    mock_content_analyzer,
    mock_knowledge_synthesizer,
    mock_query_analyzer,
    mock_query_analysis,
    mock_search_results,
    mock_fetch_results,
    mock_analysis_results,
    mock_synthesis_result
):
    """Provide an EnhancedBraveKnowledgeAggregator instance for testing."""
    # Configure mocks
    mock_query_analyzer.analyze_query.return_value = mock_query_analysis
    
    # Mock search async iterator
    mock_brave_client.search.return_value = AsyncIteratorMock(mock_search_results)
    
    # Mock fetch_stream async iterator
    mock_content_fetcher.fetch_stream.return_value = AsyncIteratorMock(mock_fetch_results)
    
    # Mock content analysis
    mock_content_analyzer.analyze.side_effect = lambda content, query: asyncio.Future(
        loop=asyncio.get_event_loop()
    ).set_result(
        next(
            (r for r in mock_analysis_results if r.source_url == content["url"]), 
            mock_analysis_results[0]
        )
    )
    
    # Mock knowledge synthesis
    mock_knowledge_synthesizer.synthesize.return_value = mock_synthesis_result
    
    # Create aggregator with mocks
    return EnhancedBraveKnowledgeAggregator(
        brave_client=mock_brave_client,
        config=config,
        content_fetcher=mock_content_fetcher,
        content_analyzer=mock_content_analyzer,
        knowledge_synthesizer=mock_knowledge_synthesizer,
        query_analyzer=mock_query_analyzer
    )


@pytest.mark.asyncio
async def test_process_query_basic(aggregator, mock_query_analyzer, mock_brave_client):
    """Test basic query processing without content enhancement."""
    # Process query without content enhancement
    results = []
    async for result in aggregator.process_query("test query", enable_content_enhancement=False):
        results.append(result)
    
    # Verify mock was called with correct parameters
    mock_query_analyzer.analyze_query.assert_called_once_with("test query")
    mock_brave_client.search.assert_called_once()
    
    # Verify results structure
    assert len(results) > 0
    
    # Verify all results have the correct type
    assert all(result["type"] == "content" for result in results)
    
    # Verify key event types are present
    content_types = [result["content_type"] for result in results]
    assert "analysis_status" in content_types
    assert "search_status" in content_types
    assert "search_result" in content_types
    assert "search_synthesis" in content_types
    
    # Verify search results are included
    search_results = [r for r in results if r["content_type"] == "search_result"]
    assert len(search_results) == 3  # Three mock search results


@pytest.mark.asyncio
async def test_process_query_with_content_enhancement(
    aggregator,
    mock_content_fetcher,
    mock_content_analyzer,
    mock_knowledge_synthesizer
):
    """Test query processing with content enhancement enabled."""
    # Process query with content enhancement
    results = []
    async for result in aggregator.process_query("test query", enable_content_enhancement=True):
        results.append(result)
    
    # Verify mocks were called with correct parameters
    mock_content_fetcher.fetch_stream.assert_called_once()
    assert mock_content_analyzer.analyze.call_count == 3  # Once for each fetch result
    mock_knowledge_synthesizer.synthesize.assert_called_once()
    
    # Verify results structure
    assert len(results) > 0
    
    # Verify all results have the correct type
    assert all(result["type"] == "content" for result in results)
    
    # Verify key event types are present
    content_types = [result["content_type"] for result in results]
    assert "analysis_status" in content_types
    assert "search_status" in content_types
    assert "search_result" in content_types
    assert "fetch_status" in content_types
    assert "fetch_progress" in content_types
    assert "synthesis_status" in content_types
    assert "final_synthesis" in content_types
    
    # Verify search results are included
    search_results = [r for r in results if r["content_type"] == "search_result"]
    assert len(search_results) == 3  # Three mock search results
    
    # Verify fetch progress is included
    fetch_progress = [r for r in results if r["content_type"] == "fetch_progress"]
    assert len(fetch_progress) == 3  # Three mock fetch results
    
    # Verify analysis results are included
    analysis_results = [r for r in results if r["content_type"] == "analysis_result"]
    assert len(analysis_results) == 3  # Three mock analysis results
    
    # Verify final synthesis is included
    synthesis_results = [r for r in results if r["content_type"] == "final_synthesis"]
    assert len(synthesis_results) == 1
    assert "content" in synthesis_results[0]
    assert synthesis_results[0]["content"] == "Synthesized knowledge from test results about testing methodologies and implementation."


@pytest.mark.asyncio
async def test_process_query_with_error_handling(aggregator, mock_query_analyzer):
    """Test error handling during query processing."""
    # Mock query_analyzer to raise an exception
    mock_query_analyzer.analyze_query.side_effect = ValueError("Test error")
    
    # Process query with error
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)
    
    # Verify results structure
    assert len(results) == 1  # Should only have error result
    
    # Verify error result
    error_result = results[0]
    assert error_result["type"] == "content"
    assert error_result["content_type"] == "error"
    assert "error" in error_result
    assert "Test error" in error_result["error"]
    assert "error_type" in error_result
    assert error_result["error_type"] == "ValueError"


@pytest.mark.asyncio
async def test_format_result(aggregator, mock_search_results):
    """Test search result formatting."""
    # Format a search result
    result = aggregator._format_result(mock_search_results[0])
    
    # Verify result structure
    assert isinstance(result, dict)
    assert "title" in result
    assert "description" in result
    assert "url" in result
    assert "display_url" in result
    assert "age" in result
    assert "favicon" in result
    
    # Verify result values
    assert result["title"] == "Test Result 1"
    assert result["description"] == "This is the first test result about testing."
    assert result["url"] == "https://example.com/test1"
    assert result["display_url"] == "example.com/test1"
    assert result["age"] == "2d"
    assert result["favicon"] == "https://example.com/favicon.ico"


@pytest.mark.asyncio
async def test_format_result_as_content(aggregator, mock_search_results):
    """Test search result formatting as content text."""
    # Format a search result as content
    content = aggregator._format_result_as_content(mock_search_results[0])
    
    # Verify content structure
    assert isinstance(content, str)
    assert "## Test Result 1" in content
    assert "This is the first test result about testing." in content
    assert "[example.com/test1](https://example.com/test1)" in content


@pytest.mark.asyncio
async def test_analyze_patterns(aggregator, mock_search_results):
    """Test pattern analysis in search results."""
    # Analyze patterns in search results
    patterns = aggregator._analyze_patterns(mock_search_results)
    
    # Verify patterns
    assert isinstance(patterns, list)
    assert len(patterns) > 0
    assert any("titles" in pattern for pattern in patterns)
    assert any("descriptions" in pattern for pattern in patterns)
    assert any("test" in pattern.lower() for pattern in patterns)  # Common term in results


@pytest.mark.asyncio
async def test_extract_common_terms(aggregator):
    """Test common term extraction from texts."""
    # Extract common terms from texts
    texts = [
        "This is a test text about Python programming and testing.",
        "Python is used for testing in many contexts.",
        "Testing with Python is common practice in programming."
    ]
    terms = aggregator._extract_common_terms(texts)
    
    # Verify terms
    assert isinstance(terms, list)
    assert "python" in terms
    assert "testing" in terms
    assert "programming" in terms
    
    # Check common words are excluded
    assert "this" not in terms
    assert "is" not in terms
    assert "a" not in terms
    assert "and" not in terms
    assert "in" not in terms
    assert "with" not in terms


@pytest.mark.asyncio
async def test_detect_content_type(aggregator):
    """Test content type detection from search results."""
    # Test different URLs
    youtube_result = {"link": "https://youtube.com/watch?v=test123"}
    wikipedia_result = {"link": "https://en.wikipedia.org/wiki/Test"}
    github_result = {"link": "https://github.com/test/repo"}
    stackoverflow_result = {"link": "https://stackoverflow.com/questions/12345/test"}
    docs_result = {"link": "https://docs.python.org/3/index.html"}
    blog_result = {"link": "https://blog.example.com/post"}
    edu_result = {"link": "https://university.edu/page"}
    gov_result = {"link": "https://agency.gov/page"}
    news_result = {"link": "https://news.example.com/article"}
    generic_result = {"link": "https://example.com/page"}
    
    # Verify detection
    assert aggregator._detect_content_type(youtube_result) == "video"
    assert aggregator._detect_content_type(wikipedia_result) == "encyclopedia"
    assert aggregator._detect_content_type(github_result) == "code_repository"
    assert aggregator._detect_content_type(stackoverflow_result) == "q_and_a"
    assert aggregator._detect_content_type(docs_result) == "documentation"
    assert aggregator._detect_content_type(blog_result) == "blog"
    assert aggregator._detect_content_type(edu_result) == "educational"
    assert aggregator._detect_content_type(gov_result) == "government"
    assert aggregator._detect_content_type(news_result) == "news"
    assert aggregator._detect_content_type(generic_result) == "webpage"


@pytest.mark.asyncio
async def test_select_sources(aggregator, mock_search_results, mock_query_analysis):
    """Test source selection from search results."""
    # Select sources
    sources = aggregator._select_sources(mock_search_results, mock_query_analysis)
    
    # Verify sources
    assert isinstance(sources, list)
    assert len(sources) <= 5  # Maximum 5 sources
    assert len(sources) == 3  # Should select all 3 mock results
    
    # Verify source structure
    for source, relevance in sources:
        assert isinstance(source, dict)
        assert isinstance(relevance, float)
        assert 0 <= relevance <= 1


@pytest.mark.asyncio
async def test_calculate_relevance(aggregator, mock_search_results, mock_query_analysis):
    """Test relevance calculation for search results."""
    # Calculate relevance
    relevance = aggregator._calculate_relevance(mock_search_results[0], mock_query_analysis)
    
    # Verify relevance
    assert isinstance(relevance, float)
    assert 0 <= relevance <= 1


@pytest.mark.asyncio
async def test_check_segment_matches(aggregator, mock_search_results, mock_query_analysis):
    """Test segment matching in search results."""
    # Check segment matches
    matches = aggregator._check_segment_matches(mock_search_results[0], mock_query_analysis)
    
    # Verify matches
    assert isinstance(matches, list)
    # The test segments include 'test', which should match the test results
    assert len(matches) > 0


@pytest.mark.asyncio
async def test_generate_basic_synthesis(aggregator, mock_search_results):
    """Test basic synthesis generation from search results."""
    # Generate basic synthesis
    synthesis = aggregator._generate_basic_synthesis(mock_search_results, "test query")
    
    # Verify synthesis
    assert isinstance(synthesis, str)
    assert "Search results for: test query" in synthesis
    assert "Test Result 1" in synthesis
    assert "Test Result 2" in synthesis
    assert "Test Result 3" in synthesis
    assert "example.com/test1" in synthesis
    assert "example.org/test2" in synthesis
    assert "example.net/test3" in synthesis
    assert "Results from Brave Search" in synthesis


@pytest.mark.asyncio
async def test_get_query_suggestions(aggregator, mock_query_analysis):
    """Test query suggestion extraction."""
    # Get query suggestions
    suggestions = aggregator._get_query_suggestions(mock_query_analysis)
    
    # Verify suggestions
    assert isinstance(suggestions, list)
    
    # Add additional insights with suggestions
    mock_query_analysis.insights = "Try using more specific terms. Consider adding technical details."
    
    # Get updated suggestions
    updated_suggestions = aggregator._get_query_suggestions(mock_query_analysis)
    
    # Verify updated suggestions
    assert isinstance(updated_suggestions, list)
    assert len(updated_suggestions) > 0
    assert any("try" in suggestion.lower() for suggestion in updated_suggestions)
    assert any("consider" in suggestion.lower() for suggestion in updated_suggestions)


@pytest.mark.asyncio
async def test_streaming_metrics(aggregator):
    """Test streaming metrics tracking and retrieval."""
    # Reset metrics
    aggregator._reset_streaming_metrics()
    
    # Track some events
    await aggregator._track_streaming_event("test_event_1")
    await asyncio.sleep(0.01)  # Small delay to ensure time difference
    await aggregator._track_streaming_event("test_event_2")
    await asyncio.sleep(0.01)  # Small delay to ensure time difference
    await aggregator._track_streaming_event("test_event_3")
    
    # Get metrics
    metrics = aggregator._get_streaming_metrics()
    
    # Verify metrics
    assert isinstance(metrics, dict)
    assert "start_time" in metrics
    assert "last_event_time" in metrics
    assert "events_emitted" in metrics
    assert "total_delay_ms" in metrics
    assert "max_delay_ms" in metrics
    assert "average_delay_ms" in metrics
    assert "total_time_ms" in metrics
    
    # Verify values
    assert metrics["events_emitted"] == 3  # Three events tracked
    assert metrics["total_time_ms"] > 0  # Should have some elapsed time
    assert metrics["total_delay_ms"] > 0  # Should have some delay
    assert metrics["max_delay_ms"] > 0  # Should have some max delay
    assert metrics["average_delay_ms"] > 0  # Should have some average delay
