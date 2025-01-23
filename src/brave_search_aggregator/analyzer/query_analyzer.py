"""
QueryAnalyzer component for analyzing and optimizing search queries.
"""
from dataclasses import dataclass
from typing import List, Optional

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

    def __post_init__(self):
        """Initialize optional lists."""
        if self.sub_queries is None:
            self.sub_queries = []
        if self.possible_interpretations is None:
            self.possible_interpretations = []

class QueryAnalyzer:
    """Analyzes and optimizes search queries."""

    MAX_QUERY_LENGTH = 500
    ARITHMETIC_OPERATORS = {'+', '-', '*', '/', '='}
    COMPLEX_INDICATORS = {'compare', 'between', 'relationship', 'correlation', 'difference'}
    AMBIGUOUS_TERMS = {
        'python': ['programming language', 'snake'],
        'java': ['programming language', 'coffee', 'island'],
        'ruby': ['programming language', 'gemstone'],
    }
    STOP_WORDS = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
                 'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
                 'that', 'the', 'to', 'was', 'were', 'will', 'with'}

    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a search query for suitability and complexity.

        Args:
            query: The search query to analyze

        Returns:
            QueryAnalysis object containing analysis results

        Raises:
            ValueError: If query is empty or too long
        """
        # Validate query
        if not query or query.isspace():
            raise ValueError("Empty query")
        if len(query) > self.MAX_QUERY_LENGTH:
            raise ValueError("Query too long")

        query = query.strip()

        # Check if query is unsuitable (e.g., basic arithmetic)
        if self._is_arithmetic_query(query):
            return QueryAnalysis(
                is_suitable_for_search=False,
                search_string=query,
                complexity="basic",
                reason_unsuitable="basic arithmetic query"
            )

        # Determine complexity
        complexity = self._determine_complexity(query)

        # Check for ambiguity
        is_ambiguous = self._is_ambiguous(query)
        possible_interpretations = self._get_possible_interpretations(query) if is_ambiguous else []

        # Generate sub-queries for complex queries
        sub_queries = self._generate_sub_queries(query) if complexity == "complex" else []

        return QueryAnalysis(
            is_suitable_for_search=True,
            search_string=query,
            complexity=complexity,
            is_ambiguous=is_ambiguous,
            possible_interpretations=possible_interpretations,
            sub_queries=sub_queries
        )

    def extract_search_terms(self, query: str) -> List[str]:
        """
        Extract key search terms from a query.

        Args:
            query: The search query

        Returns:
            List of extracted search terms
        """
        # Simple implementation - split on spaces and handle common phrases
        terms = []
        words = query.split()
        
        i = 0
        while i < len(words):
            # Check for common two-word phrases
            if i < len(words) - 1 and f"{words[i]} {words[i+1]}".lower() in {
                "machine learning", "artificial intelligence", "deep learning",
                "data science", "neural networks", "renewable energy"
            }:
                terms.append(f"{words[i]} {words[i+1]}")
                i += 2
            else:
                terms.append(words[i])
                i += 1

        return terms

    def craft_search_string(self, analysis: QueryAnalysis) -> str:
        """
        Create an optimized search string based on query analysis.

        Args:
            analysis: QueryAnalysis object containing analysis results

        Returns:
            Optimized search string
        """
        if not analysis.is_suitable_for_search:
            return analysis.search_string

        # For complex queries, combine sub-queries
        if analysis.complexity == "complex" and analysis.sub_queries:
            return " AND ".join(f"({q})" for q in analysis.sub_queries)

        # For ambiguous queries, use the first interpretation
        if analysis.is_ambiguous and analysis.possible_interpretations:
            return f"{analysis.search_string} {analysis.possible_interpretations[0]}"

        return analysis.search_string

    def _is_arithmetic_query(self, query: str) -> bool:
        """Check if query appears to be an arithmetic calculation."""
        return any(op in query for op in self.ARITHMETIC_OPERATORS)

    def _determine_complexity(self, query: str) -> str:
        """Determine query complexity based on indicators and length."""
        if any(indicator in query.lower() for indicator in self.COMPLEX_INDICATORS):
            return "complex"
        return "basic"

    def _is_ambiguous(self, query: str) -> bool:
        """Check if query contains ambiguous terms."""
        return any(term in query.lower() for term in self.AMBIGUOUS_TERMS)

    def _get_possible_interpretations(self, query: str) -> List[str]:
        """Get possible interpretations for ambiguous terms."""
        interpretations = []
        query_lower = query.lower()
        for term, meanings in self.AMBIGUOUS_TERMS.items():
            if term in query_lower:
                interpretations.extend(meanings)
        return interpretations

    def _generate_sub_queries(self, query: str) -> List[str]:
        """Generate sub-queries for complex queries."""
        # Simple implementation - split on common separators
        if "between" in query.lower():
            parts = query.lower().split("between")
            if len(parts) == 2 and "and" in parts[1]:
                subject = parts[0].strip()
                comparisons = parts[1].split("and")
                return [
                    f"{subject} {comp.strip()}"
                    for comp in comparisons
                ]
        return []

    def _optimize_query(self, query: str) -> str:
        """
        Perform basic query optimization.
        - Remove stop words
        - Remove extra whitespace
        - Handle special characters
        
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