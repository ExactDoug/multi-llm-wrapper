"""
Tests for the ContentAnalyzer component of the Brave Search Knowledge Aggregator.
"""
import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from brave_search_aggregator.synthesizer.content_analyzer import (
    ContentAnalyzer, ContentAnalysisError, AnalysisResult
)
from brave_search_aggregator.utils.config import Config, AnalyzerConfig


@pytest.fixture
def analyzer_config():
    """Provide a basic AnalyzerConfig for testing."""
    return AnalyzerConfig(
        min_complexity_score=0.7,
        min_confidence_score=0.6,
        input_type_confidence_threshold=0.8,
        enable_segmentation=True,
        max_segments=5,
        max_memory_mb=10,
        enable_streaming=True,
        batch_size=3
    )


@pytest.fixture
def config(analyzer_config):
    """Provide a Config object with the test AnalyzerConfig."""
    config = Config()
    config.analyzer = analyzer_config
    return config


@pytest.fixture
def content_analyzer(config):
    """Provide a ContentAnalyzer instance for testing."""
    return ContentAnalyzer(config)


@pytest.mark.asyncio
async def test_analyze_basic_content(content_analyzer):
    """Test basic content analysis with simple content."""
    # Create basic content
    content = {
        "url": "https://example.com/test",
        "content": "This is a test article about Python programming. Python is a high-level programming language.",
        "content_type": "text/plain",
        "fetch_time_ms": 100,
        "timestamp": time.time()
    }
    
    # Analyze content
    result = await content_analyzer.analyze(content)
    
    # Verify result is an AnalysisResult
    assert isinstance(result, AnalysisResult)
    
    # Verify basic fields
    assert result.source_url == content["url"]
    assert result.content_type == content["content_type"]
    assert result.word_count > 0
    assert 0 <= result.quality_score <= 1
    assert 0 <= result.relevance_score <= 1
    
    # Verify entities, should include "Python"
    assert "Python" in result.entities
    
    # Verify category, should be "technical"
    assert result.category == "technical"
    
    # Verify tags include "programming"
    assert "programming" in result.tags or "technical" in result.tags
    
    # Verify processing time is reasonable
    assert result.processing_time_ms > 0
    
    # Verify metadata
    assert "timestamp" in result.processing_metadata
    assert "analyzer_version" in result.processing_metadata
    assert "analyzer_config" in result.processing_metadata


@pytest.mark.asyncio
async def test_analyze_complex_content(content_analyzer):
    """Test analysis of more complex content with multiple topics and structures."""
    # Create complex content with multiple paragraphs, entities, and topics
    content = {
        "url": "https://example.com/article",
        "content": """
        # The Impact of Machine Learning on Modern Software Development
        
        Machine learning has significantly transformed how we approach software development in the 21st century.
        
        ## Key Technologies
        
        Python has become the dominant language for ML development, with frameworks like TensorFlow and PyTorch leading the way.
        
        ## Industry Applications
        
        Companies like Google, Microsoft, and Amazon have heavily invested in ML technologies.
        
        ## Future Trends
        
        The integration of ML with edge computing is expected to grow significantly in the coming years.
        
        ## Challenges
        
        However, there are concerns about bias in ML algorithms and the ethical implications of automated decision-making.
        """,
        "content_type": "text/markdown",
        "fetch_time_ms": 150,
        "timestamp": time.time()
    }
    
    # Analyze content
    result = await content_analyzer.analyze(content)
    
    # Verify key points extraction (should have multiple points)
    assert len(result.key_points) > 1
    
    # Verify entities extraction (should find multiple technical terms and companies)
    assert any(entity in result.entities for entity in ["Python", "TensorFlow", "PyTorch", "Google", "Microsoft", "Amazon"])
    
    # Verify sentiment analysis (likely mixed or neutral for technical content)
    assert result.sentiment in ["positive", "negative", "neutral", "mixed"]
    
    # Verify category (should be technical or educational)
    assert result.category in ["technical", "educational"]
    
    # Verify tags (should include ML-related terms)
    assert any(tag in result.tags for tag in ["technical", "machine learning", "programming", "ml", "technology", "software"])
    
    # Verify summary is generated and not empty
    assert result.summary
    assert len(result.summary) > 50  # Reasonable summary length
    
    # Verify reasonable quality score for well-structured content
    assert result.quality_score > 0.6


