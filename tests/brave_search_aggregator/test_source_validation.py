"""Tests for source validation component."""
import json
import time
import pytest
from typing import Dict, Any, List, AsyncIterator
import asyncio

from brave_search_aggregator.synthesizer.source_validator import SourceValidator, ValidationResult
from brave_search_aggregator.utils.config import SourceValidationConfig

# Load test data from validation_scenarios.json
with open("tests/brave_search_aggregator/test_data/validation_scenarios.json", "w") as f:
    TEST_DATA = {
        "validation_tests": [
            {
                "text": "Comprehensive analysis of quantum computing applications",
                "sources": [
                    "research_paper",
                    "academic_journal",
                    "expert_review"
                ],
                "depth": "comprehensive",
                "citations": 15,
                "technical_accuracy": 0.95,
                "timestamp": time.time(),
                "expected_scores": {
                    "trust": 0.85,
                    "reliability": 0.9,
                    "authority": 0.85,
                    "freshness": 1.0
                }
            },
            {
                "text": "Overview of quantum computing basics",
                "sources": [
                    "educational_site",
                    "blog"
                ],
                "depth": "intermediate",
                "citations": 5,
                "technical_accuracy": 0.8,
                "timestamp": time.time() - 2592000,  # 1 month old
                "expected_scores": {
                    "trust": 0.7,
                    "reliability": 0.75,
                    "authority": 0.6,
                    "freshness": 0.8
                }
            },
            {
                "text": "Brief introduction to quantum computers",
                "sources": [
                    "social_media"
                ],
                "depth": "shallow",
                "citations": 1,
                "technical_accuracy": 0.6,
                "timestamp": time.time() - 15552000,  # 6 months old
                "expected_scores": {
                    "trust": 0.5,
                    "reliability": 0.55,
                    "authority": 0.4,
                    "freshness": 0.6
                }
            }
        ],
        "resource_constraint_scenarios": [
            {
                "name": "rate_limit_test",
                "items": [{
                    "text": "Rate limit test content",
                    "sources": ["research_paper"],
                    "depth": "comprehensive",
                    "citations": 10,
                    "technical_accuracy": 0.9
                }],
                "request_pattern": {
                    "burst_size": 5,
                    "total_requests": 25,
                    "interval_ms": 100
                },
                "expected_behavior": {
                    "max_requests_per_second": 20,
                    "recovery_time_ms": 100,
                    "error_handling": "throttle"
                }
            },
            {
                "name": "timeout_test",
                "items": [{
                    "text": "Timeout test content",
                    "sources": ["academic_journal"],
                    "depth": "comprehensive",
                    "citations": 8,
                    "technical_accuracy": 0.85,
                    "delay_ms": 35000
                }],
                "expected_behavior": {
                    "connection_timeout_sec": 30,
                    "operation_timeout_sec": 25,
                    "cleanup_timeout_sec": 5,
                    "error_handling": "terminate"
                }
            },
            {
                "name": "results_limit_test",
                "items": [{
                    "text": "Results limit test content {index}",
                    "sources": ["expert_review"],
                    "depth": "comprehensive",
                    "citations": 5,
                    "technical_accuracy": 0.8
                }],
                "batch_config": {
                    "total_items": 25,
                    "batch_size": 5
                },
                "expected_behavior": {
                    "max_results": 20,
                    "overflow_behavior": "truncate",
                    "error_handling": "skip"
                }
            }
        ]
    }
    json.dump(TEST_DATA, f, indent=4)

TEST_CONTENT = {
    "high_authority": {
        "text": "Detailed analysis of quantum computing security implications",
        "sources": ["research_paper", "academic_journal", "expert_review"],
        "depth": "comprehensive",
        "citations": 15,
        "technical_accuracy": 0.95,
        "timestamp": time.time()
    },
    "medium_authority": {
        "text": "Overview of quantum computing applications",
        "sources": ["educational_site", "expert_review"],
        "depth": "intermediate",
        "citations": 8,
        "technical_accuracy": 0.85,
        "timestamp": time.time() - 2592000  # 1 month old
    },
    "low_authority": {
        "text": "Basic quantum computing concepts",
        "sources": ["blog", "social_media"],
        "depth": "shallow",
        "citations": 2,
        "technical_accuracy": 0.7,
        "timestamp": time.time() - 15552000  # 6 months old
    }
}

