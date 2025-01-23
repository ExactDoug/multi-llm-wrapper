from dataclasses import dataclass, field
from typing import Dict

@dataclass
class BraveSearchConfig:
    """Configuration for Brave Search integration"""
    api_key: str
    max_results_per_query: int = 10
    max_rate: int = 20  # queries per second
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 1
    model_map: Dict[str, str] = field(default_factory=lambda: {
        "brave-search": "brave_search/search",
        "brave-local": "brave_search/local"
    })