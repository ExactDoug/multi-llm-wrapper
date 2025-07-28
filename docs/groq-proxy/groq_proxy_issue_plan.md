# Groq Proxy Issue Plan

## Objective
To resolve the recurring issue with the `groq_proxy` provider in the `multi_llm_wrapper` project.

## Analysis
### Current State
1. **Wrapper Configuration (`config.py`)**:
   - The `WrapperConfig` class initializes various provider configurations, including `groq_proxy`.
   - The `get_provider_config` method is responsible for determining the provider and configuration based on the model name.

2. **Wrapper Implementation (`wrapper.py`)**:
   - The `LLMWrapper` class handles queries to different LLM providers.
   - The `query` method determines the provider and configuration based on the model name and handles the request accordingly.

### Issue
- The `groq_proxy` provider is not being recognized correctly, leading to an `Unsupported provider` error.

## Plan
### Step 1: Update `config.py`
1. **Ensure `groq_proxy` is correctly recognized**:
   - Update the `WrapperConfig` class to correctly handle the `groq_proxy` provider.
   - Ensure the `get_provider_config` method correctly maps the `groq_proxy` provider.

### Step 2: Update `wrapper.py`
1. **Ensure `groq_proxy` is correctly handled**:
   - Update the `query` method to correctly handle the `groq_proxy` provider.
   - Ensure the `groq_proxy` endpoint correctly handles the `groq` provider while maintaining the abstraction layer for other providers.

### Step 3: Verify Changes
1. **Run Tests**:
   - Execute the `test_groq_proxy.py` script to verify the changes.
   - Ensure the `groq_proxy` provider is correctly recognized and handled.

## Detailed Changes

### `config.py`
```python
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import os
from dotenv import load_dotenv
from .config_types import BraveSearchConfig as BraveConfig

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
            "mistral-saba-24b": "groq/mistral-saba-24b",
            "llama3-8b-8192": "groq/llama3-8b-8192"
        }

@dataclass
class PerplexityConfig(ProviderConfig):
    """Perplexity-specific configuration"""
    def __post_init__(self):
        self.model_map = {
            "sonar": "perplexity/sonar",
            "sonar-pro": "perplexity/sonar-pro",
            "sonar-huge": "perplexity/llama-3.1-sonar-huge-128k-online"
        }

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
class GeminiConfig(ProviderConfig):
    """Gemini-specific configuration"""
    def __post_init__(self):
        self.model_map = {
            "gemini-1.5-flash": "gemini/gemini-1.5-flash",
            "gemini-2.0-experimental": "gemini/gemini-2.0-experimental"
        }

@dataclass
class GroqProxyConfig(ProviderConfig):
    """Configuration for the Groq proxy server"""
    base_url: str = "http://localhost:8000"  # Default proxy URL
    def __post_init__(self):
        self.model_map = {
            "llama2-70b-8192": "groq/llama2-70b-8192", # Maps internal model name to proxy's expected model name, can be the same
            "deepseek-r1-distill-llama-70b": "groq/deepseek-r1-distill-llama-70b"
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
    groq_proxy: GroqProxyConfig = field(default_factory=GroqProxyConfig)
    perplexity: PerplexityConfig = field(default_factory=PerplexityConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    brave_search: BraveConfig = field(default_factory=lambda: BraveConfig(api_key=None))

    def __post_init__(self):
        """Load environment variables and validate configuration"""
        if not any([
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("OPENAI_API_KEY"),
            os.getenv("GROQ_API_KEY"),
            os.getenv("PERPLEXITY_API_KEY"),
            os.getenv("GEMINI_API_KEY"),
            os.getenv("BRAVE_SEARCH_API_KEY")
        ]):
            load_dotenv()

        # Load API keys from environment
        self.anthropic.api_key = self.anthropic.api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai.api_key = self.openai.api_key or os.getenv("OPENAI_API_KEY")
        self.openai.organization_id = self.openai.organization_id or os.getenv("OPENAI_ORG_ID")
        self.groq.api_key = self.groq.api_key or os.getenv("GROQ_API_KEY")
        self.perplexity.api_key = self.perplexity.api_key or os.getenv("PERPLEXITY_API_KEY")
        self.gemini.api_key = self.gemini.api_key or os.getenv("GEMINI_API_KEY")
        self.brave_search.api_key = self.brave_search.api_key or os.getenv("BRAVE_SEARCH_API_KEY")

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
            "groq_proxy": self.groq_proxy,
            "perplexity": self.perplexity,
            "gemini": self.gemini,
            "brave_search": self.brave_search
        }

        if not provider_configs[self.default_provider].api_key:
            raise ValueError(f"{self.default_provider.capitalize()} API key not found in environment or configuration")

    def copy(self):
        """Create a deep copy of the configuration"""
        return WrapperConfig(
            default_model=self.default_model,
            default_provider=self.default_provider,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
            anthropic=AnthropicConfig(**vars(self.anthropic)),
            openai=OpenAIConfig(**vars(self.openai)),
            groq=GroqConfig(**vars(self.groq)),
            groq_proxy=GroqProxyConfig(**vars(self.groq_proxy)),
            perplexity=PerplexityConfig(**vars(self.perplexity)),
            gemini=GeminiConfig(**vars(self.gemini)),
            brave_search=BraveConfig(**vars(self.brave_search))
        )

    def get_provider_config(self, model: Optional[str] = None) -> tuple[str, ProviderConfig]:
        """Get provider and configuration based on model"""
        model = model or self.default_model

        # First check explicit provider prefixes
        provider_prefixes = {
            "openai/": ("openai", self.openai),
            "anthropic/": ("anthropic", self.anthropic),
            "groq/": ("groq", self.groq),
            "groq_proxy/": ("groq_proxy", self.groq_proxy),
            "perplexity/": ("perplexity", self.perplexity),
            "gemini/": ("gemini", self.gemini),
            "brave_search/": ("brave_search", self.brave_search)
        }

        for prefix, (provider, config) in provider_prefixes.items():
            if model.startswith(prefix):
                return provider, config

        # Then check model maps in priority order
        provider_configs = [
            ("openai", self.openai),
            ("anthropic", self.anthropic),
            ("groq", self.groq),
            ("groq_proxy", self.groq_proxy),
            ("perplexity", self.perplexity),
            ("gemini", self.gemini),
            ("brave_search", self.brave_search)
        ]

        for provider, config in provider_configs:
            if model in config.model_map:
                return provider, config

        raise ValueError(f"Unsupported model: {model}")

# Create a function to get default config instead of a module-level instance
def get_default_config() -> WrapperConfig:
    return WrapperConfig()
```

