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
            "gemini": {"requests": 0, "tokens": 0}
        }
        
        # Track response times for monitoring
        self.response_times = {
            "openai": [],
            "anthropic": [],
            "groq": [],
            "perplexity": [],
            "gemini": []
        }
    
    async def query(
        self, 
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Send a query to the specified LLM provider with optional streaming support
        
        Args:
            prompt: The input prompt
            model: Optional model override
            stream: Whether to stream the response
            **kwargs: Additional arguments passed to the provider
            
        Returns:
            Either a complete response dict or an async generator of response chunks
        """
        provider = None
        start_time = None
        
        try:
            if not prompt:
                raise ValueError("Prompt cannot be empty")
            
            # Get provider and configuration based on model
            provider, provider_config = self.config.get_provider_config(model)
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
            return self._format_error_response(
                error=str(e),
                error_type="general_error",
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