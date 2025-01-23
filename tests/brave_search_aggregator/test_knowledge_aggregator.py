"""Tests for knowledge aggregator component."""
import pytest
from src.brave_search_aggregator.synthesizer.knowledge_aggregator import (
    KnowledgeAggregator,
    SourceType,
    AggregationResult,
    SourceConfig
)

@pytest.fixture
def aggregator():
    """Fixture providing a KnowledgeAggregator instance."""
    return KnowledgeAggregator()

@pytest.fixture
def test_sources():
    """Fixture providing test source names."""
    return ["brave_search", "llm1", "llm2"]

@pytest.mark.asyncio
async def test_process_source(aggregator):
    """Test processing of a single source."""
    result = await aggregator.process_source(
        "brave_search",
        "test query",
        preserve_nuances=True
    )
    
    assert isinstance(result, dict)
    assert "source" in result
    assert "content" in result
    assert "confidence" in result
    assert "nuances" in result
    assert result["source"] == "brave_search"
    assert isinstance(result["confidence"], float)

@pytest.mark.asyncio
async def test_process_source_invalid(aggregator):
    """Test handling of invalid source."""
    with pytest.raises(ValueError):
        await aggregator.process_source(
            "invalid_source",
            "test query"
        )

@pytest.mark.asyncio
async def test_resolve_conflicts(aggregator):
    """Test conflict resolution between sources."""
    test_results = [
        {
            "source": "source1",
            "content": "content1",
            "confidence": 0.8
        },
        {
            "source": "source2",
            "content": "content2",
            "confidence": 0.9
        }
    ]
    
    resolved = await aggregator.resolve_conflicts(test_results)
    assert isinstance(resolved, list)
    assert len(resolved) == 2
    # Should be sorted by confidence (highest first)
    assert resolved[0]["confidence"] == 0.9
    assert resolved[1]["confidence"] == 0.8

@pytest.mark.asyncio
async def test_parallel_processing(aggregator, test_sources):
    """Test parallel processing of multiple sources."""
    result = await aggregator.process_parallel(
        "test query",
        test_sources,
        preserve_nuances=True
    )
    
    assert isinstance(result, AggregationResult)
    assert result.all_sources_processed
    assert result.conflicts_resolved
    assert result.nuances_preserved
    assert isinstance(result.processing_time, float)
    assert result.processing_time > 0
    
    # Check source metrics
    assert len(result.source_metrics) == len(test_sources)
    for source in test_sources:
        assert source in result.source_metrics
        metrics = result.source_metrics[source]
        assert "confidence" in metrics
        assert "processing_time" in metrics

@pytest.mark.asyncio
async def test_parallel_processing_no_nuances(aggregator, test_sources):
    """Test parallel processing without nuance preservation."""
    result = await aggregator.process_parallel(
        "test query",
        test_sources,
        preserve_nuances=False
    )
    
    assert isinstance(result, AggregationResult)
    assert not result.nuances_preserved
    
    # Verify no nuances in content
    for source in test_sources:
        metrics = result.source_metrics[source]
        assert "nuances" not in metrics

@pytest.mark.asyncio
async def test_source_configs(aggregator):
    """Test source configuration handling."""
    for source, config in aggregator.source_configs.items():
        assert isinstance(config, SourceConfig)
        assert isinstance(config.source_type, SourceType)
        assert isinstance(config.processing_weight, float)
        assert isinstance(config.timeout_seconds, int)
        assert isinstance(config.max_retries, int)

@pytest.mark.asyncio
async def test_parallel_processing_partial_failure(aggregator):
    """Test handling of partial source processing failure."""
    # Include an invalid source to test error handling
    sources = ["brave_search", "invalid_source", "llm1"]
    
    result = await aggregator.process_parallel(
        "test query",
        sources,
        preserve_nuances=True
    )
    
    assert isinstance(result, AggregationResult)
    assert not result.all_sources_processed  # Should be False due to invalid source
    assert len(result.source_metrics) < len(sources)  # Should only have metrics for valid sources

@pytest.mark.asyncio
async def test_content_combination(aggregator, test_sources):
    """Test content combination from multiple sources."""
    result = await aggregator.process_parallel(
        "test query",
        test_sources,
        preserve_nuances=True
    )
    
    assert isinstance(result.content, str)
    # Content should contain all source names
    for source in test_sources:
        assert source in result.content