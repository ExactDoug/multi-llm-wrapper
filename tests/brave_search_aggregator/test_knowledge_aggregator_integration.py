"""Integration tests for BraveKnowledgeAggregator."""
import pytest
import asyncio
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

from brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer, QueryAnalysis
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient
from brave_search_aggregator.synthesizer.knowledge_synthesizer import KnowledgeSynthesizer
from brave_search_aggregator.utils.config import Config, AnalyzerConfig

@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        brave_api_key="test_key",
        max_results_per_query=10,
        timeout_seconds=30,
        rate_limit=20,
        analyzer=AnalyzerConfig(
            max_memory_mb=10,
            input_type_confidence_threshold=0.8,
            complexity_threshold=0.7,
            ambiguity_threshold=0.6,
            enable_segmentation=True,
            max_segments=5,
            enable_streaming_analysis=True,
            analysis_batch_size=3
        )
    )

@pytest.fixture
def mock_brave_client():
    """Create mock BraveSearchClient."""
    client = Mock(spec=BraveSearchClient)
    
    async def mock_search(query: str):
        results = [
            {
                "title": "Test Result 1",
                "description": "Technical documentation about Python",
                "url": "https://docs.python.org/3/"
            },
            {
                "title": "Test Result 2",
                "description": "Scientific paper about algorithms",
                "url": "https://example.com/paper.pdf"
            }
        ]
        for result in results:
            yield result
            
    client.search = mock_search
    return client

@pytest.fixture
def mock_query_analyzer():
    """Create mock QueryAnalyzer."""
    analyzer = Mock(spec=QueryAnalyzer)
    analyzer.analyze_query = AsyncMock(return_value=QueryAnalysis(
        is_suitable_for_search=True,
        search_string="test query",
        complexity="moderate",
        is_ambiguous=False,
        insights="Test insights",
        performance_metrics={
            "processing_time_ms": 100,
            "memory_usage_mb": 5
        }
    ))
    return analyzer

@pytest.fixture
def mock_knowledge_synthesizer():
    """Create mock KnowledgeSynthesizer."""
    synthesizer = Mock(spec=KnowledgeSynthesizer)
    synthesizer.synthesize = AsyncMock(return_value="Test synthesis")
    return synthesizer

@pytest.mark.asyncio
async def test_process_query_integration(
    config,
    mock_brave_client,
    mock_query_analyzer,
    mock_knowledge_synthesizer
):
    """Test full query processing integration."""
    aggregator = BraveKnowledgeAggregator(
        brave_client=mock_brave_client,
        config=config,
        query_analyzer=mock_query_analyzer,
        knowledge_synthesizer=mock_knowledge_synthesizer
    )
    
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)
        
    # Verify sequence of events
    assert len(results) > 0
    
    # Check analysis phase
    analysis_complete = next(r for r in results if r["type"] == "status" and r["stage"] == "analysis_complete")
    assert analysis_complete["query_analysis"]["complexity"] == "moderate"
    
    # Check search phase
    search_results = [r for r in results if r["type"] == "search_result"]
    assert len(search_results) > 0
    for result in search_results:
        assert "relevance_score" in result["context"]
        assert "matches_segments" in result["context"]
        
    # Check final synthesis
    final_synthesis = next(r for r in results if r["type"] == "final_synthesis")
    assert "analysis_summary" in final_synthesis
    assert "performance_metrics" in final_synthesis["analysis_summary"]

@pytest.mark.asyncio
async def test_error_handling_integration(
    config,
    mock_brave_client,
    mock_query_analyzer,
    mock_knowledge_synthesizer
):
    """Test error handling in integrated components."""
    # Make query analyzer raise an error
    mock_query_analyzer.analyze_query = AsyncMock(side_effect=ValueError("Test error"))
    
    aggregator = BraveKnowledgeAggregator(
        brave_client=mock_brave_client,
        config=config,
        query_analyzer=mock_query_analyzer,
        knowledge_synthesizer=mock_knowledge_synthesizer
    )
    
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)
        
    # Verify error handling
    error_result = next(r for r in results if r["type"] == "error")
    assert "Test error" in error_result["error"]
    assert "context" in error_result

@pytest.mark.asyncio
async def test_streaming_analysis_integration(
    config,
    mock_brave_client,
    mock_query_analyzer,
    mock_knowledge_synthesizer
):
    """Test streaming analysis with batch processing."""
    aggregator = BraveKnowledgeAggregator(
        brave_client=mock_brave_client,
        config=config,
        query_analyzer=mock_query_analyzer,
        knowledge_synthesizer=mock_knowledge_synthesizer
    )
    
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)
        
    # Verify batch analysis
    interim_analyses = [r for r in results if r["type"] == "interim_analysis"]
    assert len(interim_analyses) > 0
    for analysis in interim_analyses:
        assert "batch_size" in analysis["performance"]
        assert analysis["performance"]["batch_size"] <= config.analyzer.analysis_batch_size

@pytest.mark.asyncio
async def test_source_selection_integration(
    config,
    mock_brave_client,
    mock_query_analyzer,
    mock_knowledge_synthesizer
):
    """Test source selection with relevance scoring."""
    aggregator = BraveKnowledgeAggregator(
        brave_client=mock_brave_client,
        config=config,
        query_analyzer=mock_query_analyzer,
        knowledge_synthesizer=mock_knowledge_synthesizer
    )
    
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)
        
    # Verify source selection
    source_selection = next(r for r in results if r["type"] == "status" and r["stage"] == "source_selection")
    assert "selection_criteria" in source_selection
    assert len(source_selection["sources"]) <= aggregator.min_sources
    for source in source_selection["sources"]:
        assert "relevance" in source
        assert "content_type" in source