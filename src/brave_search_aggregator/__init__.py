"""
Brave Search Knowledge Aggregator

A sophisticated component for the multi-llm-wrapper project that enhances search capabilities
by intelligently processing and synthesizing web search results.
"""

__version__ = "0.1.0"
__author__ = "Exact Technology Partners"
__email__ = "dmortensen@exactpartners.com"

from .analyzer import QueryAnalyzer
from .fetcher import ContentFetcher
from .synthesizer import KnowledgeSynthesizer

__all__ = ["QueryAnalyzer", "ContentFetcher", "KnowledgeSynthesizer"]