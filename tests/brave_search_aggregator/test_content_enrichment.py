"""Tests for content enrichment component."""
import json
import time
import pytest
from typing import Dict, Any, List, AsyncIterator
import asyncio

from brave_search_aggregator.synthesizer.content_enricher import ContentEnricher, EnrichedContent
from brave_search_aggregator.utils.config import EnricherConfig

# Load test data from enrichment_scenarios.json
with open("tests/brave_search_aggregator/test_data/enrichment_scenarios.json", "r") as f:
    TEST_DATA = json.load(f)

@pytest.fixture
def content_enricher():
    """Create ContentEnricher instance with test configuration."""
    config = EnricherConfig(
        min_enrichment_score=0.8,
        min_diversity_score=0.7,
        min_depth_score=0.7,
        max_enrichment_time_ms=100,
        max_memory_mb=10,
        max_chunk_size_kb=16,
        requests_per_second=20,
        connection_timeout_sec=30,
        max_results=20,
        enable_streaming=True,
        enable_memory_tracking=True,
        enable_performance_tracking=True,
        batch_size=3
    )
    return ContentEnricher(config)

async def create_content_stream(content_items: List[Dict[str, Any]]) -> AsyncIterator[Dict[str, Any]]:
    """Create an async iterator from content items."""
    for item in content_items:
        yield item
        await asyncio.sleep(0.01)  # Reduced sleep time for better performance

@pytest.mark.asyncio
async def test_content_enrichment_streaming(content_enricher):
    """Test streaming content enrichment functionality."""
    content_items = TEST_DATA["enrichment_tests"]
    content_stream = create_content_stream([item["input"] for item in content_items])
    
    results = []
    start_time = time.time()
    
    async for result in content_enricher.enrich_stream(content_stream):
        assert isinstance(result, EnrichedContent)
        results.append(result)
        
        # Verify timing requirements
        assert time.time() - start_time < 1.0  # First result within 1s
        
    assert len(results) == len(content_items)
    assert any(r.enrichment_score > 0.8 for r in results)
    assert content_enricher.resource_manager.current_memory_mb < 10
    
    # Verify state tracking
    assert content_enricher.processing_state.processed_count == len(content_items)
    assert content_enricher.processing_state.error_count == 0
    assert content_enricher.processing_state.get_error_rate() == 0
    assert len(content_enricher.processing_state.successful_items) == len(content_items)

@pytest.mark.asyncio
async def test_content_enrichment_performance(content_enricher):
    """Test content enrichment performance metrics."""
    scenario = TEST_DATA["performance_scenarios"][0]
    content_items = []
    
    # Create test items from template
    for i in range(scenario["batch_size"]):
        item = dict(scenario["content_template"])
        item["text"] = item["text"].format(index=i)
        content_items.append(item)
    
    content_stream = create_content_stream(content_items)
    start_time = time.time()
    results = []
    throughput_measurements = []
    last_check = start_time
    item_count = 0
    
    async for result in content_enricher.enrich_stream(content_stream):
        results.append(result)
        item_count += 1
        
        # Measure throughput every second
        current_time = time.time()
        if current_time - last_check >= 1.0:
            throughput = item_count / (current_time - last_check)
            throughput_measurements.append(throughput)
            last_check = current_time
            item_count = 0
    
    total_time = time.time() - start_time
    
    # Verify performance requirements
    assert total_time < scenario["requirements"]["max_total_time_ms"] / 1000  # Convert to seconds
    assert content_enricher.resource_manager.peak_memory < scenario["requirements"]["max_memory_mb"] * 1024 * 1024
    assert len(results) == len(content_items)
    
    # Verify throughput
    if throughput_measurements:
        avg_throughput = sum(throughput_measurements) / len(throughput_measurements)
        assert avg_throughput >= 2.0  # At least 2 items per second
        
    # Verify resource monitoring
    assert content_enricher.resource_manager.peak_memory > 0
    assert content_enricher.resource_manager.current_memory_mb < content_enricher.resource_manager.peak_memory

@pytest.mark.asyncio
async def test_content_enrichment_error_recovery(content_enricher):
    """Test error recovery during streaming."""
    # Create stream with various error scenarios
    error_scenarios = TEST_DATA["error_scenarios"]
    content_items = []
    for scenario in error_scenarios:
        content_items.extend(scenario["items"])
    
    content_stream = create_content_stream(content_items)
    results = []
    
    async for result in content_enricher.enrich_stream(content_stream):
        results.append(result)
    
    # Verify error handling and recovery
    assert len(results) > 0  # Should process valid items
    assert all(isinstance(r, EnrichedContent) for r in results)
    assert content_enricher.processing_state.error_count > 0
    assert content_enricher.processing_state.get_error_rate() <= 0.4  # Max 40% error rate for test data
    
    # Verify cleanup after errors
    assert not content_enricher.processing_state.current_batch  # Batch should be cleared
    assert content_enricher.resource_manager.current_memory_mb < 1  # Memory should be cleaned up

