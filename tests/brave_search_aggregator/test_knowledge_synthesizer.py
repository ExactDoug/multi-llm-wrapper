"""Tests for knowledge synthesizer component."""
import pytest
from src.brave_search_aggregator.synthesizer.knowledge_synthesizer import (
    KnowledgeSynthesizer,
    SynthesisMode,
    ModelRoute,
    SynthesisResult
)

@pytest.fixture
def synthesizer():
    """Fixture providing a KnowledgeSynthesizer instance."""
    return KnowledgeSynthesizer()

@pytest.fixture
def sample_responses():
    """Fixture providing sample model responses."""
    return [
        {
            "model": "perplexity",
            "content": "Sample perplexity response",
            "confidence": 0.9
        },
        {
            "model": "brave_search",
            "content": "Sample brave search response",
            "confidence": 0.8
        },
        {
            "model": "gemini",
            "content": "Sample gemini response",
            "confidence": 0.85
        }
    ]

@pytest.mark.asyncio
async def test_route_query(synthesizer):
    """Test query routing functionality."""
    # Test research mode routing
    route = await synthesizer.route_query(
        "What is quantum computing?",
        "research"
    )
    assert isinstance(route, ModelRoute)
    assert len(route.selected_models) > 0
    assert route.routing_confidence > 0.6
    assert route.synthesis_mode == SynthesisMode.RESEARCH
    
    # Test coding mode routing
    route = await synthesizer.route_query(
        "How to implement quicksort in Python?",
        "coding"
    )
    assert isinstance(route, ModelRoute)
    assert "chatgpt" in route.selected_models
    assert route.routing_confidence > 0.6
    assert route.synthesis_mode == SynthesisMode.CODING

@pytest.mark.asyncio
async def test_combine_knowledge(synthesizer, sample_responses):
    """Test knowledge combination functionality."""
    result = await synthesizer.combine_knowledge(sample_responses)
    assert isinstance(result, dict)
    assert "content" in result
    assert "coherence_score" in result
    assert result["coherence_score"] > 0
    assert all(resp["content"] in result["content"] 
              for resp in sample_responses)

@pytest.mark.asyncio
async def test_merge_responses(synthesizer, sample_responses):
    """Test response merging functionality."""
    result = await synthesizer.merge_responses(sample_responses)
    assert isinstance(result, dict)
    assert "content" in result
    assert "consistency_score" in result
    assert result["consistency_score"] > 0
    assert all(resp["content"] in result["content"] 
              for resp in sample_responses)

@pytest.mark.asyncio
async def test_synthesize(synthesizer, sample_responses):
    """Test end-to-end synthesis functionality."""
    result = await synthesizer.synthesize(
        "What is quantum computing?",
        sample_responses,
        "research"
    )
    assert isinstance(result, SynthesisResult)
    assert result.content
    assert result.confidence_score > 0
    assert len(result.sources) > 0
    assert result.mode == SynthesisMode.RESEARCH
    assert result.coherence_score is not None
    assert result.consistency_score is not None

@pytest.mark.asyncio
async def test_invalid_synthesis_mode(synthesizer, sample_responses):
    """Test handling of invalid synthesis mode."""
    # Should default to research mode
    result = await synthesizer.synthesize(
        "What is quantum computing?",
        sample_responses,
        "invalid_mode"
    )
    assert isinstance(result, SynthesisResult)
    assert result.mode == SynthesisMode.RESEARCH

@pytest.mark.asyncio
async def test_empty_responses(synthesizer):
    """Test handling of empty responses."""
    result = await synthesizer.synthesize(
        "What is quantum computing?",
        [],
        "research"
    )
    assert isinstance(result, SynthesisResult)
    assert result.content == ""
    assert len(result.sources) == 0

@pytest.mark.asyncio
async def test_synthesis_modes(synthesizer, sample_responses):
    """Test different synthesis modes."""
    modes = ["research", "coding", "analysis", "creative"]
    
    for mode in modes:
        result = await synthesizer.synthesize(
            "Test query",
            sample_responses,
            mode
        )
        assert isinstance(result, SynthesisResult)
        assert result.mode == SynthesisMode(mode)
        assert result.confidence_score > 0