@pytest.fixture
def source_validator():
    """Create SourceValidator instance with test configuration."""
    config = SourceValidationConfig(
        min_trust_score=0.8,
        min_reliability_score=0.8,
        min_authority_score=0.7,
        min_freshness_score=0.7,
        required_citations=2,
        max_validation_time_ms=100,
        complete_timeout_ms=5000,
        max_memory_mb=10,
        max_chunk_size_kb=16,
        requests_per_second=20,
        connection_timeout_sec=30,
        max_results=20,
        enable_streaming=True,
        enable_memory_tracking=True,
        enable_performance_tracking=True
    )
    return SourceValidator(config)

async def create_content_stream(content_items: List[Dict[str, Any]]) -> AsyncIterator[Dict[str, Any]]:
    """Create an async iterator from content items."""
    for item in content_items:
        yield item
        await asyncio.sleep(0.1)  # Simulate processing time

@pytest.mark.asyncio
async def test_source_validation_streaming(source_validator):
    """Test streaming source validation functionality."""
    content_items = list(TEST_CONTENT.values())
    content_stream = create_content_stream(content_items)
    
    results = []
    start_time = time.time()
    
    async for result in source_validator.validate_stream(content_stream):
        assert isinstance(result, ValidationResult)
        results.append(result)
        
        # Verify timing requirements
        assert time.time() - start_time < 1.0  # First result within 1s
        
    assert len(results) == len(content_items)
    assert any(r.trust_score > 0.8 for r in results)
    assert source_validator.resource_manager.current_memory_mb < 10
    
    # Verify state tracking
    assert source_validator.validation_state.processed_count == len(content_items)
    assert source_validator.validation_state.error_count == 0
    assert source_validator.validation_state.get_error_rate() == 0
    assert len(source_validator.validation_state.successful_items) == len(content_items)

@pytest.mark.asyncio
async def test_source_validation_performance(source_validator):
    """Test source validation performance metrics."""
    content_items = TEST_DATA["validation_tests"]
    content_stream = create_content_stream(content_items)
    
    start_time = time.time()
    results = []
    throughput_measurements = []
    last_check = start_time
    item_count = 0
    
    async for result in source_validator.validate_stream(content_stream):
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
    assert source_validator.resource_manager.peak_memory < 10 * 1024 * 1024  # Under 10MB
    assert len(results) == len(content_items)
    
    # Verify throughput
    if throughput_measurements:
        avg_throughput = sum(throughput_measurements) / len(throughput_measurements)
        assert avg_throughput >= 2.0  # At least 2 items per second
        
    # Verify resource monitoring
    assert source_validator.resource_manager.peak_memory > 0
    assert source_validator.resource_manager.current_memory_mb < source_validator.resource_manager.peak_memory

@pytest.mark.asyncio
async def test_source_validation_error_recovery(source_validator):
    """Test error recovery during streaming."""
    # Create stream with various error scenarios
    content_items = [
        TEST_CONTENT["high_authority"],
        {},  # Invalid item
        TEST_CONTENT["medium_authority"],
        {"text": "Invalid", "sources": []},  # Another invalid item
        TEST_CONTENT["low_authority"]
    ]
    content_stream = create_content_stream(content_items)
    
    results = []
    async for result in source_validator.validate_stream(content_stream):
        results.append(result)
    
    # Verify error handling and recovery
    assert len(results) == 3  # Should process valid items only
    assert all(isinstance(r, ValidationResult) for r in results)
    assert source_validator.validation_state.error_count == 2
    assert source_validator.validation_state.get_error_rate() == 0.4  # 2 errors out of 5 items
    
    # Verify state recovery
    assert len(source_validator.validation_state.successful_items) == 3
    assert all(item in source_validator.validation_state.successful_items 
              for item in [TEST_CONTENT["high_authority"], 
                         TEST_CONTENT["medium_authority"],
                         TEST_CONTENT["low_authority"]])
    
    # Verify cleanup after errors
    assert not source_validator.validation_state.current_batch  # Batch should be cleared
    assert source_validator.resource_manager.current_memory_mb < 1  # Memory should be cleaned up

