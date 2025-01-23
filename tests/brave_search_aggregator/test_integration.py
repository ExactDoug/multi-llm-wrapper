"""Integration tests for Brave Search Knowledge Aggregator components."""
import pytest
from src.brave_search_aggregator.synthesizer.knowledge_synthesizer import (
    KnowledgeSynthesizer,
    SynthesisMode,
    SynthesisResult
)
from src.brave_search_aggregator.synthesizer.knowledge_aggregator import (
    KnowledgeAggregator,
    AggregationResult
)

@pytest.fixture
def synthesizer():
    """Fixture providing a KnowledgeSynthesizer instance."""
    return KnowledgeSynthesizer()

@pytest.fixture
def aggregator():
    """Fixture providing a KnowledgeAggregator instance."""
    return KnowledgeAggregator()

@pytest.mark.integration
async def test_synthesis_architecture(synthesizer):
    """Test synthesis architecture components."""
    # Test MoE routing
    route = await synthesizer.route_query(
        query="test query",
        synthesis_mode="research"
    )
    assert route.selected_models
    assert route.routing_confidence > 0.8
    
    # Create test responses
    response1 = {
        "model": "perplexity",
        "content": "Test response 1",
        "confidence": 0.9
    }
    response2 = {
        "model": "brave_search",
        "content": "Test response 2",
        "confidence": 0.85
    }
    
    # Test vector operations
    result = await synthesizer.combine_knowledge(
        responses=[response1, response2],
        operation="task_vector_merge"
    )
    assert result["coherence_score"] > 0.7
    
    # Test SLERP merging
    merged = await synthesizer.merge_responses(
        responses=[response1, response2],
        interpolation_factor=0.5
    )
    assert merged["consistency_score"] > 0.8

@pytest.mark.integration
async def test_parallel_processing(aggregator):
    """Test parallel knowledge aggregation."""
    results = await aggregator.process_parallel(
        query="test query",
        sources=["brave_search", "llm1", "llm2"],
        preserve_nuances=True
    )
    
    assert results.all_sources_processed
    assert results.conflicts_resolved
    assert results.nuances_preserved

@pytest.mark.integration
async def test_end_to_end_flow(synthesizer, aggregator):
    """Test complete knowledge processing flow."""
    # First, aggregate knowledge from sources
    aggregation_results = await aggregator.process_parallel(
        query="What is quantum computing?",
        sources=["brave_search", "llm1", "llm2"],
        preserve_nuances=True
    )
    
    # Convert aggregation results to synthesis input format
    synthesis_inputs = [
        {
            "model": source,
            "content": content,
            "confidence": metrics["confidence"]
        }
        for source, content, metrics in zip(
            aggregation_results.source_metrics.keys(),
            aggregation_results.content.split("\n\n"),
            aggregation_results.source_metrics.values()
        )
    ]
    
    # Synthesize the aggregated knowledge
    synthesis_results = await synthesizer.synthesize(
        query="What is quantum computing?",
        responses=synthesis_inputs,
        synthesis_mode="research"
    )
    
    # Verify end-to-end results
    assert isinstance(synthesis_results, SynthesisResult)
    assert synthesis_results.content
    assert synthesis_results.confidence_score > 0.7
    assert synthesis_results.coherence_score > 0.7
    assert synthesis_results.consistency_score > 0.7
    assert len(synthesis_results.sources) > 0
    assert synthesis_results.mode == SynthesisMode.RESEARCH

@pytest.mark.integration
async def test_error_handling(synthesizer, aggregator):
    """Test error handling in integrated flow."""
    # Test with invalid source
    aggregation_results = await aggregator.process_parallel(
        query="test query",
        sources=["invalid_source", "llm1"],
        preserve_nuances=True
    )
    assert not aggregation_results.all_sources_processed
    
    # Test with invalid synthesis mode
    synthesis_results = await synthesizer.synthesize(
        query="test query",
        responses=[{"model": "test", "content": "test"}],
        synthesis_mode="invalid_mode"
    )
    assert synthesis_results.mode == SynthesisMode.RESEARCH  # Should default to research

@pytest.mark.integration
async def test_compatibility_layer(synthesizer, aggregator):
    """Test compatibility between aggregator and synthesizer."""
    # Get aggregation results
    agg_results = await aggregator.process_parallel(
        query="test compatibility",
        sources=["brave_search", "llm1"],
        preserve_nuances=True
    )
    
    # Verify aggregation results can be used for synthesis
    assert isinstance(agg_results, AggregationResult)
    assert agg_results.content
    assert agg_results.source_metrics
    
    # Convert to synthesis format
    synthesis_inputs = [
        {
            "model": source,
            "content": content,
            "confidence": metrics["confidence"]
        }
        for source, content, metrics in zip(
            agg_results.source_metrics.keys(),
            agg_results.content.split("\n\n"),
            agg_results.source_metrics.values()
        )
    ]
    
    # Verify synthesis accepts aggregation output
    synth_results = await synthesizer.synthesize(
        query="test compatibility",
        responses=synthesis_inputs,
        synthesis_mode="research"
    )
    assert isinstance(synth_results, SynthesisResult)
    assert synth_results.content
    assert synth_results.sources