@pytest.mark.asyncio
async def test_analyze_with_query(content_analyzer):
    """Test content analysis with a specific query for relevance scoring."""
    # Create content
    content = {
        "url": "https://example.com/python-guide",
        "content": """
        Python Programming Guide
        
        Python is a versatile programming language used in web development, data science, and AI.
        
        Getting Started
        
        To begin with Python, first install the latest version from python.org.
        Next, set up your IDE. Popular choices include PyCharm, VSCode, and Jupyter Notebook.
        
        Basic Syntax
        
        Python uses indentation to define code blocks. This makes code more readable.
        Variables in Python are dynamically typed, meaning you don't need to declare types.
        """,
        "content_type": "text/plain",
        "fetch_time_ms": 120,
        "timestamp": time.time()
    }
    
    # Query related to Python programming
    query = "Python beginner guide"
    
    # Analyze content with query
    result = await content_analyzer.analyze(content, query)
    
    # Verify high relevance score for matching query
    assert result.relevance_score > 0.7
    
    # Verify key points include relevant terms from query
    assert any("Python" in point for point in result.key_points)
    assert any("guide" in point.lower() or "beginner" in point.lower() or "getting started" in point.lower() for point in result.key_points)
    
    # Verify summary includes query-relevant content
    assert "Python" in result.summary
    
    # Try with unrelated query
    unrelated_query = "JavaScript frameworks React Angular"
    unrelated_result = await content_analyzer.analyze(content, unrelated_query)
    
    # Verify lower relevance score for unmatching query
    assert unrelated_result.relevance_score < result.relevance_score