@pytest.mark.asyncio
async def test_source_validation_high_authority(source_validator):
    """Test source validation for high authority content."""
    result = await source_validator.validate(TEST_CONTENT["high_authority"])
    assert isinstance(result, ValidationResult)
    assert result.trust_score > 0.8
    assert result.reliability_score > 0.8
    assert result.authority_score > 0.7
    assert result.freshness_score > 0.7
    assert result.is_valid

@pytest.mark.asyncio
async def test_source_validation_medium_authority(source_validator):
    """Test source validation for medium authority content."""
    result = await source_validator.validate(TEST_CONTENT["medium_authority"])
    assert isinstance(result, ValidationResult)
    assert result.trust_score <= 0.8
    assert result.reliability_score <= 0.8
    assert result.authority_score <= 0.7
    assert result.freshness_score > 0.7  # Still fresh (1 month old)
    assert not result.is_valid  # Below minimum thresholds

@pytest.mark.asyncio
async def test_source_validation_low_authority(source_validator):
    """Test source validation for low authority content."""
    result = await source_validator.validate(TEST_CONTENT["low_authority"])
    assert isinstance(result, ValidationResult)
    assert result.trust_score < 0.6
    assert result.reliability_score < 0.6
    assert result.authority_score < 0.6
    assert result.freshness_score < 0.7  # Not fresh (6 months old)
    assert not result.is_valid

@pytest.mark.asyncio
async def test_source_validation_resource_management(source_validator):
    """Test resource management during source validation."""
    async with source_validator.resource_manager:
        result = await source_validator.validate(TEST_CONTENT["high_authority"])
        assert result.is_valid
        assert source_validator.resource_manager.current_memory_mb < 10

@pytest.mark.asyncio
async def test_source_validation_batch_processing(source_validator):
    """Test batch processing efficiency."""
    results = []
    async with source_validator.resource_manager:
        for content in TEST_CONTENT.values():
            result = await source_validator.validate(content)
            results.append(result)
    
    assert len(results) == 3
    assert all(isinstance(r, ValidationResult) for r in results)
    assert any(r.is_valid for r in results)

@pytest.mark.asyncio
async def test_source_validation_error_handling(source_validator):
    """Test error handling for invalid inputs."""
    with pytest.raises(ValueError):
        await source_validator.validate({})

    with pytest.raises(ValueError):
        await source_validator.validate(None)

    with pytest.raises(ValueError):
        await source_validator.validate({"text": ""})

@pytest.mark.asyncio
async def test_source_validation_resource_cleanup(source_validator):
    """Test resource cleanup and memory management."""
    # Create large batch of items
    content_items = [TEST_CONTENT["high_authority"]] * 50  # 50 items
    content_stream = create_content_stream(content_items)
    
    results = []
    peak_memory = 0
    cleanup_count = 0
    
    async for result in source_validator.validate_stream(content_stream):
        results.append(result)
        current_memory = source_validator.resource_manager.current_memory_mb
        peak_memory = max(peak_memory, current_memory)
        
        if source_validator.validation_state.should_trigger_cleanup():
            cleanup_count += 1
    
    # Verify memory management
    assert peak_memory < 10  # Peak memory under limit
    assert cleanup_count > 0  # Cleanup was triggered
    assert len(results) == 50  # All items processed
    assert source_validator.resource_manager.current_memory_mb < 1  # Memory cleaned up
    assert source_validator.validation_state.processed_count == 50
    assert source_validator.validation_state.error_count == 0

@pytest.mark.asyncio
async def test_source_validation_throughput_monitoring(source_validator):
    """Test throughput monitoring and performance tracking."""
    # Create stream of items
    content_items = [TEST_CONTENT["high_authority"]] * 20  # 20 items
    content_stream = create_content_stream(content_items)
    
    start_time = time.time()
    results = []
    
    async for result in source_validator.validate_stream(content_stream):
        results.append(result)
    
    total_time = time.time() - start_time
    throughput = len(results) / total_time
    
    # Verify throughput requirements
    assert throughput >= 2.0  # At least 2 items per second
    assert source_validator.throughput_counter >= 0
    assert source_validator.last_throughput_check > start_time
    
    # Verify monitoring
    assert source_validator.resource_manager.peak_memory > 0
    assert source_validator.resource_manager.last_cleanup > start_time
    assert source_validator.validation_state.processed_count == 20