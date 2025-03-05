"""
Input type detection for the QueryAnalyzer component.
"""
from dataclasses import dataclass
from enum import Enum, auto
import re
from typing import List, Optional

class InputType(Enum):
    """Enumeration of possible input types."""
    NATURAL_LANGUAGE = auto()
    CODE = auto()
    LOG = auto()
    ERROR_LOG = auto()
    MIXED = auto()

@dataclass
class InputTypeAnalysis:
    """Results of input type analysis."""
    primary_type: InputType
    confidence: float  # 0.0 to 1.0
    detected_types: List[InputType]
    details: Optional[str] = None

class InputTypeDetector:
    """Detects and classifies input types in queries."""
    
    # Code detection patterns
    CODE_PATTERNS = {
        'xml_html': r'<[^>]+>',
        'code_block': r'```[\s\S]*?```|`[^`]+`',
        'function_def': r'\b(?:def|function|class)\s+\w+',
        'variable_assignment': r'\b\w+\s*=\s*[\w\'"{\[]+',
    }
    
    # Log detection patterns
    LOG_PATTERNS = {
        'timestamp': r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}',
        'log_level': r'\b(?:DEBUG|INFO|WARNING|ERROR|CRITICAL)\b',
        'stack_trace': r'(?:Exception|Error|Stack trace):[^\n]+(?:\n\s+at\s+[^\n]+)*',
        'file_line': r'\b(?:in|at)\s+[\w/\\.]+:\d+\b',
    }
    
    # Natural language patterns
    NL_PATTERNS = {
        'question': r'\b(?:what|when|where|why|how|who|which)\b.*\?',
        'sentence': r'[A-Z][^.!?]*[.!?]',
        'conversation': r'\b(?:I|you|we|they)\b.*\b(?:think|believe|want|need)\b',
    }

    def __init__(self, confidence_threshold: float = 0.8):
        """
        Initialize the InputTypeDetector.
        
        Args:
            confidence_threshold: Minimum confidence threshold for type detection (0.0 to 1.0)
            
        Raises:
            ValueError: If confidence_threshold is not between 0.0 and 1.0
        """
        if not isinstance(confidence_threshold, (int, float)):
            raise ValueError(f"confidence_threshold must be a number, got {type(confidence_threshold)}")
            
        if not 0 <= confidence_threshold <= 1:
            raise ValueError(f"confidence_threshold must be between 0.0 and 1.0, got {confidence_threshold}")
        
        self.confidence_threshold = confidence_threshold
        
        # Compile regex patterns for efficiency
        self.code_regex = {k: re.compile(v, re.IGNORECASE) for k, v in self.CODE_PATTERNS.items()}
        self.log_regex = {k: re.compile(v) for k, v in self.LOG_PATTERNS.items()}
        self.nl_regex = {k: re.compile(v, re.IGNORECASE) for k, v in self.NL_PATTERNS.items()}

    def detect_type(self, text: str) -> InputTypeAnalysis:
        """
        Detect the type of input in the given text.
        
        Args:
            text: The text to analyze
            
        Returns:
            InputTypeAnalysis containing the detected type and confidence
        """
        # Initialize counters for each type
        code_matches = self._count_code_matches(text)
        log_matches = self._count_log_matches(text)
        nl_matches = self._count_nl_matches(text)
        
        # Calculate total matches
        total_matches = code_matches + log_matches + nl_matches
        if total_matches == 0:
            # Default to natural language if no clear patterns are found
            return InputTypeAnalysis(
                primary_type=InputType.NATURAL_LANGUAGE,
                confidence=0.5,
                detected_types=[InputType.NATURAL_LANGUAGE],
                details="No clear patterns detected, defaulting to natural language"
            )
        
        # Calculate percentages
        code_percent = code_matches / total_matches
        log_percent = log_matches / total_matches
        nl_percent = nl_matches / total_matches
        
        # Determine detected types
        detected_types = []
        if code_percent > 0.1:
            detected_types.append(InputType.CODE)
        if log_percent > 0.1:
            detected_types.append(InputType.LOG)
        if nl_percent > 0.1:
            detected_types.append(InputType.NATURAL_LANGUAGE)
            
        # Determine primary type and confidence
        if len(detected_types) > 1:
            primary_type = InputType.MIXED
            confidence = max(code_percent, log_percent, nl_percent)
            details = f"Mixed input detected: Code ({code_percent:.1%}), Log ({log_percent:.1%}), Natural Language ({nl_percent:.1%})"
        else:
            if code_percent > log_percent and code_percent > nl_percent:
                primary_type = InputType.CODE
                confidence = code_percent
                details = f"Code patterns detected with {confidence:.1%} confidence"
            elif log_percent > code_percent and log_percent > nl_percent:
                primary_type = InputType.LOG
                confidence = log_percent
                details = f"Log patterns detected with {confidence:.1%} confidence"
            else:
                primary_type = InputType.NATURAL_LANGUAGE
                confidence = nl_percent
                details = f"Natural language patterns detected with {confidence:.1%} confidence"
                
        return InputTypeAnalysis(
            primary_type=primary_type,
            confidence=confidence,
            detected_types=detected_types,
            details=details
        )
    
    def _count_code_matches(self, text: str) -> int:
        """Count matches for code patterns."""
        return sum(1 for pattern in self.code_regex.values() if pattern.search(text))
    
    def _count_log_matches(self, text: str) -> int:
        """Count matches for log patterns."""
        return sum(1 for pattern in self.log_regex.values() if pattern.search(text))
    
    def _count_nl_matches(self, text: str) -> int:
        """Count matches for natural language patterns."""
        return sum(1 for pattern in self.nl_regex.values() if pattern.search(text))