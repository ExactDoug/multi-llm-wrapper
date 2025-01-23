"""
Brave Search API client implementation.
"""
import aiohttp
from ..utils.config import Config

class BraveSearchClient:
    """Client for interacting with Brave Search API."""
    
    def __init__(self, config: Config, session: aiohttp.ClientSession):
        """
        Initialize the Brave Search client.

        Args:
            config: Configuration settings
            session: aiohttp client session
        """
        self.config = config
        self.session = session
        self.base_url = "https://api.search.brave.com/res/v1"