@pytest.mark.asyncio
async def test_content_enrichment_comprehensive(content_enricher):
    """Test comprehensive content enrichment."""
    test_case = TEST_DATA["enrichment_tests"][0]  # Use comprehensive test case
    result = await content_enricher.enrich(test_case["input"])
    
    assert isinstance(result, EnrichedContent)
    assert result.enrichment_score >= test_case["expected"]["enrichment_score"]
    assert result.diversity_score >= test_case["expected"]["diversity_score"]
    assert result.depth_score >= test_case["expected"]["depth_score"]
    
    # Verify quality metrics
    quality = test_case["expected"]["quality_metrics"]
    assert result.quality_metrics.trust_score >= quality["trust_score"]
    assert result.quality_metrics.reliability_score >= quality["reliability_score"]
    assert result.quality_metrics.authority_score >= quality["authority_score"]
    assert result.quality_metrics.freshness_score >= quality["freshness_score"]

@pytest.mark.asyncio
async def test_content_enrichment_intermediate(content_enricher):
    """Test intermediate content enrichment."""
    test_case = TEST_DATA["enrichment_tests"][1]  # Use intermediate test case
    result = await content_enricher.enrich(test_case["input"])
    
    assert isinstance(result, EnrichedContent)
    assert result.enrichment_score >= test_case["expected"]["enrichment_score"]
    assert result.diversity_score >= test_case["expected"]["diversity_score"]
    assert result.depth_score >= test_case["expected"]["depth_score"]

@pytest.mark.asyncio
async def test_content_enrichment_shallow(content_enricher):
    """Test shallow content enrichment."""
    test_case = TEST_DATA["enrichment_tests"][2]  # Use shallow test case
    result = await content_enricher.enrich(test_case["input"])
    
    assert isinstance(result, EnrichedContent)
    assert result.enrichment_score >= test_case["expected"]["enrichment_score"]
    assert result.diversity_score >= test_case["expected"]["diversity_score"]
    assert result.depth_score >= test_case["expected"]["depth_score"]

@pytest.mark.asyncio
async def test_content_enrichment_resource_management(content_enricher):
    """Test resource management during enrichment."""
    async with content_enricher.resource_manager:
        test_case = TEST_DATA["enrichment_tests"][0]
        result = await content_enricher.enrich(test_case["input"])
        assert result.enrichment_score >= test_case["expected"]["enrichment_score"]
        assert content_enricher.resource_manager.current_memory_mb < 10

@pytest.mark.asyncio
async def test_content_enrichment_batch_processing(content_enricher):
    """Test batch processing efficiency."""
    test_cases = TEST_DATA["enrichment_tests"]
    results = []
    async with content_enricher.resource_manager:
        for test_case in test_cases:
            result = await content_enricher.enrich(test_case["input"])
            results.append(result)
    
    assert len(results) == len(test_cases)
    assert all(isinstance(r, EnrichedContent) for r in results)
    assert any(r.enrichment_score > 0.8 for r in results)

@pytest.mark.asyncio
async def test_content_enrichment_error_handling(content_enricher):
    """Test error handling for invalid inputs."""
    with pytest.raises(ValueError):
        await content_enricher.enrich({})
    
    with pytest.raises(ValueError):
        await content_enricher.enrich(None)
    
    with pytest.raises(ValueError):
        await content_enricher.enrich({"text": ""})

@pytest.mark.asyncio
async def test_content_enrichment_resource_cleanup(content_enricher):
    """Test resource cleanup and memory management."""
    # Create large batch of items
    test_case = TEST_DATA["enrichment_tests"][0]
    content_items = [test_case["input"]] * 50  # 50 items
    content_stream = create_content_stream(content_items)
    
    results = []
    peak_memory = 0
    cleanup_count = 0
    
    async for result in content_enricher.enrich_stream(content_stream):
        results.append(result)
        current_memory = content_enricher.resource_manager.current_memory_mb
        peak_memory = max(peak_memory, current_memory)
        
        if content_enricher.processing_state.should_trigger_cleanup():
            cleanup_count += 1
    
    # Verify memory management
    assert peak_memory < 10  # Peak memory under limit
    assert cleanup_count > 0  # Cleanup was triggered
    assert len(results) == 50  # All items processed
    assert content_enricher.resource_manager.current_memory_mb < 1  # Memory cleaned up
    assert content_enricher.processing_state.processed_count == 50
    assert content_enricher.processing_state.error_count == 0

@pytest.mark.asyncio
async def test_content_enrichment_throughput_monitoring(content_enricher):
    """Test throughput monitoring and performance tracking."""
    # Create stream of items
    test_case = TEST_DATA["enrichment_tests"][0]
    content_items = [test_case["input"]] * 20  # 20 items
    content_stream = create_content_stream(content_items)
    
    start_time = time.time()
    results = []
    
    async for result in content_enricher.enrich_stream(content_stream):
        results.append(result)
    
    total_time = time.time() - start_time
    throughput = len(results) / total_time
    
    # Verify throughput requirements
    assert throughput >= 2.0  # At least 2 items per second
    assert content_enricher.throughput_counter >= 0
    assert content_enricher.last_throughput_check > start_time
    
    # Verify monitoring
    assert content_enricher.resource_manager.peak_memory > 0
    assert content_enricher.resource_manager.last_cleanup > start_time
    assert content_enricher.processing_state.processed_count == 20