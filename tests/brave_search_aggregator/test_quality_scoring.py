"""Tests for quality scoring component."""
import json
import time
import pytest
from typing import Dict, Any, List, AsyncIterator
import asyncio

from brave_search_aggregator.synthesizer.quality_scorer import QualityScorer, QualityScore
from brave_search_aggregator.utils.config import QualityConfig, QualityResourceConfig

# Load test data from synthesis_scenarios.json
with open("tests/brave_search_aggregator/test_data/synthesis_scenarios.json", "r") as f:
    TEST_DATA = json.load(f)

TEST_CONTENT = {
    "high_quality": {
        "text": "Detailed technical analysis of quantum computing applications in cryptography",
        "sources": ["research_paper", "academic_journal", "expert_review"],
        "depth": "comprehensive",
        "citations": 12,
        "technical_accuracy": 0.95
    },
    "medium_quality": {
        "text": "Overview of quantum computing basics",
        "sources": ["educational_site", "blog"],
        "depth": "intermediate",
        "citations": 5,
        "technical_accuracy": 0.8
    },
    "low_quality": {
        "text": "Brief mention of quantum computers",
        "sources": ["social_media"],
        "depth": "shallow",
        "citations": 0,
        "technical_accuracy": 0.5
    }
}

@pytest.fixture
def quality_scorer():
    """Create QualityScorer instance with test configuration."""
    config = QualityConfig(
        min_quality_score=0.8,
        min_confidence_score=0.7,
        required_depth="comprehensive",
        max_memory_mb=10,
        enable_streaming=True,
        batch_size=3,
        resources=QualityResourceConfig(
            requests_per_second=20,
            burst_size=5,
            recovery_time_ms=100,
            connection_timeout_sec=30,
            operation_timeout_sec=25,
            cleanup_timeout_sec=5,
            max_results=20,
            batch_size=5,
            overflow_behavior="truncate"
        )
    )
    return QualityScorer(config)

@pytest.mark.asyncio
async def test_rate_limiting(quality_scorer):
    """Test rate limiting behavior."""
    scenario = TEST_DATA["resource_constraint_scenarios"][0]  # rate_limit_test
    content = scenario["items"][0]
    
    # Create burst of requests
    start_time = time.time()
    request_count = 0
    throttled_count = 0
    
    for _ in range(scenario["request_pattern"]["total_requests"]):
        try:
            result = await quality_scorer.evaluate(content)
            request_count += 1
            
            # Check if within burst limit
            if request_count <= scenario["request_pattern"]["burst_size"]:
                assert time.time() - start_time < 1.0
            
            # Simulate rapid requests
            if request_count % 3 == 0:  # Every third request is rapid
                continue  # Skip sleep to trigger rate limiting
            await asyncio.sleep(scenario["request_pattern"]["interval_ms"] / 1000)
        except Exception as e:
            assert "rate limit exceeded" in str(e).lower()
            throttled_count += 1
            # Allow recovery time
            await asyncio.sleep(scenario["expected_behavior"]["recovery_time_ms"] / 1000)
    
    # Verify rate limiting
    total_time = time.time() - start_time
    actual_rate = request_count / total_time
    assert actual_rate <= scenario["expected_behavior"]["max_requests_per_second"]
    assert throttled_count > 0, "Rate limiting was not triggered"

@pytest.mark.asyncio
async def test_connection_timeout(quality_scorer):
    """Test connection timeout behavior."""
    scenario = TEST_DATA["resource_constraint_scenarios"][1]  # timeout_test
    content = scenario["items"][0]
    
    start_time = time.time()
    try:
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                quality_scorer.evaluate(content),
                timeout=scenario["expected_behavior"]["connection_timeout_sec"]
            )
    finally:
        # Ensure cleanup happens even after timeout
        await quality_scorer.resource_manager.cleanup()
        assert quality_scorer.resource_manager.current_memory_mb < 1
    
    # Verify timeout occurred within expected window
    elapsed = time.time() - start_time
    assert elapsed < scenario["expected_behavior"]["connection_timeout_sec"] + 1