@pytest.mark.asyncio
async def test_key_points_extraction(content_analyzer):
    """Test key points extraction functionality."""
    # Content with clear key points indicated by markers
    content = {
        "url": "https://example.com/key-points",
        "content": """
        Important points about software testing:
        
        The key to effective testing is test coverage. Good tests should cover all critical paths.
        
        Essential for any testing strategy is automation. Automated tests save time and reduce human error.
        
        Critical aspect of testing is consistency. Tests should be reliable and produce the same results each time.
        
        Significantly, testing should start early in the development cycle. Early testing catches issues before they become costly.
        
        It's important to note that tests should be maintained alongside code. Outdated tests can give false confidence.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    # Analyze content
    result = await content_analyzer.analyze(content)
    
    # Verify key points extraction
    assert len(result.key_points) >= 3  # Should extract multiple key points
    
    # Key points should contain important markers from the content
    key_points_text = " ".join(result.key_points).lower()
    important_topics = ["test coverage", "automation", "consistency", "early", "maintained"]
    
    # At least 3 of the important topics should be in the key points
    matches = sum(1 for topic in important_topics if topic in key_points_text)
    assert matches >= 3


@pytest.mark.asyncio
async def test_entity_extraction(content_analyzer):
    """Test entity extraction functionality."""
    # Content with various entity types
    content = {
        "url": "https://example.com/entities",
        "content": """
        Microsoft Corporation announced a new partnership with OpenAI on January 15, 2023.
        
        The collaboration will focus on integrating GPT-4 technology into Microsoft's Azure platform.
        
        Satya Nadella, CEO of Microsoft, stated that this partnership will revolutionize cloud computing.
        
        The technology will be available in the United States and European Union starting in March 2023.
        
        For more information, contact press@microsoft.com or visit https://microsoft.com/ai-partnership.
        
        The project uses Python 3.9 and TensorFlow 2.5 for implementation.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    # Analyze content
    result = await content_analyzer.analyze(content)
    
    # Verify entity extraction
    entities = result.entities
    
    # Should find organization entities
    assert any("Microsoft" in entity for entity in entities)
    assert any("OpenAI" in entity for entity in entities)
    
    # Should find person entities
    assert any("Satya Nadella" in entity for entity in entities)
    
    # Should find location entities
    assert any("United States" in entity for entity in entities) or any("European Union" in entity for entity in entities)
    
    # Should find date entities
    assert any("January 15, 2023" in entity for entity in entities) or any("March 2023" in entity for entity in entities)
    
    # Should find email entities
    assert any("press@microsoft.com" in entity for entity in entities)
    
    # Should find URL entities
    assert any("https://microsoft.com/ai-partnership" in entity for entity in entities)
    
    # Should find version entities
    assert any("3.9" in entity for entity in entities) or any("2.5" in entity for entity in entities)
    
    # Should find technology entities
    assert any("Python" in entity for entity in entities)
    assert any("TensorFlow" in entity for entity in entities)


@pytest.mark.asyncio
async def test_sentiment_analysis(content_analyzer):
    """Test sentiment analysis functionality."""
    # 1. Positive content
    positive_content = {
        "url": "https://example.com/positive",
        "content": """
        We are extremely pleased with the excellent results of our latest product release.
        The customer feedback has been outstanding, with many reporting significant improvements in productivity.
        The new features have been praised for their intuitive design and impressive performance.
        Our team did an amazing job delivering this fantastic update ahead of schedule.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    positive_result = await content_analyzer.analyze(positive_content)
    assert positive_result.sentiment == "positive"
    
    # 2. Negative content
    negative_content = {
        "url": "https://example.com/negative",
        "content": """
        Unfortunately, the latest update has been disappointing for many users.
        There have been numerous complaints about poor performance and confusing interfaces.
        The bug count is frustratingly high, making the software difficult to use effectively.
        We regret the inadequate testing that led to these issues in the production release.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    negative_result = await content_analyzer.analyze(negative_content)
    assert negative_result.sentiment == "negative"
    
    # 3. Neutral content
    neutral_content = {
        "url": "https://example.com/neutral",
        "content": """
        The report contains the following data points about market performance:
        - Average growth rate: 2.3%
        - Total market size: $4.7 billion
        - Annual change: +0.5%
        - Number of new entrants: 12
        
        These figures represent the standard metrics used in quarterly analysis.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    neutral_result = await content_analyzer.analyze(neutral_content)
    assert neutral_result.sentiment == "neutral"
    
    # 4. Mixed content
    mixed_content = {
        "url": "https://example.com/mixed",
        "content": """
        While the new design has received excellent feedback for its visual appeal,
        there have been disappointing performance issues when running on older hardware.
        
        The positive user engagement metrics show a significant improvement,
        although the conversion rate has unfortunately decreased by 2.5%.
        
        We're pleased with the innovative features but concerned about the increased bug reports.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    mixed_result = await content_analyzer.analyze(mixed_content)
    assert mixed_result.sentiment == "mixed"


@pytest.mark.asyncio
async def test_categorization(content_analyzer):
    """Test content categorization functionality."""
    # Test different content categories
    
    # 1. Technical content
    technical_content = {
        "url": "https://example.com/technical",
        "content": """
        How to Implement a Binary Search Tree in Python
        
        A binary search tree (BST) is a data structure that allows for efficient insertion, deletion, and lookup operations.
        
        The code below demonstrates a simple BST implementation:
        
        ```python
        class Node:
            def __init__(self, value):
                self.value = value
                self.left = None
                self.right = None
        
        class BinarySearchTree:
            def __init__(self):
                self.root = None
                
            def insert(self, value):
                if not self.root:
                    self.root = Node(value)
                    return
                # More implementation details...
        ```
        """,
        "content_type": "text/markdown",
        "timestamp": time.time()
    }
    
    technical_result = await content_analyzer.analyze(technical_content)
    assert technical_result.category == "technical"
    
    # 2. Educational content
    educational_content = {
        "url": "https://example.com/educational",
        "content": """
        Learning Guide: Introduction to Photosynthesis
        
        Photosynthesis is the process used by plants to convert light energy into chemical energy.
        
        This tutorial will guide you through the key concepts of photosynthesis:
        
        1. Light-dependent reactions
        2. The Calvin cycle
        3. Factors affecting photosynthesis
        
        By the end of this guide, you'll understand how plants transform sunlight into energy.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    educational_result = await content_analyzer.analyze(educational_content)
    assert educational_result.category == "educational"
    
    # 3. News content
    news_content = {
        "url": "https://example.com/news",
        "content": """
        BREAKING NEWS: Major Technology Announcement
        
        San Francisco, CA - Today, a leading tech company unveiled their latest innovation in renewable energy technology.
        
        The announcement, made during their annual conference, reveals a breakthrough in solar panel efficiency that could revolutionize the industry.
        
        "This represents the biggest advance in solar technology in the last decade," said the company's CTO during today's press conference.
        
        Industry analysts predict this development will significantly impact the renewable energy market in the coming months.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    news_result = await content_analyzer.analyze(news_content)
    assert news_result.category == "news"
    
    # 4. Opinion content
    opinion_content = {
        "url": "https://example.com/opinion",
        "content": """
        Opinion: Why Remote Work Should Become the New Normal
        
        I believe that remote work represents the future of employment for knowledge workers.
        
        In my view, the traditional office environment often stifles creativity and productivity.
        
        From my perspective, companies that embrace remote work will have a competitive advantage in attracting talent.
        
        The evidence suggests that remote workers are often more productive and report higher job satisfaction.
        
        While some argue that in-person collaboration is essential, I would counter that modern tools make virtual collaboration equally effective.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    opinion_result = await content_analyzer.analyze(opinion_content)
    assert opinion_result.category == "opinion"


@pytest.mark.asyncio
async def test_quality_scoring(content_analyzer):
    """Test quality scoring functionality."""
    # 1. High-quality content (well-structured, substantive, from reliable source)
    high_quality_content = {
        "url": "https://edu.harvard.edu/research/study",
        "content": """
        A Comparative Analysis of Machine Learning Approaches for Natural Language Processing
        
        Abstract:
        This study examines five different machine learning approaches for natural language processing tasks,
        focusing on their performance in sentiment analysis, named entity recognition, and text classification.
        
        Introduction:
        Natural Language Processing (NLP) represents one of the most active areas of research in artificial intelligence.
        Recent advances in machine learning have dramatically improved the performance of NLP systems.
        
        Methodology:
        We evaluated transformer-based models (BERT, RoBERTa), recurrent neural networks (LSTM, GRU),
        and traditional methods (SVM with TF-IDF) across a diverse set of benchmark datasets.
        
        Results:
        The transformer-based models consistently outperformed other approaches, with BERT achieving 
        an average of 94.3% accuracy across all tasks. However, the RNN-based approaches demonstrated 
        superior performance in specific contexts, particularly those involving sequential dependencies.
        
        Discussion:
        Our findings suggest that while transformer models offer state-of-the-art performance,
        there remain specialized use cases where alternative approaches may be preferable.
        
        Conclusion:
        This comprehensive analysis provides guidance for NLP practitioners in selecting appropriate
        machine learning approaches based on their specific application requirements.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    high_quality_result = await content_analyzer.analyze(high_quality_content)
    assert high_quality_result.quality_score >= 0.8
    
    # 2. Medium quality content (less structure, shorter, generic source)
    medium_quality_content = {
        "url": "https://techblog.example.com/nlp-overview",
        "content": """
        NLP Models Overview
        
        Natural Language Processing has several popular approaches including transformers, RNNs, and traditional ML methods.
        
        BERT and GPT are transformer models that have shown great results in many tasks.
        
        LSTMs and GRUs are recurrent neural networks good for sequential data.
        
        SVMs with TF-IDF features are traditional methods that still work well for some simpler classification tasks.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    medium_quality_result = await content_analyzer.analyze(medium_quality_content)
    assert 0.4 <= medium_quality_result.quality_score < 0.8
    
    # 3. Low quality content (very short, poorly structured, generic)
    low_quality_content = {
        "url": "https://randomsite.com/post123",
        "content": """
        NLP stuff
        bert is good
        lstm also works
        i think transformers are best but not sure
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    low_quality_result = await content_analyzer.analyze(low_quality_content)
    assert low_quality_result.quality_score < 0.4


@pytest.mark.asyncio
async def test_relevance_scoring(content_analyzer):
    """Test relevance scoring with different queries."""
    # Content about machine learning
    ml_content = {
        "url": "https://example.com/machine-learning",
        "content": """
        Introduction to Machine Learning Algorithms
        
        Machine learning algorithms can be broadly categorized into supervised, unsupervised, and reinforcement learning.
        
        Supervised learning includes algorithms like linear regression, decision trees, and neural networks.
        
        Unsupervised learning encompasses clustering algorithms like k-means and hierarchical clustering.
        
        Reinforcement learning involves training agents to make decisions through reward-based feedback.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    # 1. Highly relevant query
    highly_relevant_query = "machine learning algorithms supervised unsupervised"
    highly_relevant_result = await content_analyzer.analyze(ml_content, highly_relevant_query)
    assert highly_relevant_result.relevance_score >= 0.8
    
    # 2. Moderately relevant query
    moderately_relevant_query = "neural networks decision trees"
    moderately_relevant_result = await content_analyzer.analyze(ml_content, moderately_relevant_query)
    assert 0.4 <= moderately_relevant_result.relevance_score < 0.8
    
    # 3. Slightly relevant query
    slightly_relevant_query = "data science statistics"
    slightly_relevant_result = await content_analyzer.analyze(ml_content, slightly_relevant_query)
    assert 0.1 <= slightly_relevant_result.relevance_score < 0.4
    
    # 4. Irrelevant query
    irrelevant_query = "ancient history roman empire"
    irrelevant_result = await content_analyzer.analyze(ml_content, irrelevant_query)
    assert irrelevant_result.relevance_score < 0.1


@pytest.mark.asyncio
async def test_reliability_checking(content_analyzer):
    """Test reliability checking functionality."""
    # 1. Content from a reliable domain with good structure
    reliable_content = {
        "url": "https://github.com/tensorflow/tensorflow/blob/master/README.md",
        "content": """
        # TensorFlow
        
        TensorFlow is an end-to-end open source platform for machine learning.
        
        ## Installation
        
        pip install tensorflow
        
        ## Documentation
        
        For comprehensive documentation, visit [tensorflow.org](https://www.tensorflow.org/).
        
        ## References
        
        1. Abadi, M., et al. (2016). TensorFlow: A system for large-scale machine learning.
        2. Dean, J., et al. (2012). Large Scale Distributed Deep Networks.
        """,
        "content_type": "text/markdown",
        "timestamp": time.time()
    }
    
    reliable_result = await content_analyzer.analyze(reliable_content)
    assert reliable_result.is_reliable
    
    # 2. Content from an unknown domain with poor structure
    unreliable_content = {
        "url": "https://random-blog-site123.com/ai-stuff",
        "content": """
        AI is changing everything!
        
        neural networks are the future. they will probably take over the world someday.
        
        tensorflow and pytorch are popular frameworks that people use for AI.
        
        i heard that gpt-4 is really smart but expensive.
        """,
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    unreliable_result = await content_analyzer.analyze(unreliable_content)
    assert not unreliable_result.is_reliable


@pytest.mark.asyncio
async def test_analyze_multiple(content_analyzer):
    """Test analyzing multiple content items concurrently."""
    # Create multiple content items
    contents = [
        {
            "url": f"https://example.com/article{i}",
            "content": f"This is test article {i} about {'Python programming' if i % 2 == 0 else 'Data science'}. {'It covers advanced topics.' if i % 3 == 0 else 'Good for beginners.'}",
            "content_type": "text/plain",
            "timestamp": time.time()
        }
        for i in range(5)
    ]
    
    # Analyze multiple contents
    results = await content_analyzer.analyze_multiple(contents)
    
    # Verify correct number of results
    assert len(results) == len(contents)
    
    # Verify all results are AnalysisResult objects
    assert all(isinstance(result, AnalysisResult) for result in results)
    
    # Verify each result matches its source content
    for i, result in enumerate(results):
        assert result.source_url == contents[i]["url"]
        assert "Python" in result.entities if i % 2 == 0 else "Data" in " ".join(result.entities)


@pytest.mark.asyncio
async def test_analyze_stream(content_analyzer):
    """Test streaming analysis of content items."""
    # Create content generator
    async def content_generator():
        for i in range(5):
            yield {
                "url": f"https://example.com/stream{i}",
                "content": f"Streaming content {i} about {'technology' if i % 2 == 0 else 'science'}.",
                "content_type": "text/plain",
                "timestamp": time.time()
            }
            await asyncio.sleep(0.1)  # Simulate delay between items
    
    # Collect streamed results
    results = []
    async for result in content_analyzer.analyze_stream(content_generator()):
        results.append(result)
    
    # Verify correct number of results
    assert len(results) == 5
    
    # Verify all results are AnalysisResult objects
    assert all(isinstance(result, AnalysisResult) for result in results)
    
    # Verify results match source URLs pattern
    for i, result in enumerate(results):
        assert f"stream{i}" in result.source_url


@pytest.mark.asyncio
async def test_error_handling(content_analyzer):
    """Test error handling during content analysis."""
    # 1. Empty content
    empty_content = {
        "url": "https://example.com/empty",
        "content": "",
        "content_type": "text/plain",
        "timestamp": time.time()
    }
    
    with pytest.raises(ContentAnalysisError) as excinfo:
        await content_analyzer.analyze(empty_content)
    assert "Empty content" in str(excinfo.value)
    
    # 2. Missing required fields
    incomplete_content = {
        "url": "https://example.com/incomplete"
        # Missing content and content_type
    }
    
    with pytest.raises(ContentAnalysisError) as excinfo:
        await content_analyzer.analyze(incomplete_content)
    
    # 3. Test error handling in analyze_multiple
    mixed_contents = [
        {
            "url": "https://example.com/good",
            "content": "This is good content.",
            "content_type": "text/plain",
            "timestamp": time.time()
        },
        {
            "url": "https://example.com/empty",
            "content": "",
            "content_type": "text/plain",
            "timestamp": time.time()
        },
        {
            "url": "https://example.com/good2",
            "content": "This is also good content.",
            "content_type": "text/plain",
            "timestamp": time.time()
        }
    ]
    
    # Should return only valid results, skipping errors
    results = await content_analyzer.analyze_multiple(mixed_contents)
    assert len(results) == 2  # Only the good contents
    assert all("good" in result.source_url for result in results)
