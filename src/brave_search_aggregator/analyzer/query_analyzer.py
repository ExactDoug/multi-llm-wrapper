"""
QueryAnalyzer component for analyzing and optimizing search queries.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import asyncio
import re
import time
import gc
import sys

from .input_detector import InputTypeDetector, InputType, InputTypeAnalysis
from .complexity_analyzer import ComplexityAnalyzer, ComplexityLevel, ComplexityAnalysis
from .ambiguity_detector import AmbiguityDetector, AmbiguityType, AmbiguityAnalysis
from .query_segmenter import QuerySegmenter, SegmentType, SegmentationResult

@dataclass
class QueryAnalysis:
    """Results of query analysis."""
    is_suitable_for_search: bool
    search_string: str
    complexity: str
    is_ambiguous: bool = False
    reason_unsuitable: Optional[str] = None
    sub_queries: List[str] = None
    possible_interpretations: List[str] = None
    insights: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    
    # New fields for enhanced analysis
    input_type: Optional[InputTypeAnalysis] = None
    complexity_analysis: Optional[ComplexityAnalysis] = None
    ambiguity_analysis: Optional[AmbiguityAnalysis] = None
    segmentation: Optional[SegmentationResult] = None

    def __post_init__(self):
        """Initialize optional lists."""
        if self.sub_queries is None:
            self.sub_queries = []
        if self.possible_interpretations is None:
            self.possible_interpretations = []
        if self.performance_metrics is None:
            self.performance_metrics = {}

    def __str__(self) -> str:
        """String representation of query analysis."""
        parts = [
            f"Search string: {self.search_string}",
            f"Complexity: {self.complexity}"
        ]
        
        if self.is_ambiguous:
            parts.append("Status: Ambiguous")
            if self.possible_interpretations:
                parts.append(f"Possible interpretations: {', '.join(self.possible_interpretations)}")
                
        if self.sub_queries:
            parts.append(f"Sub-queries: {', '.join(self.sub_queries)}")
            
        if self.insights:
            parts.append(f"Insights: {self.insights}")
            
        if not self.is_suitable_for_search:
            parts.append(f"Not suitable for search: {self.reason_unsuitable}")

        if self.performance_metrics:
            parts.append("Performance Metrics:")
            for key, value in self.performance_metrics.items():
                parts.append(f"  {key}: {value}")
            
        return "\n".join(parts)

class ResourceManager:
    """Manages resources and memory usage."""
    
    def __init__(self, max_memory_mb: int = 10):
        self.max_memory_mb = max_memory_mb * 1024 * 1024  # Convert to bytes
        self.start_memory = 0
        self.peak_memory = 0
        
    def __enter__(self):
        """Start tracking resource usage."""
        gc.collect()  # Force garbage collection
        self.start_memory = self._get_memory_usage()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources."""
        gc.collect()  # Force garbage collection
        
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        return sys.getsizeof(self) + sum(sys.getsizeof(obj) for obj in gc.get_objects())
        
    def check_memory_usage(self) -> bool:
        """Check if memory usage is within limits."""
        current_memory = self._get_memory_usage()
        self.peak_memory = max(self.peak_memory, current_memory)
        return current_memory - self.start_memory <= self.max_memory_mb