@pytest.mark.asyncio
async def test_results_limit(quality_scorer):
    """Test results limit enforcement."""
    scenario = TEST_DATA["resource_constraint_scenarios"][2]  # results_limit_test
    
    # Create test items
    content_items = []
    for i in range(scenario["batch_config"]["total_items"]):
        item = dict(scenario["items"][0])
        item["text"] = item["text"].format(index=i)
        content_items.append(item)
    
    content_stream = create_content_stream(content_items)
    results = []
    skipped_count = 0
    
    async for result in quality_scorer.evaluate_stream(content_stream):
        if len(results) >= scenario["expected_behavior"]["max_results"]:
            skipped_count += 1
            continue
            
        results.append(result)
        
        # Verify batch processing
        if len(results) % scenario["batch_config"]["batch_size"] == 0:
            assert quality_scorer.processing_state.should_trigger_cleanup()
            # Verify cleanup happened
            assert quality_scorer.resource_manager.current_memory_mb < quality_scorer.config.max_memory_mb
    
    # Verify results limit and overflow behavior
    assert len(results) == scenario["expected_behavior"]["max_results"]
    assert skipped_count > 0, "Overflow handling was not triggered"
    assert quality_scorer.processing_state.processed_count == scenario["expected_behavior"]["max_results"]
    assert quality_scorer.processing_state.error_count == 0

async def create_content_stream(content_items: List[Dict[str, Any]]) -> AsyncIterator[Dict[str, Any]]:
    """Create an async iterator from content items."""
    for item in content_items:
        yield item
        await asyncio.sleep(0.1)  # Simulate processing time

@pytest.mark.asyncio
async def test_quality_scoring_streaming(quality_scorer):
    """Test streaming quality scoring functionality."""
    content_items = list(TEST_CONTENT.values())
    content_stream = create_content_stream(content_items)
    
    results = []
    start_time = time.time()
    
    async for result in quality_scorer.evaluate_stream(content_stream):
        assert isinstance(result, QualityScore)
        results.append(result)
        
        # Verify timing requirements
        assert time.time() - start_time < 1.0  # First result within 1s
        
    assert len(results) == len(content_items)
    assert any(r.quality_score > 0.8 for r in results)
    assert quality_scorer.resource_manager.current_memory_mb < 10
    
    # Verify state tracking
    assert quality_scorer.processing_state.processed_count == len(content_items)
    assert quality_scorer.processing_state.error_count == 0
    assert quality_scorer.processing_state.get_error_rate() == 0
    assert len(quality_scorer.processing_state.successful_items) == len(content_items)

@pytest.mark.asyncio
async def test_quality_scoring_performance(quality_scorer):
    """Test quality scoring performance metrics."""
    content_items = TEST_DATA["quality_tests"]
    content_stream = create_content_stream(content_items)
    
    start_time = time.time()
    results = []
    throughput_measurements = []
    last_check = start_time
    item_count = 0
    
    async for result in quality_scorer.evaluate_stream(content_stream):
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
    assert total_time < 3.0  # Complete within 3s
    assert quality_scorer.resource_manager.peak_memory < 10 * 1024 * 1024  # Under 10MB
    assert len(results) == len(content_items)
    
    # Verify throughput
    if throughput_measurements:
        avg_throughput = sum(throughput_measurements) / len(throughput_measurements)
        assert avg_throughput >= 2.0  # At least 2 items per second
        
    # Verify resource monitoring
    assert quality_scorer.resource_manager.peak_memory > 0
    assert quality_scorer.resource_manager.current_memory_mb < quality_scorer.resource_manager.peak_memory

@pytest.mark.asyncio
async def test_quality_scoring_error_recovery(quality_scorer):
    """Test error recovery during streaming."""
    # Create stream with various error scenarios
    content_items = [
        TEST_CONTENT["high_quality"],
        {},  # Invalid item
        TEST_CONTENT["medium_quality"],
        {"text": "Invalid", "sources": []},  # Another invalid item
        TEST_CONTENT["low_quality"]
    ]
    content_stream = create_content_stream(content_items)
    
    results = []
    async for result in quality_scorer.evaluate_stream(content_stream):
        results.append(result)
    
    # Verify error handling and recovery
    assert len(results) == 3  # Should process valid items only
    assert all(isinstance(r, QualityScore) for r in results)
    assert quality_scorer.processing_state.error_count == 2
    assert quality_scorer.processing_state.get_error_rate() == 0.4  # 2 errors out of 5 items
    
    # Verify state recovery
    assert len(quality_scorer.processing_state.successful_items) == 3
    assert all(item in quality_scorer.processing_state.successful_items 
              for item in [TEST_CONTENT["high_quality"], 
                         TEST_CONTENT["medium_quality"],
                         TEST_CONTENT["low_quality"]])
    
    # Verify cleanup after errors
    assert not quality_scorer.processing_state.current_batch  # Batch should be cleared
    assert quality_scorer.resource_manager.current_memory_mb < 1  # Memory should be cleaned up

