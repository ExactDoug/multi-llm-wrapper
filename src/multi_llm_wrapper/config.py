from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

@dataclass
class ProviderConfig:
    """Base configuration for LLM providers"""
    api_key: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 2
    model_map: Dict[str, str] = field(default_factory=dict)

@dataclass
class GroqConfig(ProviderConfig):
    """Groq-specific configuration"""
    def __post_init__(self):
        self.model_map = {
            "mixtral-8x7b-32768": "groq/mixtral-8x7b-32768",
            "llama3-8b-8192": "groq/llama3-8b-8192"
        }

@dataclass
class PerplexityConfig(ProviderConfig):
    """Perplexity-specific configuration"""
    def __post_init__(self):
        self.model_map = {
            "sonar-small": "perplexity/llama-3.1-sonar-small-128k-online",
            "sonar-large": "perplexity/llama-3.1-sonar-large-128k-online",
            "sonar-huge": "perplexity/llama-3.1-sonar-huge-128k-online"
        }

@dataclass
class ProviderConfig:
    """Base configuration for LLM providers"""
    api_key: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 2
    model_map: Dict[str, str] = field(default_factory=dict)

@dataclass
class OpenAIConfig(ProviderConfig):
    """OpenAI-specific configuration"""
    organization_id: Optional[str] = None
    
    def __post_init__(self):
        self.model_map = {
            "gpt-4": "gpt-4",
            "gpt-3.5-turbo": "gpt-3.5-turbo"
        }

@dataclass
class AnthropicConfig(ProviderConfig):
    """Anthropic-specific configuration"""
    def __post_init__(self):
        self.model_map = {
            "claude-3-opus-20240229": "claude-3-opus-20240229",
            "claude-3-sonnet-20240229": "claude-3-sonnet-20240229"
        }

@dataclass
class WrapperConfig:
    """Main configuration class"""
    default_model: str = "claude-3-sonnet-20240229"
    default_provider: str = "anthropic"
    timeout_seconds: int = 30
    max_retries: int = 2
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    groq: GroqConfig = field(default_factory=GroqConfig)
    perplexity: PerplexityConfig = field(default_factory=PerplexityConfig)
    
    def __post_init__(self):
        """Load environment variables and validate configuration"""
        if not any([
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("OPENAI_API_KEY"),
            os.getenv("GROQ_API_KEY"),
            os.getenv("PERPLEXITY_API_KEY")
        ]):
            load_dotenv()
            
        # Load API keys from environment
        self.anthropic.api_key = self.anthropic.api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai.api_key = self.openai.api_key or os.getenv("OPENAI_API_KEY")
        self.openai.organization_id = self.openai.organization_id or os.getenv("OPENAI_ORG_ID")
        self.groq.api_key = self.groq.api_key or os.getenv("GROQ_API_KEY")
        self.perplexity.api_key = self.perplexity.api_key or os.getenv("PERPLEXITY_API_KEY")
        
        # Load global settings from environment if present
        self.default_model = os.getenv("DEFAULT_MODEL", self.default_model)
        self.default_provider = os.getenv("DEFAULT_PROVIDER", self.default_provider)
        self.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", str(self.timeout_seconds)))
        self.max_retries = int(os.getenv("MAX_RETRIES", str(self.max_retries)))
        
        # Validate required configuration based on provider
        provider_configs = {
            "anthropic": self.anthropic,
            "openai": self.openai,
            "groq": self.groq,
            "perplexity": self.perplexity
        }
        
        if not provider_configs[self.default_provider].api_key:
            raise ValueError(f"{self.default_provider.capitalize()} API key not found in environment or configuration")
            
    def get_provider_config(self, model: Optional[str] = None) -> tuple[str, ProviderConfig]:
        """Get provider and configuration based on model"""
        model = model or self.default_model
        
        # Check each provider's model map
        for provider, config in {
            "openai": self.openai,
            "anthropic": self.anthropic,
            "groq": self.groq,
            "perplexity": self.perplexity
        }.items():
            if model in config.model_map:
                return provider, config
                
        raise ValueError(f"Unsupported model: {model}")

# Create a function to get default config instead of a module-level instance
def get_default_config() -> WrapperConfig:
    return WrapperConfig()