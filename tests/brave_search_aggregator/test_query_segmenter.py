"""
Tests for the query segmentation component.
"""
import pytest
from brave_search_aggregator.analyzer.query_segmenter import (
    QuerySegmenter,
    SegmentType
)

@pytest.fixture
def segmenter():
    """Create a QuerySegmenter instance for testing."""
    return QuerySegmenter()

def test_question_segmentation():
    """Test segmentation of questions."""
    segmenter = QuerySegmenter()
    
    query = """
    What is a binary search tree?
    How do you implement one in Python?
    Can you show me an example?
    """
    
    result = segmenter.segment_query(query)
    assert result.segment_count >= 3
    assert result.primary_type == SegmentType.QUESTION
    assert not result.has_mixed_types
    assert all(segment.type == SegmentType.QUESTION 
              for segment in result.segments)

def test_code_block_segmentation():
    """Test segmentation of code blocks."""
    segmenter = QuerySegmenter()
    
    query = """
    Here's my implementation:
    
    ```python
    def binary_search(arr, target):
        left, right = 0, len(arr) - 1
        while left <= right:
            mid = (left + right) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return -1
    ```
    
    But it's not working correctly.
    """
    
    result = segmenter.segment_query(query)
    assert result.segment_count >= 3
    assert result.has_mixed_types
    
    # Should find at least one code block
    code_segments = [s for s in result.segments 
                    if s.type == SegmentType.CODE_BLOCK]
    assert len(code_segments) >= 1
    
    # Should find statements before and after code
    statement_segments = [s for s in result.segments 
                        if s.type == SegmentType.STATEMENT]
    assert len(statement_segments) >= 2

def test_error_log_segmentation():
    """Test segmentation of error logs."""
    segmenter = QuerySegmenter()
    
    query = """
    I'm getting this error:
    
    2025-02-19 11:23:45 ERROR: NullPointerException
        at MyClass.processData(MyClass.java:123)
        at Main.main(Main.java:45)
    
    How do I fix it?
    """
    
    result = segmenter.segment_query(query)
    assert result.segment_count >= 3
    assert result.has_mixed_types
    
    # Should find error log and question
    segment_types = {segment.type for segment in result.segments}
    assert SegmentType.ERROR_LOG in segment_types
    assert SegmentType.QUESTION in segment_types

def test_metadata_segmentation():
    """Test segmentation of metadata."""
    segmenter = QuerySegmenter()
    
    query = """
    @version: 1.2.3
    @author: John Doe
    
    How do I update the configuration?
    
    #environment = production
    #status = active
    """
    
    result = segmenter.segment_query(query)
    assert result.has_mixed_types
    
    # Should find metadata segments
    metadata_segments = [s for s in result.segments 
                        if s.type == SegmentType.METADATA]
    assert len(metadata_segments) >= 2

def test_mixed_content_segmentation():
    """Test segmentation of mixed content types."""
    segmenter = QuerySegmenter()
    
    query = """
    How do I fix this error?
    
    ERROR: Failed to connect to database
        at DatabaseConnection.connect():123
    
    Here's my current code:
    
    ```python
    def connect():
        return db.connect(host, port)
    ```
    
    @environment: development
    @database: PostgreSQL
    """
    
    result = segmenter.segment_query(query)
    assert result.has_mixed_types
    assert result.segment_count >= 4
    
    # Should find multiple segment types
    segment_types = {segment.type for segment in result.segments}
    assert len(segment_types) >= 4
    assert SegmentType.QUESTION in segment_types
    assert SegmentType.ERROR_LOG in segment_types
    assert SegmentType.CODE_BLOCK in segment_types
    assert SegmentType.METADATA in segment_types

def test_segment_positions():
    """Test accuracy of segment positions."""
    segmenter = QuerySegmenter()
    
    query = "What is x? x = 5"
    
    result = segmenter.segment_query(query)
    
    # Verify positions are correct
    for segment in result.segments:
        assert segment.content == query[segment.start_pos:segment.end_pos].strip()
        if segment.type == SegmentType.QUESTION:
            assert segment.content.endswith('?')

def test_empty_input():
    """Test handling of empty or whitespace input."""
    segmenter = QuerySegmenter()
    
    empty_queries = ["", "   ", "\n\n"]
    
    for query in empty_queries:
        result = segmenter.segment_query(query)
        assert result.segment_count == 0
        assert len(result.segments) == 0
        assert result.primary_type == SegmentType.STATEMENT
        assert not result.has_mixed_types

def test_details_generation():
    """Test generation of segmentation details."""
    segmenter = QuerySegmenter()
    
    query = """
    What is the error?
    
    ERROR: Connection failed
    
    ```python
    connect()
    ```
    """
    
    result = segmenter.segment_query(query)
    assert result.details is not None
    assert "Query Segmentation Analysis:" in result.details
    assert "Total segments:" in result.details
    assert "Segment type distribution:" in result.details
    assert "Segment details:" in result.details