@pytest.mark.asyncio
async def test_quality_scoring_high_quality(quality_scorer):
    """Test quality scoring for high quality content."""
    result = await quality_scorer.evaluate(TEST_CONTENT["high_quality"])
    assert isinstance(result, QualityScore)
    assert result.quality_score > 0.8
    assert result.confidence_score > 0.7
    assert result.depth_rating == "comprehensive"

@pytest.mark.asyncio
async def test_quality_scoring_medium_quality(quality_scorer):
    """Test quality scoring for medium quality content."""
    result = await quality_scorer.evaluate(TEST_CONTENT["medium_quality"])
    assert isinstance(result, QualityScore)
    assert result.quality_score <= 0.8
    assert result.confidence_score > 0.6
    assert result.depth_rating == "intermediate"

@pytest.mark.asyncio
async def test_quality_scoring_low_quality(quality_scorer):
    """Test quality scoring for low quality content."""
    result = await quality_scorer.evaluate(TEST_CONTENT["low_quality"])
    assert isinstance(result, QualityScore)
    assert result.quality_score < 0.6
    assert result.confidence_score < 0.7
    assert result.depth_rating == "shallow"

@pytest.mark.asyncio
async def test_quality_scoring_resource_management(quality_scorer):
    """Test resource management during quality scoring."""
    async with quality_scorer.resource_manager:
        result = await quality_scorer.evaluate(TEST_CONTENT["high_quality"])
        assert result.quality_score > 0.8
        assert quality_scorer.resource_manager.current_memory_mb < 10

@pytest.mark.asyncio
async def test_quality_scoring_batch_processing(quality_scorer):
    """Test batch processing efficiency."""
    results = []
    async with quality_scorer.resource_manager:
        for content in TEST_CONTENT.values():
            result = await quality_scorer.evaluate(content)
            results.append(result)
    
    assert len(results) == 3
    assert all(isinstance(r, QualityScore) for r in results)
    assert any(r.quality_score > 0.8 for r in results)

@pytest.mark.asyncio
async def test_quality_scoring_error_handling(quality_scorer):
    """Test error handling for invalid inputs."""
    with pytest.raises(ValueError):
        await quality_scorer.evaluate({})

    with pytest.raises(ValueError):
        await quality_scorer.evaluate(None)

    with pytest.raises(ValueError):
        await quality_scorer.evaluate({"text": ""})

@pytest.mark.asyncio
async def test_quality_scoring_resource_cleanup(quality_scorer):
    """Test resource cleanup and memory management."""
    # Create large batch of items
    content_items = [TEST_CONTENT["high_quality"]] * 50  # 50 items
    content_stream = create_content_stream(content_items)
    
    results = []
    peak_memory = 0
    cleanup_count = 0
    
    async for result in quality_scorer.evaluate_stream(content_stream):
        results.append(result)
        current_memory = quality_scorer.resource_manager.current_memory_mb
        peak_memory = max(peak_memory, current_memory)
        
        if quality_scorer.processing_state.should_trigger_cleanup():
            cleanup_count += 1
    
    # Verify memory management
    assert peak_memory < 10  # Peak memory under limit
    assert cleanup_count > 0  # Cleanup was triggered
    assert len(results) == 50  # All items processed
    assert quality_scorer.resource_manager.current_memory_mb < 1  # Memory cleaned up
    assert quality_scorer.processing_state.processed_count == 50
    assert quality_scorer.processing_state.error_count == 0

@pytest.mark.asyncio
async def test_quality_scoring_throughput_monitoring(quality_scorer):
    """Test throughput monitoring and performance tracking."""
    # Create stream of items
    content_items = [TEST_CONTENT["high_quality"]] * 20  # 20 items
    content_stream = create_content_stream(content_items)
    
    start_time = time.time()
    results = []
    
    async for result in quality_scorer.evaluate_stream(content_stream):
        results.append(result)
    
    total_time = time.time() - start_time
    throughput = len(results) / total_time
    
    # Verify throughput requirements
    assert throughput >= 2.0  # At least 2 items per second
    assert quality_scorer.throughput_counter >= 0
    assert quality_scorer.last_throughput_check > start_time
    
    # Verify monitoring
    assert quality_scorer.resource_manager.peak_memory > 0
    assert quality_scorer.resource_manager.last_cleanup > start_time
    assert quality_scorer.processing_state.processed_count == 20