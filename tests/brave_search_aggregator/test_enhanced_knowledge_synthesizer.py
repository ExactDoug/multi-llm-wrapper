"""
Tests for the EnhancedKnowledgeSynthesizer component of the Brave Search Knowledge Aggregator.
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any
from dataclasses import dataclass, field

from brave_search_aggregator.synthesizer.enhanced_knowledge_synthesizer import (
    EnhancedKnowledgeSynthesizer, SynthesisResult, SynthesisError
)
from brave_search_aggregator.synthesizer.content_analyzer import AnalysisResult
from brave_search_aggregator.utils.config import Config, AnalyzerConfig


@pytest.fixture
def config():
    """Provide a Config object for testing."""
    config = Config()
    config.analyzer = AnalyzerConfig()
    return config


@pytest.fixture
def mock_analysis_results():
    """Provide mock analysis results for testing."""
    return [
        AnalysisResult(
            source_url="https://example.com/article1",
            quality_score=0.85,
            relevance_score=0.9,
            key_points=[
                "Python is a versatile programming language.",
                "Python is widely used in data science and machine learning.",
                "Python has a simple and readable syntax."
            ],
            entities=["Python", "Data Science", "Machine Learning"],
            sentiment="positive",
            category="technical",
            tags=["programming", "technical", "python"],
            summary="Python is a versatile programming language widely used in data science and machine learning.",
            processing_time_ms=150,
            content_type="text/html",
            word_count=120,
            is_reliable=True,
            processing_metadata={
                "timestamp": time.time()
            }
        ),
        AnalysisResult(
            source_url="https://example.org/python-article",
            quality_score=0.75,
            relevance_score=0.8,
            key_points=[
                "Python was created by Guido van Rossum in 1991.",
                "Python supports multiple programming paradigms.",
                "Python has a large standard library."
            ],
            entities=["Python", "Guido van Rossum", "Standard Library"],
            sentiment="neutral",
            category="educational",
            tags=["programming", "history", "python"],
            summary="Python was created by Guido van Rossum in 1991 and supports multiple programming paradigms.",
            processing_time_ms=130,
            content_type="text/html",
            word_count=150,
            is_reliable=True,
            processing_metadata={
                "timestamp": time.time()
            }
        ),
        AnalysisResult(
            source_url="https://blog.example.net/python-criticism",
            quality_score=0.65,
            relevance_score=0.7,
            key_points=[
                "Python can be slower than compiled languages.",
                "Python's Global Interpreter Lock (GIL) limits concurrency.",
                "Python requires careful memory management for large applications."
            ],
            entities=["Python", "GIL", "Memory Management"],
            sentiment="negative",
            category="technical",
            tags=["programming", "performance", "python"],
            summary="Python has some performance limitations including the GIL and slower execution compared to compiled languages.",
            processing_time_ms=120,
            content_type="text/html",
            word_count=180,
            is_reliable=True,
            processing_metadata={
                "timestamp": time.time()
            }
        )
    ]


@pytest.fixture
def synthesizer(config):
    """Provide an EnhancedKnowledgeSynthesizer instance for testing."""
    return EnhancedKnowledgeSynthesizer(config)


@pytest.mark.asyncio
async def test_basic_synthesis(synthesizer, mock_analysis_results):
    """Test basic knowledge synthesis functionality."""
    # Perform synthesis
    result = await synthesizer.synthesize(mock_analysis_results)
    
    # Verify result is a SynthesisResult
    assert isinstance(result, SynthesisResult)
    
    # Verify basic fields
    assert isinstance(result.content, str)
    assert len(result.sources) == 3
    assert len(result.key_insights) > 0
    assert len(result.source_quality) == 3
    assert len(result.entity_map) > 0
    assert result.synthesis_time_ms > 0
    assert 0 <= result.confidence_score <= 1
    
    # Verify content includes key information from sources
    assert "Python" in result.content
    
    # Verify source URLs are included
    for mock_result in mock_analysis_results:
        assert mock_result.source_url in result.sources
    
    # Verify source quality mapping
    for mock_result in mock_analysis_results:
        assert mock_result.source_url in result.source_quality
        assert result.source_quality[mock_result.source_url] == mock_result.quality_score
    
    # Verify entity map contains key entities
    assert "Python" in result.entity_map
    
    # Verify processing metadata
    assert "timestamp" in result.processing_metadata
    assert "synthesizer_version" in result.processing_metadata
    assert "num_sources" in result.processing_metadata
    assert result.processing_metadata["num_sources"] == 3


@pytest.mark.asyncio
async def test_synthesis_with_query(synthesizer, mock_analysis_results):
    """Test knowledge synthesis with a specific query."""
    # Query related to Python
    query = "Python programming language"
    
    # Perform synthesis with query
    result = await synthesizer.synthesize(mock_analysis_results, query)
    
    # Verify query is referenced in the content
    assert "Python programming language" in result.content
    
    # Verify query is in processing metadata
    assert "query" in result.processing_metadata
    assert result.processing_metadata["query"] == query
    
    # Try with a more specific query
    specific_query = "Python performance issues"
    specific_result = await synthesizer.synthesize(mock_analysis_results, specific_query)
    
    # Verify specific query is referenced
    assert "Python performance issues" in specific_result.content
    
    # Content should focus more on performance aspects from the negative source
    assert "slower" in specific_result.content or "GIL" in specific_result.content


@pytest.mark.asyncio
async def test_key_insights_extraction(synthesizer, mock_analysis_results):
    """Test key insights extraction functionality."""
    # Perform synthesis
    result = await synthesizer.synthesize(mock_analysis_results)
    
    # Verify key insights
    assert len(result.key_insights) > 0
    
    # Key insights should contain important points from source analyses
    key_insights_text = " ".join(result.key_insights).lower()
    
    # Should include points from different sentiments and categories
    important_topics = ["versatile", "created", "paradigms", "slower", "gil"]
    
    # At least 3 of the important topics should be in the key insights
    matches = sum(1 for topic in important_topics if topic in key_insights_text)
    assert matches >= 3
    
    # Verify content sections
    assert "Key Insights" in result.content


@pytest.mark.asyncio
async def test_entity_mapping(synthesizer, mock_analysis_results):
    """Test entity mapping functionality."""
    # Perform synthesis
    result = await synthesizer.synthesize(mock_analysis_results)
    
    # Verify entity map
    assert len(result.entity_map) > 0
    
    # Common entities should map to multiple sources
    assert "Python" in result.entity_map
    assert len(result.entity_map["Python"]) == 3  # From all three sources
    
    # Specific entities should map to their respective sources
    entity_map = result.entity_map
    
    # Check specific entity mappings
    if "Guido van Rossum" in entity_map:
        assert "https://example.org/python-article" in entity_map["Guido van Rossum"]
    
    if "GIL" in entity_map:
        assert "https://blog.example.net/python-criticism" in entity_map["GIL"]


@pytest.mark.asyncio
async def test_sentiment_based_sections(synthesizer, mock_analysis_results):
    """Test sentiment-based sections in synthesis."""
    # Perform synthesis
    result = await synthesizer.synthesize(mock_analysis_results)
    
    # Verify sentiment-based sections
    content = result.content
    
    # Should have positive perspectives section
    assert "Positive Perspectives" in content
    
    # Should include positive content
    assert "versatile" in content
    
    # Should have challenges section
    assert "Challenges" in content or "Concerns" in content
    
    # Should include negative content
    assert "slower" in content or "GIL" in content


@pytest.mark.asyncio
async def test_technical_section(synthesizer, mock_analysis_results):
    """Test technical section in synthesis for technical content."""
    # Perform synthesis
    result = await synthesizer.synthesize(mock_analysis_results)
    
    # Verify technical section presence (since mock data has technical category)
    content = result.content
    
    # Should have technical details section
    assert "Technical Details" in content or "Technical Information" in content


@pytest.mark.asyncio
async def test_confidence_calculation(synthesizer, mock_analysis_results):
    """Test confidence score calculation."""
    # Perform synthesis with high-quality sources
    high_quality_result = await synthesizer.synthesize(mock_analysis_results)
    
    # Confidence should be fairly high (3 sources, good quality, 2/3 reliable)
    assert high_quality_result.confidence_score > 0.7
    
    # Create lower quality sources
    low_quality_analyses = [
        AnalysisResult(
            source_url="https://randomsite.com/article",
            quality_score=0.4,
            relevance_score=0.5,
            key_points=["Python is a language.", "Python has functions."],
            entities=["Python"],
            sentiment="neutral",
            category="general",
            tags=["python"],
            summary="Python is a programming language.",
            processing_time_ms=100,
            content_type="text/html",
            word_count=50,
            is_reliable=False,
            processing_metadata={"timestamp": time.time()}
        )
    ]
    
    # Perform synthesis with low-quality source
    low_quality_result = await synthesizer.synthesize(low_quality_analyses)
    
    # Confidence should be lower (1 source, lower quality, not reliable)
    assert low_quality_result.confidence_score < 0.5


@pytest.mark.asyncio
async def test_mixed_categories_synthesis(synthesizer):
    """Test synthesis with mixed category sources."""
    # Create analysis results with different categories
    mixed_analyses = [
        AnalysisResult(
            source_url="https://tech.example.com/python",
            quality_score=0.8,
            relevance_score=0.9,
            key_points=["Python is used for web development.", "Django is a Python framework."],
            entities=["Python", "Django", "Web Development"],
            sentiment="positive",
            category="technical",
            tags=["programming", "web", "python"],
            summary="Python is widely used for web development, with frameworks like Django.",
            processing_time_ms=130,
            content_type="text/html",
            word_count=120,
            is_reliable=True,
            processing_metadata={"timestamp": time.time()}
        ),
        AnalysisResult(
            source_url="https://news.example.com/python-release",
            quality_score=0.7,
            relevance_score=0.8,
            key_points=["Python 3.10 was released recently.", "New features include pattern matching."],
            entities=["Python 3.10", "Pattern Matching"],
            sentiment="neutral",
            category="news",
            tags=["news", "release", "python"],
            summary="Python 3.10 has been released with new features like pattern matching.",
            processing_time_ms=110,
            content_type="text/html",
            word_count=150,
            is_reliable=True,
            processing_metadata={"timestamp": time.time()}
        ),
        AnalysisResult(
            source_url="https://blog.example.com/python-opinion",
            quality_score=0.6,
            relevance_score=0.7,
            key_points=["Python is great for beginners.", "I think Python will continue to grow in popularity."],
            entities=["Python"],
            sentiment="positive",
            category="opinion",
            tags=["opinion", "python"],
            summary="In my opinion, Python is an excellent language for beginners and will continue to grow in popularity.",
            processing_time_ms=100,
            content_type="text/html",
            word_count=180,
            is_reliable=False,
            processing_metadata={"timestamp": time.time()}
        )
    ]
    
    # Perform synthesis
    result = await synthesizer.synthesize(mixed_analyses)
    
    # Verify result includes different categories of information
    content = result.content
    
    # Should include technical information
    assert "Django" in content or "web development" in content
    
    # Should include news information
    assert "3.10" in content or "release" in content
    
    # Should include opinion information
    assert "beginners" in content or "grow" in content
    
    # Should have appropriate structure despite mixed categories
    assert "Based on information from 3 sources" in content
    assert "Sources" in content


@pytest.mark.asyncio
async def test_error_handling(synthesizer):
    """Test error handling during synthesis."""
    # 1. Empty analyses list
    with pytest.raises(SynthesisError) as excinfo:
        await synthesizer.synthesize([])
    assert "No content analyses to synthesize" in str(excinfo.value)
    
    # 2. Test error recovery with partial results
    # Mock ErrorHandler.handle_error to return a recovery result
    error_handler = synthesizer.error_handler
    original_handle_error = error_handler.handle_error
    
    async def mock_handle_error(error, context):
        # Return recovery result
        return SynthesisResult(
            content="Recovery content",
            sources=["recovery-source"],
            key_insights=["recovery insight"],
            source_quality={"recovery-source": 0.5},
            entity_map={"Recovery Entity": ["recovery-source"]},
            synthesis_time_ms=0,
            confidence_score=0.1,
            processing_metadata={"recovered": True}
        )
    
    error_handler.handle_error = mock_handle_error
    
    # Create a scenario that would normally fail
    with patch.object(synthesizer, '_extract_key_insights', side_effect=ValueError("Test error")):
        # Should use error handler and return recovery result
        result = await synthesizer.synthesize([
            AnalysisResult(
                source_url="https://example.com/error-test",
                quality_score=0.7,
                relevance_score=0.7,
                key_points=["Test point"],
                entities=["Test"],
                sentiment="neutral",
                category="general",
                tags=["test"],
                summary="Test summary",
                processing_time_ms=100,
                content_type="text/html",
                word_count=100,
                is_reliable=True,
                processing_metadata={"timestamp": time.time()}
            )
        ])
        
        # Should have recovery content
        assert result.content == "Recovery content"
        assert "recovered" in result.processing_metadata
    
    # Restore original method
    error_handler.handle_error = original_handle_error


@pytest.mark.asyncio
async def test_point_relevance_calculation(synthesizer):
    """Test point relevance calculation functionality."""
    # Direct test of _calculate_point_relevance method
    # 1. Exact match
    relevance = synthesizer._calculate_point_relevance(
        "Python is a programming language with many uses.",
        "Python programming language"
    )
    assert relevance == 1.0  # Exact match should be highest relevance
    
    # 2. High match (many matching terms)
    relevance = synthesizer._calculate_point_relevance(
        "Python developers use many programming tools and languages.",
        "Python programming language"
    )
    assert relevance >= 0.7  # High but not exact match
    
    # 3. Medium match (some matching terms)
    relevance = synthesizer._calculate_point_relevance(
        "Programming requires understanding of algorithms and data structures.",
        "Python programming language"
    )
    assert 0.3 <= relevance < 0.7  # Medium match
    
    # 4. Low match (few matching terms)
    relevance = synthesizer._calculate_point_relevance(
        "Software engineering involves many disciplines.",
        "Python programming language"
    )
    assert 0.0 < relevance < 0.3  # Low match
    
    # 5. No match
    relevance = synthesizer._calculate_point_relevance(
        "Quantum physics studies the behavior of matter and energy at small scales.",
        "Python programming language"
    )
    assert relevance < 0.2  # Very low or no match
    
    # 6. No query
    relevance = synthesizer._calculate_point_relevance(
        "Any content here doesn't matter.",
        None
    )
    assert relevance == 1.0  # No query means everything is relevant