### `wrapper.py`
```python
from typing import Dict, Any, Optional, AsyncGenerator, Union
from litellm import acompletion
import logging
import time
from dotenv import load_dotenv
from .config import WrapperConfig, get_default_config

# Load environment variables at module level
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMWrapper:
    """
    LLM wrapper implementation with support for multiple providers.
    """
    def __init__(self, config: Optional[WrapperConfig] = None):
        """Initialize wrapper with configuration"""
        self.config = config or get_default_config()

        # Initialize usage tracking
        self.usage_stats = {
            "openai": {"requests": 0, "tokens": 0},
            "anthropic": {"requests": 0, "tokens": 0},
            "groq": {"requests": 0, "tokens": 0},
            "perplexity": {"requests": 0, "tokens": 0},
            "gemini": {"requests": 0, "tokens": 0},
            "brave_search": {"requests": 0, "results": 0}
        }

        # Track response times for monitoring
        self.response_times = {
            "openai": [],
            "anthropic": [],
            "groq": [],
            "perplexity": [],
            "gemini": [],
            "brave_search": []
        }

        # Initialize Brave Search client as None - will be created lazily when needed
        self._brave_search = None

    @property
    def brave_search(self):
        """Lazy initialization of Brave Search client"""
        if self._brave_search is None and self.config.brave_search.api_key:
            from .web.brave_search import BraveSearchClient
            self._brave_search = BraveSearchClient(self.config.brave_search)
        return self._brave_search

    async def enhance_with_search(
        self,
        prompt: str,
        search_results_count: int = 5
    ) -> str:
        """
        Enhance prompt with Brave Search results

        Args:
            prompt: Original prompt
            search_results_count: Number of search results to include

        Returns:
            Enhanced prompt with search context
        """
        if not self.brave_search:
            return prompt

        try:
            # Execute search
            results = await self.brave_search.search(prompt, search_results_count)

            # Track usage
            self.usage_stats["brave_search"]["requests"] += 1
            self.usage_stats["brave_search"]["results"] += len(results)

            # Format results as context
            if results:
                context = "\nRelevant search results:\n"
                for i, result in enumerate(results, 1):
                    context += f"\n{i}. {result.title}\n"
                    context += f"URL: {result.url}\n"
                    context += f"Description: {result.description}\n"

                # Combine context with original prompt
                enhanced_prompt = f"{context}\n\nBased on the above information, {prompt}"
                return enhanced_prompt

        except Exception as e:
            logger.error(f"Search enhancement failed: {str(e)}")

        return prompt

    async def query(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        enhance_with_search: bool = False,
        search_results_count: int = 5,
        **kwargs: Any
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Send a query to the specified LLM provider with optional streaming support

        Args:
            prompt: The input prompt
            model: Optional model override
            stream: Whether to stream the response
            enhance_with_search: Whether to enhance the prompt with Brave Search results
            search_results_count: Number of search results to include when enhancing
            **kwargs: Additional arguments passed to the provider

        Returns:
            Either a complete response dict or an async generator of response chunks
        """
        provider = None
        start_time = None

        try:
            if not prompt:
                raise ValueError("Prompt cannot be empty")

            # Enhance prompt with search results if requested
            if enhance_with_search:
                prompt = await self.enhance_with_search(prompt, search_results_count)

            # Get provider and configuration based on model
            provider, provider_config = self.config.get_provider_config(model)
            logging.debug(f"Provider: {provider}, Provider Config: {provider_config}")
            if provider != "groq":
                raise ValueError(f"Unsupported provider: {provider}")

            # Ensure request_kwargs is initialized
            request_kwargs = {
                "model": f"groq/{model}",  # Prefix model name with provider
                "messages": [{"role": "user", "content": prompt}],
                "timeout": kwargs.pop("timeout", self.config.timeout_seconds),
                "api_key": provider_config.api_key,  # Pass API key directly for all providers
                "stream": stream,
                **kwargs
            }

            # Explicitly handle the groq provider
            if provider == "groq":
                logging.debug("Using groq provider")
                response = await acompletion(
                    base_url=provider_config.base_url,
                    **request_kwargs
                )
                return self._format_complete_response(
                    response=response,
                    provider=provider,
                    model=model,
                    start_time=start_time
                )

            model = model or self.config.default_model

            # Get the actual model name from the provider's model map
            model = provider_config.model_map.get(model, model)

            # Track request
            self.usage_stats[provider]["requests"] += 1
            start_time = time.time()

            # Prepare request kwargs
            request_kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "timeout": kwargs.pop("timeout", self.config.timeout_seconds),
                "api_key": provider_config.api_key,  # Pass API key directly for all providers
                "stream": stream,
                **kwargs
            }

            # Add provider-specific configuration
            if provider == "openai" and provider_config.organization_id:
                request_kwargs["headers"] = {
                    "OpenAI-Organization": provider_config.organization_id
                }
            elif provider == "gemini":
                # Gemini requires the API key to be passed as google_api_key
                request_kwargs["google_api_key"] = provider_config.api_key
                # Remove the default api_key parameter
                request_kwargs.pop("api_key", None)
            elif provider == "groq":
                # Use litellm's acompletion with the proxy's base URL
                response = await acompletion(
                    base_url=provider_config.base_url,
                    **request_kwargs
                )
                return self._format_complete_response(
                    response=response,
                    provider=provider,
                    model=model,
                    start_time=start_time
                )

            logger.info(f"Sending query to {provider} model: {model} (streaming: {stream})")

            if stream:
                return self._handle_streaming_response(
                    provider=provider,
                    model=model,
                    start_time=start_time,
                    request_kwargs=request_kwargs
                )

            # Non-streaming response using acompletion
            response = await acompletion(**request_kwargs)
            return self._format_complete_response(
                response=response,
                provider=provider,
                model=model,
                start_time=start_time
            )
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return self._format_error_response(
                error=str(e),
                error_type="validation_error",
                model=model if 'model' in locals() else None,
                provider=provider if 'provider' in locals() else None
            )

        except TimeoutError as e:
            logger.error(f"Request timed out: {str(e)}")
            return self._format_error_response(
                error="Request timed out",
                error_type="timeout",
                model=model if 'model' in locals() else None,
                provider=provider if 'provider' in locals() else None
            )

        except Exception as e:
            logger.error(f"Query failed: {type(e).__name__}: {str(e)}")
            error_type = "general_error"

            # Map litellm errors to our error types
            error_name = type(e).__name__
            if "TimeoutError" in error_name:
                error_type = "timeout"
            elif "AuthenticationError" in error_name:
                error_type = "auth_error"
            elif "RateLimitError" in error_name:
                error_type = "rate_limit"
            elif "InvalidRequestError" in error_name:
                error_type = "validation_error"

            return self._format_error_response(
                error=str(e),
                error_type=error_type,
                model=model if 'model' in locals() else None,
                provider=provider if 'provider' in locals() else None
            )

    async def _handle_streaming_response(
        self,
        provider: str,
        model: str,
        start_time: float,
        request_kwargs: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle streaming response from provider"""
        try:
            # Get the async generator from acompletion
            stream = await acompletion(**request_kwargs)

            # Now iterate over the chunks
            async for chunk in stream:
                try:
                    # Extract content from chunk based on provider
                    content = None
                    if hasattr(chunk, 'choices') and chunk.choices:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'text'):  # Anthropic format
                            content = delta.text
                        elif hasattr(delta, 'content'):  # OpenAI format
                            content = delta.content
                        elif hasattr(delta, 'role') and delta.role == 'assistant':
                            continue  # Skip role messages

                    # Only yield if we have content
                    if content:
                        # Track token usage if available
                        if hasattr(chunk, "usage") and chunk.usage:
                            self.usage_stats[provider]["tokens"] += getattr(chunk.usage, "total_tokens", 0)

                        yield {
                            "content": content,
                            "model": model,
                            "provider": provider,
                            "metadata": {
                                "response_time": time.time() - start_time,
                                "chunk": True,
                                "usage": chunk.usage if hasattr(chunk, "usage") else None
                            },
                            "status": "success"
                        }
                except Exception as e:
                    # Skip malformed chunks
                    continue

        except Exception as e:
            yield self._format_error_response(
                error=str(e),
                error_type="streaming_error",
                model=model,
                provider=provider
            )

    def _format_complete_response(
        self,
        response: Any,
        provider: str,
        model: str,
        start_time: float
    ) -> Dict[str, Any]:
        """Format a complete (non-streaming) response"""
        elapsed_time = time.time() - start_time
        self.response_times[provider].append(elapsed_time)

        # Track token usage
        if hasattr(response, "usage"):
            self.usage_stats[provider]["tokens"] += getattr(response.usage, "total_tokens", 0)

        # Extract response content
        response_content = response.choices[0].message.content if response.choices else None
        response_usage = response.usage if hasattr(response, "usage") else None

        return {
            "content": response_content,
            "model": model,
            "provider": provider,
            "metadata": {
                "response_time": elapsed_time,
                "usage": response_usage,
                "chunk": False
            },
            "status": "success"
        }

    def _format_error_response(
        self,
        error: str,
        error_type: str,
        model: Optional[str],
        provider: Optional[str]
    ) -> Dict[str, Any]:
        """Format an error response"""
        return {
            "content": None,
            "model": model,
            "provider": provider,
            "error": error,
            "status": "error",
            "error_type": error_type
        }

    def get_usage_stats(self) -> Dict[str, Dict[str, int]]:
        """Get current usage statistics"""
        return self.usage_stats

    def get_average_response_time(self, provider: str) -> float:
        """Get average response time for a provider"""
        times = self.response_times.get(provider, [])
        return sum(times) / len(times) if times else 0.0

    async def cleanup(self):
        """Cleanup resources"""
        if self._brave_search:
            await self._brave_search.close()
```

## Verification
1. **Run Tests**:
   - Execute the `test_groq_proxy.py` script to verify the changes.
   - Ensure the `groq_proxy` provider is correctly recognized and handled.

## Conclusion
By following this plan, we should be able to resolve the recurring issue with the `groq_proxy` provider in the `multi_llm_wrapper` project.