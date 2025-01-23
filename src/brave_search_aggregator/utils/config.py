"""Configuration management for Brave Search Aggregator."""
from dataclasses import dataclass

@dataclass
class Config:
    """Configuration settings."""
    brave_api_key: str
    max_results_per_query: int
    timeout_seconds: int
    rate_limit: int