class QueryAnalyzer:
    """Analyzes and optimizes search queries."""
    
    MAX_QUERY_LENGTH = 2000
    ARITHMETIC_OPERATORS = {'+', '-', '*', '/', '='}
    COMPLEX_INDICATORS = {'compare', 'between', 'relationship', 'correlation', 'difference'}
    AMBIGUOUS_TERMS = {
        'python': ['programming language', 'snake'],
        'java': ['programming language', 'coffee', 'island'],
        'ruby': ['programming language', 'gemstone'],
    }
    # Common English stop words
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
        'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were',
        'will', 'with', 'the', 'this', 'but', 'they', 'have', 'had', 'what', 'when',
        'where', 'who', 'which', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'can', 'just', 'should', 'now'
    }
    
    def __init__(self):
        """Initialize the QueryAnalyzer."""
        self._resource_manager = ResourceManager(max_memory_mb=10)
        self._buffer = []
        self._buffer_size = 0
        self._max_buffer_size = 1000  # Maximum number of items in buffer
        self._cleanup_required = False
        
        # Initialize analysis components
        self._input_detector = InputTypeDetector()
        self._complexity_analyzer = ComplexityAnalyzer()
        self._ambiguity_detector = AmbiguityDetector()
        self._query_segmenter = QuerySegmenter()
        
    async def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a search query for suitability and complexity.
        
        Args:
            query: The search query to analyze
        
        Returns:
            QueryAnalysis object containing analysis results
        
        Raises:
            ValueError: If query is empty or too long
            MemoryError: If memory usage exceeds limits
        """
        start_time = time.time()
        
        try:
            with self._resource_manager as rm:
                # Preprocess the query to remove unnecessary characters and formatting
                query = self._preprocess_query(query)
                
                # Validate query
                if not query or query.isspace():
                    raise ValueError("Empty query")
                if len(query) > self.MAX_QUERY_LENGTH:
                    raise ValueError("Query too long")
                
                query = query.strip()
                
                # Check memory usage
                if not rm.check_memory_usage():
                    raise MemoryError("Memory usage exceeded limits")
                
                # Check if query is unsuitable (e.g., basic arithmetic)
                if self._is_arithmetic_query(query):
                    return QueryAnalysis(
                        is_suitable_for_search=False,
                        search_string=query,
                        complexity="basic",
                        reason_unsuitable="basic arithmetic query",
                        performance_metrics={
                            'processing_time_ms': (time.time() - start_time) * 1000,
                            'memory_usage_mb': (rm._get_memory_usage() - rm.start_memory) / (1024 * 1024)
                        }
                    )
                
                # Perform enhanced analysis using new components
                input_analysis = self._input_detector.detect_type(query)
                complexity_analysis = self._complexity_analyzer.analyze_complexity(query)
                ambiguity_analysis = self._ambiguity_detector.analyze_ambiguity(query)
                segmentation_result = self._query_segmenter.segment_query(query)
                
                # Map complexity level to string representation
                complexity_map = {
                    ComplexityLevel.SIMPLE: "simple",
                    ComplexityLevel.MODERATE: "moderate",
                    ComplexityLevel.COMPLEX: "complex",
                    ComplexityLevel.VERY_COMPLEX: "very complex"
                }
                complexity = complexity_map[complexity_analysis.level]
                
                # Generate sub-queries from segmentation
                sub_queries = [
                    segment.content for segment in segmentation_result.segments
                    if segment.type == SegmentType.QUESTION
                ]
                
                # Get possible interpretations from ambiguity analysis
                possible_interpretations = []
                if ambiguity_analysis.is_ambiguous:
                    for instance in ambiguity_analysis.instances:
                        possible_interpretations.extend(instance.possible_meanings)
                
                # Generate insights based on all analyses
                insights = []
                
                # Input type insights
                insights.append(f"Input Type: {input_analysis.primary_type.name}")
                if input_analysis.confidence < 0.8:
                    insights.append("Mixed input types detected")
                
                # Complexity insights
                insights.append(f"Complexity Level: {complexity}")
                if complexity_analysis.factors:
                    insights.append("Complexity factors:")
                    insights.extend(f"- {factor}" for factor in complexity_analysis.factors)
                
                # Ambiguity insights
                if ambiguity_analysis.is_ambiguous:
                    insights.append("Ambiguity detected:")
                    for instance in ambiguity_analysis.instances:
                        insights.append(f"- {instance.term}: {', '.join(instance.possible_meanings)}")
                
                # Segmentation insights
                if segmentation_result.has_mixed_types:
                    insights.append(f"Mixed content types ({segmentation_result.segment_count} segments)")
                
                insights_text = "\n".join(insights)
                
                # Check memory usage again
                if not rm.check_memory_usage():
                    raise MemoryError("Memory usage exceeded limits")
                
                # Determine if query is suitable for search based on input type and complexity
                is_suitable = (
                    input_analysis.primary_type != InputType.CODE and
                    input_analysis.primary_type != InputType.ERROR_LOG and
                    complexity_analysis.level != ComplexityLevel.VERY_COMPLEX
                )
                
                return QueryAnalysis(
                    is_suitable_for_search=is_suitable,
                    search_string=query,
                    complexity=complexity,
                    is_ambiguous=ambiguity_analysis.is_ambiguous,
                    possible_interpretations=possible_interpretations,
                    sub_queries=sub_queries,
                    insights=insights_text,
                    performance_metrics={
                        'processing_time_ms': (time.time() - start_time) * 1000,
                        'memory_usage_mb': (rm._get_memory_usage() - rm.start_memory) / (1024 * 1024),
                        'input_type_confidence': input_analysis.confidence,
                        'ambiguity_score': ambiguity_analysis.ambiguity_score,
                        'complexity_score': complexity_analysis.score
                    },
                    # Include full analysis results
                    input_type=input_analysis,
                    complexity_analysis=complexity_analysis,
                    ambiguity_analysis=ambiguity_analysis,
                    segmentation=segmentation_result
                )
                
        except Exception as e:
            # Handle errors and return partial results if possible
            error_analysis = QueryAnalysis(
                is_suitable_for_search=False,
                search_string=query,
                complexity="unknown",
                reason_unsuitable=str(e),
                performance_metrics={
                    'processing_time_ms': (time.time() - start_time) * 1000,
                    'error': str(e)
                }
            )
            return error_analysis
        finally:
            # Cleanup if needed
            if self._cleanup_required:
                await self._cleanup()
    
    async def _cleanup(self):
        """Clean up resources."""
        self._buffer.clear()
        self._buffer_size = 0
        self._cleanup_required = False
        gc.collect()
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess the query to remove unnecessary characters and formatting.
        
        Args:
            query: The search query to preprocess
        
        Returns:
            Preprocessed query
        """
        # Remove XML tags
        query = re.sub(r'<.*?>', '', query)
        
        # Remove error messages
        query = re.sub(r'Error:.*?', '', query)
        
        # Remove diagnostic code
        query = re.sub(r'Diagnostic Code:.*?', '', query)
        
        # Remove unnecessary whitespace
        query = re.sub(r'\s+', ' ', query)
        
        return query
    
    def _optimize_query(self, query: str) -> str:
        """
        Perform basic query optimization.
        
        Args:
            query: The search query to optimize
            
        Returns:
            Optimized search string
        """
        # Convert to lowercase for consistent processing
        query = query.lower()
        
        # Split into words
        words = query.split()
        
        # Remove stop words while preserving phrase meaning
        optimized_words = []
        i = 0
        while i < len(words):
            # Skip stop words unless they're part of a known phrase
            if words[i] not in self.STOP_WORDS or (
                i < len(words) - 1 and
                f"{words[i]} {words[i+1]}" in {
                    "machine learning", "artificial intelligence",
                    "deep learning", "data science"
                }
            ):
                optimized_words.append(words[i])
            i += 1
            
        # Rejoin words and normalize whitespace
        optimized = ' '.join(optimized_words)
        
        # Handle special characters (keep quotes for exact phrases)
        optimized = ''.join(c for c in optimized if c.isalnum() or c in ' "\'')
        
        # Remove extra whitespace
        optimized = ' '.join(optimized.split())
        
        return optimized
    
    def _is_arithmetic_query(self, query: str) -> bool:
        """Check if query is a basic arithmetic operation."""
        words = query.split()
        return any(op in words for op in self.ARITHMETIC_OPERATORS)
    
    def __aiter__(self):
        """Return self as async iterator."""
        self._buffer.clear()
        self._buffer_size = 0
        return self
    
    async def __anext__(self):
        """Get next analysis result."""
        try:
            # Check if cleanup is needed
            if self._cleanup_required:
                await self._cleanup()
            
            # Check buffer size
            if self._buffer_size >= self._max_buffer_size:
                self._cleanup_required = True
                raise StopAsyncIteration
            
            # Get next query from buffer or raise StopAsyncIteration
            if not self._buffer:
                raise StopAsyncIteration
            
            query = self._buffer.pop(0)
            self._buffer_size -= 1
            
            # Analyze query
            return await self.analyze_query(query)
            
        except Exception as e:
            self._cleanup_required = True
            raise StopAsyncIteration from e

