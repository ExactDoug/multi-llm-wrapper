"""
Tests for the QueryAnalyzer component.
"""
import pytest
from brave_search_aggregator.analyzer.query_analyzer import QueryAnalyzer

@pytest.mark.unit
class TestQueryAnalyzer:
    """Test suite for QueryAnalyzer."""

    def test_analyze_query_basic(self, query_analyzer: QueryAnalyzer):
        """Test basic query analysis."""
        query = "latest developments in AI"
        analysis = query_analyzer.analyze_query(query)
        
        assert analysis is not None
        assert analysis.is_suitable_for_search
        assert analysis.search_string == query
        assert analysis.complexity == "basic"

    def test_analyze_query_complex(self, query_analyzer: QueryAnalyzer):
        """Test analysis of complex queries."""
        query = "compare renewable energy adoption rates between European and Asian countries in the last 5 years"
        analysis = query_analyzer.analyze_query(query)
        
        assert analysis is not None
        assert analysis.is_suitable_for_search
        assert analysis.complexity == "complex"
        assert len(analysis.sub_queries) > 1

    def test_analyze_query_ambiguous(self, query_analyzer: QueryAnalyzer):
        """Test analysis of ambiguous queries."""
        query = "python libraries"
        analysis = query_analyzer.analyze_query(query)
        
        assert analysis is not None
        assert analysis.is_suitable_for_search
        assert analysis.is_ambiguous
        assert len(analysis.possible_interpretations) > 1

    def test_analyze_query_unsuitable(self, query_analyzer: QueryAnalyzer):
        """Test analysis of unsuitable queries."""
        query = "what is 2+2"
        analysis = query_analyzer.analyze_query(query)
        
        assert analysis is not None
        assert not analysis.is_suitable_for_search
        assert analysis.reason_unsuitable == "basic arithmetic query"

    @pytest.mark.parametrize("query,expected_terms", [
        ("AI developments", ["AI", "developments"]),
        ("machine learning applications", ["machine learning", "applications"]),
        ("python programming tutorial", ["python", "programming", "tutorial"])
    ])
    def test_extract_search_terms(self, query_analyzer: QueryAnalyzer, query: str, expected_terms: list):
        """Test extraction of search terms from queries."""
        terms = query_analyzer.extract_search_terms(query)
        assert set(terms) == set(expected_terms)

    def test_craft_search_string_basic(self, query_analyzer: QueryAnalyzer):
        """Test creation of search strings for basic queries."""
        query = "AI developments"
        analysis = query_analyzer.analyze_query(query)
        search_string = query_analyzer.craft_search_string(analysis)
        
        assert isinstance(search_string, str)
        assert len(search_string) > 0
        assert "AI" in search_string
        assert "developments" in search_string

    def test_craft_search_string_complex(self, query_analyzer: QueryAnalyzer):
        """Test creation of search strings for complex queries."""
        query = "compare renewable energy adoption rates between European and Asian countries"
        analysis = query_analyzer.analyze_query(query)
        search_string = query_analyzer.craft_search_string(analysis)
        
        assert isinstance(search_string, str)
        assert len(search_string) > 0
        assert "renewable energy" in search_string
        assert "adoption rates" in search_string

    @pytest.mark.parametrize("query", [
        "",
        "   ",
        "\n\t"
    ])
    def test_analyze_query_empty(self, query_analyzer: QueryAnalyzer, query: str):
        """Test handling of empty or whitespace-only queries."""
        with pytest.raises(ValueError, match="Empty query"):
            query_analyzer.analyze_query(query)

    def test_analyze_query_too_long(self, query_analyzer: QueryAnalyzer):
        """Test handling of extremely long queries."""
        query = "test " * 1000
        with pytest.raises(ValueError, match="Query too long"):
            query_analyzer.analyze_query(query)