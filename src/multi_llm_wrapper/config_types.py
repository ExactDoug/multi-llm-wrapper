from dataclasses import dataclass

@dataclass
class BraveSearchConfig:
    """Configuration for Brave Search integration"""
    api_key: str
    max_results_per_query: int = 10
    max_rate: int = 20  # queries per second
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 1