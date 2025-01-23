"""
Test-specific configuration for Brave Search Knowledge Aggregator.
"""
from dataclasses import dataclass
from typing import Dict, Any
import os

@dataclass
class TestServerConfig:
    """Test server configuration settings."""
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8001
    reload: bool = True
    workers: int = 1
    log_level: str = "debug"
    
    # Brave Search API settings
    brave_api_key: str = ""
    max_results_per_query: int = 20
    timeout_seconds: int = 30
    rate_limit: int = 20
    
    @classmethod
    def from_env(cls) -> 'TestServerConfig':
        """Create configuration from environment variables."""
        return cls(
            # Server settings
            host=os.getenv("TEST_SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("TEST_SERVER_PORT", "8001")),
            reload=os.getenv("TEST_SERVER_RELOAD", "true").lower() == "true",
            workers=int(os.getenv("TEST_SERVER_WORKERS", "1")),
            log_level=os.getenv("TEST_SERVER_LOG_LEVEL", "debug"),
            
            # Brave Search API settings
            brave_api_key=os.getenv("BRAVE_API_KEY", ""),
            max_results_per_query=int(os.getenv("MAX_RESULTS_PER_QUERY", "20")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "30")),
            rate_limit=int(os.getenv("RATE_LIMIT", "20"))
        )

@dataclass
class TestLoggingConfig:
    """Test-specific logging configuration."""
    log_file: str = "test_server.log"
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    
    def get_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary."""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.console_level,
                    'formatter': 'detailed'
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'filename': self.log_file,
                    'level': self.file_level,
                    'formatter': 'detailed'
                }
            },
            'root': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG'
            }
        }

@dataclass
class TestFeatureFlags:
    """Test-specific feature flag configuration."""
    advanced_synthesis: bool = False
    parallel_processing: bool = True
    moe_routing: bool = False
    task_vectors: bool = False
    slerp_merging: bool = False
    
    @classmethod
    def from_env(cls) -> 'TestFeatureFlags':
        """Create feature flags from environment variables."""
        return cls(
            advanced_synthesis=os.getenv("FEATURE_ADVANCED_SYNTHESIS", "false").lower() == "true",
            parallel_processing=os.getenv("FEATURE_PARALLEL_PROCESSING", "true").lower() == "true",
            moe_routing=os.getenv("FEATURE_MOE_ROUTING", "false").lower() == "true",
            task_vectors=os.getenv("FEATURE_TASK_VECTORS", "false").lower() == "true",
            slerp_merging=os.getenv("FEATURE_SLERP_MERGING", "false").lower() == "true"
        )
    
    def get_enabled_features(self) -> Dict[str, bool]:
        """Get dictionary of enabled features."""
        return {
            'advanced_synthesis': self.advanced_synthesis,
            'parallel_processing': self.parallel_processing,
            'moe_routing': self.moe_routing,
            'task_vectors': self.task_vectors,
            'slerp_merging': self.slerp_merging
        }

@dataclass
class TestMetricsConfig:
    """Test-specific metrics configuration."""
    enabled: bool = True
    collection_interval: int = 10  # seconds
    
    def get_config(self) -> Dict[str, Any]:
        """Get metrics configuration dictionary."""
        return {
            'enabled': self.enabled,
            'collection_interval': self.collection_interval,
            'metrics': {
                'response_time': True,
                'error_rate': True,
                'api_quota': True,
                'memory_usage': True,
                'cpu_usage': True
            }
        }