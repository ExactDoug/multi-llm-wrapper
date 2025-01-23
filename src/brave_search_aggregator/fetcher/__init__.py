"""
Fetcher package for retrieving search results and content.
"""
from .brave_client import BraveSearchClient

class ContentFetcher:
    """Fetches and processes search results and web content."""
    pass

__all__ = ['BraveSearchClient', 'ContentFetcher']