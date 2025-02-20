"""
Complexity analysis component for the QueryAnalyzer.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Optional
import re

class ComplexityLevel(Enum):
    """Enumeration of complexity levels."""
    SIMPLE = auto()
    MODERATE = auto()
    COMPLEX = auto()
    VERY_COMPLEX = auto()

@dataclass
class ComplexityMetrics:
    """Detailed complexity metrics."""
    sentence_count: int
    avg_sentence_length: float
    nested_clause_count: int
    technical_term_count: int
    distinct_topic_count: int
    cross_references: int
    context_depth: int

@dataclass
class ComplexityAnalysis:
    """Results of complexity analysis."""
    level: ComplexityLevel
    score: float  # 0.0 to 1.0
    metrics: ComplexityMetrics
    factors: List[str]
    details: Optional[str] = None

class ComplexityAnalyzer:
    """Analyzes query complexity based on multiple factors."""
    
    # Technical terms by domain
    TECHNICAL_TERMS = {
        'programming': {
            'algorithm', 'function', 'class', 'method', 'variable',
            'inheritance', 'polymorphism', 'interface', 'api',
            'database', 'query', 'server', 'client', 'framework'
        },
        'networking': {
            'protocol', 'tcp/ip', 'dns', 'router', 'firewall',
            'subnet', 'gateway', 'bandwidth', 'latency', 'packet'
        },
        'system': {
            'cpu', 'memory', 'disk', 'process', 'thread',
            'kernel', 'driver', 'filesystem', 'buffer', 'cache'
        }
    }
    
    # Patterns indicating nested clauses
    NESTED_PATTERNS = [
        r'if.*?(?:else|elif)',
        r'try.*?except',
        r'while.*?in',
        r'for.*?in',
        r'\((?:[^()]*\([^()]*\))*[^()]*\)'  # Nested parentheses
    ]
    
    def __init__(self):
        """Initialize the ComplexityAnalyzer."""
        self.nested_regex = [re.compile(p) for p in self.NESTED_PATTERNS]
        # Flatten technical terms for easier lookup
        self.all_technical_terms = {
            term for domain_terms in self.TECHNICAL_TERMS.values()
            for term in domain_terms
        }
        
    def analyze_complexity(self, text: str) -> ComplexityAnalysis:
        """
        Analyze the complexity of the given text.
        
        Args:
            text: The text to analyze
            
        Returns:
            ComplexityAnalysis containing complexity metrics and assessment
        """
        # Calculate basic metrics
        sentences = self._split_into_sentences(text)
        sentence_count = len(sentences)
        avg_length = sum(len(s.split()) for s in sentences) / max(sentence_count, 1)
        
        # Calculate technical metrics
        metrics = ComplexityMetrics(
            sentence_count=sentence_count,
            avg_sentence_length=avg_length,
            nested_clause_count=self._count_nested_clauses(text),
            technical_term_count=self._count_technical_terms(text),
            distinct_topic_count=self._count_distinct_topics(text),
            cross_references=self._count_cross_references(text),
            context_depth=self._calculate_context_depth(text)
        )
        
        # Calculate complexity factors
        factors = self._determine_complexity_factors(metrics)
        
        # Calculate overall complexity
        complexity_score = self._calculate_complexity_score(metrics)
        complexity_level = self._determine_complexity_level(complexity_score)
        
        return ComplexityAnalysis(
            level=complexity_level,
            score=complexity_score,
            metrics=metrics,
            factors=factors,
            details=self._generate_complexity_details(complexity_level, factors)
        )
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Basic sentence splitting - could be enhanced with NLP
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _count_nested_clauses(self, text: str) -> int:
        """Count nested clauses in the text."""
        return sum(len(pattern.findall(text)) for pattern in self.nested_regex)
    
    def _count_technical_terms(self, text: str) -> int:
        """Count technical terms in the text."""
        words = set(re.findall(r'\b\w+\b', text.lower()))
        return len(words.intersection(self.all_technical_terms))
    
    def _count_distinct_topics(self, text: str) -> int:
        """Estimate number of distinct topics."""
        # Simple estimation based on technical term domains
        topics = set()
        words = set(re.findall(r'\b\w+\b', text.lower()))
        for domain, terms in self.TECHNICAL_TERMS.items():
            if words.intersection(terms):
                topics.add(domain)
        return len(topics)
    
    def _count_cross_references(self, text: str) -> int:
        """Count cross-references between topics."""
        # Look for phrases indicating relationships between topics
        reference_patterns = [
            r'compared to',
            r'related to',
            r'with respect to',
            r'in terms of',
            r'versus',
            r'as opposed to'
        ]
        return sum(len(re.findall(pattern, text, re.IGNORECASE))
                  for pattern in reference_patterns)
    
    def _calculate_context_depth(self, text: str) -> int:
        """Calculate the context depth required."""
        # Estimate based on various factors
        depth = 0
        
        # Check for temporal context
        if re.search(r'\b(?:before|after|during|while)\b', text, re.IGNORECASE):
            depth += 1
            
        # Check for conditional context
        if re.search(r'\b(?:if|when|unless|assuming)\b', text, re.IGNORECASE):
            depth += 1
            
        # Check for comparative context
        if re.search(r'\b(?:compared|versus|better|worse)\b', text, re.IGNORECASE):
            depth += 1
            
        # Check for system-level context
        if re.search(r'\b(?:system|environment|platform)\b', text, re.IGNORECASE):
            depth += 1
            
        return depth
    
    def _determine_complexity_factors(self, metrics: ComplexityMetrics) -> List[str]:
        """Determine factors contributing to complexity."""
        factors = []
        
        if metrics.sentence_count > 3:
            factors.append(f"Multiple sentences ({metrics.sentence_count})")
        if metrics.avg_sentence_length > 15:
            factors.append(f"Long sentences (avg {metrics.avg_sentence_length:.1f} words)")
        if metrics.nested_clause_count > 0:
            factors.append(f"Nested clauses ({metrics.nested_clause_count})")
        if metrics.technical_term_count > 2:
            factors.append(f"Technical terms ({metrics.technical_term_count})")
        if metrics.distinct_topic_count > 1:
            factors.append(f"Multiple topics ({metrics.distinct_topic_count})")
        if metrics.cross_references > 0:
            factors.append(f"Cross-references ({metrics.cross_references})")
        if metrics.context_depth > 1:
            factors.append(f"Deep context ({metrics.context_depth} levels)")
            
        return factors
    
    def _calculate_complexity_score(self, metrics: ComplexityMetrics) -> float:
        """Calculate overall complexity score."""
        # Weight different factors
        weights = {
            'sentence_count': 0.1,
            'avg_sentence_length': 0.15,
            'nested_clause_count': 0.2,
            'technical_term_count': 0.15,
            'distinct_topic_count': 0.15,
            'cross_references': 0.1,
            'context_depth': 0.15
        }
        
        # Normalize each metric to 0-1 range
        normalized = {
            'sentence_count': min(metrics.sentence_count / 10, 1.0),
            'avg_sentence_length': min(metrics.avg_sentence_length / 30, 1.0),
            'nested_clause_count': min(metrics.nested_clause_count / 5, 1.0),
            'technical_term_count': min(metrics.technical_term_count / 10, 1.0),
            'distinct_topic_count': min(metrics.distinct_topic_count / 5, 1.0),
            'cross_references': min(metrics.cross_references / 5, 1.0),
            'context_depth': min(metrics.context_depth / 5, 1.0)
        }
        
        # Calculate weighted sum
        return sum(weights[k] * normalized[k] for k in weights)
    
    def _determine_complexity_level(self, score: float) -> ComplexityLevel:
        """Determine complexity level based on score."""
        if score < 0.3:
            return ComplexityLevel.SIMPLE
        elif score < 0.5:
            return ComplexityLevel.MODERATE
        elif score < 0.7:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX
    
    def _generate_complexity_details(self, level: ComplexityLevel,
                                   factors: List[str]) -> str:
        """Generate detailed explanation of complexity assessment."""
        level_descriptions = {
            ComplexityLevel.SIMPLE: "Query is straightforward",
            ComplexityLevel.MODERATE: "Query has moderate complexity",
            ComplexityLevel.COMPLEX: "Query is complex",
            ComplexityLevel.VERY_COMPLEX: "Query is highly complex"
        }
        
        details = [level_descriptions[level]]
        if factors:
            details.append("Complexity factors:")
            details.extend(f"- {factor}" for factor in factors)
            
        return "\n".join(details)