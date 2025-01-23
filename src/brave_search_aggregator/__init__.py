"""
Brave Search Knowledge Aggregator package.

This package provides components for analyzing queries, fetching search results,
and synthesizing knowledge from web content.
"""

__version__ = "0.1.0"

from .analyzer import QueryAnalyzer, QueryAnalysis
from .fetcher import ContentFetcher, BraveSearchClient
from .synthesizer import KnowledgeSynthesizer
from .utils import Config

__all__ = [
    'QueryAnalyzer',
    'QueryAnalysis',
    'ContentFetcher',
    'BraveSearchClient',
    'KnowledgeSynthesizer',
    'Config',
]