# Test the QueryAnalyzer class
if __name__ == "__main__":
    analyzer = QueryAnalyzer()
    query = """
This is a sample diagnostic code output.
It has multiple paragraphs and line breaks.
The query is: What is the meaning of life?
The answer is: 42.
But what about the universe?
Is it expanding or contracting?
The query is: What is the nature of reality?
The answer is: It is complex and multifaceted.
But what about the human experience?
Is it meaningful or meaningless?
The query is: What is the purpose of existence?
The answer is: It is to find meaning and purpose.
But what about the role of technology?
Is it a tool or a threat?
The query is: What is the impact of technology on society?
The answer is: It is complex and multifaceted.
But what about the future?
Is it bright or bleak?
The query is: What is the future of humanity?
The answer is: It is uncertain and unpredictable.
"""
    result = asyncio.run(analyzer.analyze_query(query))
    print(f"Query: {query}")
    print("Query Analysis:")
    print(f"Search String: {result.search_string}")
    print(f"Complexity: {result.complexity}")
    print(f"Is Ambiguous: {result.is_ambiguous}")
    print(f"Possible Interpretations: {result.possible_interpretations}")
    print(f"Sub-queries: {result.sub_queries}")
    print(f"Insights: {result.insights}")
    print(f"Performance Metrics: {result.performance_metrics}")
    print()