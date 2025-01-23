"""
Test-specific configuration for Brave Search Knowledge Aggregator.
"""
from typing import Dict, Any
import os
from pydantic import BaseModel, Field

class TestFeatureFlags(BaseModel):
    """Test-specific feature flag configuration."""
    advanced_synthesis: bool = Field(
        default=False,
        description="Enable advanced synthesis features"
    )
    parallel_processing: bool = Field(
        default=True,
        description="Enable parallel processing of search results"
    )
    moe_routing: bool = Field(
        default=False,
        description="Enable mixture of experts routing"
    )
    task_vectors: bool = Field(
        default=False,
        description="Enable task vector support"
    )
    slerp_merging: bool = Field(
        default=False,
        description="Enable SLERP-based vector merging"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "advanced_synthesis": False,
                    "parallel_processing": True,
                    "moe_routing": False,
                    "task_vectors": False,
                    "slerp_merging": False
                }
            ]
        }
    }

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
        return self.model_dump()

class TestServerConfig(BaseModel):
    """Test server configuration settings."""
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8001, description="Server port number")
    reload: bool = Field(default=True, description="Enable auto-reload on code changes")
    workers: int = Field(default=1, description="Number of worker processes")
    log_level: str = Field(default="debug", description="Logging level")
    
    # Brave Search API settings
    brave_api_key: str = Field(default="", description="Brave Search API key")
    max_results_per_query: int = Field(default=20, description="Maximum results per query")
    timeout_seconds: int = Field(default=30, description="API timeout in seconds")
    rate_limit: int = Field(default=20, description="API rate limit")

    # Feature flags
    features: TestFeatureFlags = Field(
        default_factory=TestFeatureFlags,
        description="Feature flag configuration"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "host": "0.0.0.0",
                    "port": 8001,
                    "reload": True,
                    "workers": 1,
                    "log_level": "debug",
                    "brave_api_key": "your-api-key-here",
                    "max_results_per_query": 20,
                    "timeout_seconds": 30,
                    "rate_limit": 20,
                    "features": {
                        "advanced_synthesis": False,
                        "parallel_processing": True,
                        "moe_routing": False,
                        "task_vectors": False,
                        "slerp_merging": False
                    }
                }
            ]
        }
    }

    @classmethod
    def from_env(cls) -> 'TestServerConfig':
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("TEST_SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("TEST_SERVER_PORT", "8001")),
            reload=os.getenv("TEST_SERVER_RELOAD", "true").lower() == "true",
            workers=int(os.getenv("TEST_SERVER_WORKERS", "1")),
            log_level=os.getenv("TEST_SERVER_LOG_LEVEL", "debug"),
            brave_api_key=os.getenv("BRAVE_API_KEY", ""),
            max_results_per_query=int(os.getenv("MAX_RESULTS_PER_QUERY", "20")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "30")),
            rate_limit=int(os.getenv("RATE_LIMIT", "20")),
            features=TestFeatureFlags.from_env()
        )

class TestLoggingConfig(BaseModel):
    """Test-specific logging configuration."""
    log_file: str = Field(default="test_server.log", description="Log file path")
    console_level: str = Field(default="INFO", description="Console logging level")
    file_level: str = Field(default="DEBUG", description="File logging level")
    
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

class TestMetricsConfig(BaseModel):
    """Test-specific metrics configuration."""
    enabled: bool = Field(default=True, description="Enable metrics collection")
    collection_interval: int = Field(default=10, description="Metrics collection interval in seconds")
    
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