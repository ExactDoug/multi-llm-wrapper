"""
Query segmentation component for the QueryAnalyzer.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Optional
import re

class SegmentType(Enum):
    """Types of query segments."""
    QUESTION = auto()
    STATEMENT = auto()
    CODE_BLOCK = auto()
    ERROR_LOG = auto()
    CONTEXT = auto()
    METADATA = auto()

@dataclass
class QuerySegment:
    """Represents a segment of the query."""
    type: SegmentType
    content: str
    start_pos: int
    end_pos: int
    metadata: Optional[Dict[str, str]] = None

@dataclass
class SegmentationResult:
    """Results of query segmentation."""
    segments: List[QuerySegment]
    segment_count: int
    has_mixed_types: bool
    primary_type: SegmentType
    details: Optional[str] = None

class QuerySegmenter:
    """Segments queries into logical parts based on type and content."""
    
    # Patterns for different segment types
    PATTERNS = {
        'code_block': [
            r'```[\s\S]*?```',  # Markdown code blocks
            r'<code>[\s\S]*?</code>',  # HTML code tags
            r'(?m)^[ ]{4}.*$',  # Indented code blocks
        ],
        'error_log': [
            r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}.*?(?:\n\s+at\s+.*?)*',  # Timestamps with stack traces
            r'(?:ERROR|WARN|INFO|DEBUG):.*(?:\n\s+.*)*',  # Log levels with content
            r'Exception:.*(?:\n\s+at\s+.*)*',  # Exception stack traces
        ],
        'question': [
            r'\b(?:what|when|where|why|how|who|which|whose|whom)\b[^.!?\n]*\?',  # WH-questions
            r'(?:can|could|would|should|is|are|do|does|did)[^.!?\n]*\?',  # Yes/no questions
        ],
        'metadata': [
            r'@\w+:.*(?:\n\s+.*)*',  # Tagged metadata
            r'#\w+\s*=.*(?:\n\s+.*)*',  # Key-value metadata
        ],
    }
    
    def __init__(self):
        """Initialize the QuerySegmenter."""
        # Compile regex patterns
        self.compiled_patterns = {
            type_name: [re.compile(pattern, re.IGNORECASE) 
                       for pattern in patterns]
            for type_name, patterns in self.PATTERNS.items()
        }
        
    def segment_query(self, text: str) -> SegmentationResult:
        """
        Segment a query into logical parts.
        
        Args:
            text: The query text to segment
            
        Returns:
            SegmentationResult containing the identified segments
        """
        segments = []
        
        # Find all segments with their positions
        segment_positions = []
        
        # Find code blocks
        for pattern in self.compiled_patterns['code_block']:
            for match in pattern.finditer(text):
                segment_positions.append((
                    match.start(),
                    match.end(),
                    SegmentType.CODE_BLOCK,
                    match.group()
                ))
        
        # Find error logs
        for pattern in self.compiled_patterns['error_log']:
            for match in pattern.finditer(text):
                segment_positions.append((
                    match.start(),
                    match.end(),
                    SegmentType.ERROR_LOG,
                    match.group()
                ))
        
        # Find questions
        for pattern in self.compiled_patterns['question']:
            for match in pattern.finditer(text):
                segment_positions.append((
                    match.start(),
                    match.end(),
                    SegmentType.QUESTION,
                    match.group()
                ))
        
        # Find metadata
        for pattern in self.compiled_patterns['metadata']:
            for match in pattern.finditer(text):
                segment_positions.append((
                    match.start(),
                    match.end(),
                    SegmentType.METADATA,
                    match.group()
                ))
        
        # Sort segments by position
        segment_positions.sort()
        
        # Handle non-overlapping segments
        current_pos = 0
        for start, end, type_, content in segment_positions:
            # Add any text between segments as STATEMENT
            if start > current_pos:
                intermediate = text[current_pos:start].strip()
                if intermediate:
                    segments.append(QuerySegment(
                        type=SegmentType.STATEMENT,
                        content=intermediate,
                        start_pos=current_pos,
                        end_pos=start
                    ))
            
            # Add the segment
            segments.append(QuerySegment(
                type=type_,
                content=content,
                start_pos=start,
                end_pos=end
            ))
            
            current_pos = end
        
        # Add any remaining text as STATEMENT
        if current_pos < len(text):
            remaining = text[current_pos:].strip()
            if remaining:
                segments.append(QuerySegment(
                    type=SegmentType.STATEMENT,
                    content=remaining,
                    start_pos=current_pos,
                    end_pos=len(text)
                ))
        
        # Determine primary type and mixed status
        type_counts = {}
        for segment in segments:
            type_counts[segment.type] = type_counts.get(segment.type, 0) + 1
        
        primary_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else SegmentType.STATEMENT
        has_mixed_types = len(type_counts) > 1
        
        # Generate details
        details = self._generate_segmentation_details(segments, type_counts)
        
        return SegmentationResult(
            segments=segments,
            segment_count=len(segments),
            has_mixed_types=has_mixed_types,
            primary_type=primary_type,
            details=details
        )
    
    def _generate_segmentation_details(self, 
                                     segments: List[QuerySegment],
                                     type_counts: Dict[SegmentType, int]) -> str:
        """Generate detailed explanation of segmentation."""
        if not segments:
            return "No segments identified"
        
        details = ["Query Segmentation Analysis:"]
        
        # Overall statistics
        details.append(f"\nTotal segments: {len(segments)}")
        details.append("Segment type distribution:")
        for type_, count in type_counts.items():
            details.append(f"- {type_.name}: {count}")
        
        # Detailed segment information
        details.append("\nSegment details:")
        for i, segment in enumerate(segments, 1):
            details.append(f"\nSegment {i}:")
            details.append(f"- Type: {segment.type.name}")
            details.append(f"- Position: {segment.start_pos}-{segment.end_pos}")
            # Truncate content if too long
            content = segment.content
            if len(content) > 100:
                content = f"{content[:97]}..."
            details.append(f"- Content: {content}")
            
        return "\n".join(details)