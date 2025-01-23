import pytest
from src.multi_llm_wrapper.config import (
    WrapperConfig, OpenAIConfig, AnthropicConfig, GroqProxyConfig,
    GroqConfig, PerplexityConfig, GeminiConfig
)
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from multi_llm_wrapper import LLMWrapper
from multi_llm_wrapper.config import WrapperConfig, get_default_config
from dataclasses import dataclass

# Test API key
TEST_API_KEY = "test_api_key_12345"

def create_mock_error(error_type="timeout", message="Request timed out"):
    """Create a mock error response"""
    if error_type == "timeout":
        return TimeoutError(message)
    elif error_type == "validation_error":
        return ValueError(message)
    else:
        return Exception(message)

def create_test_config():
    """Factory function to create test configuration"""
    config = WrapperConfig()
    config.default_model = "gpt-4"
    config.default_provider = "openai"
    config.timeout_seconds = 30
    config.max_retries = 2
    
    # Initialize provider configs
    config.openai = OpenAIConfig(
        api_key="test-openai-key",
        organization_id="test-org-id",
        timeout_seconds=30,
        max_retries=2
    )
    config.anthropic = AnthropicConfig(
        api_key="test-anthropic-key",
        timeout_seconds=30,
        max_retries=2
    )
    config.groq = GroqConfig(
        api_key="test-groq-key",
        timeout_seconds=30,
        max_retries=2
    )
    config.groq_proxy = GroqProxyConfig(
        api_key="test-groq-proxy-key",
        base_url="http://localhost:8000",
        timeout_seconds=30,
        max_retries=2
    )
    config.perplexity = PerplexityConfig(
        api_key="test-perplexity-key",
        timeout_seconds=30,
        max_retries=2
    )
    config.gemini = GeminiConfig(
        api_key="test-gemini-key",
        timeout_seconds=30,
        max_retries=2
    )
    return config

@pytest.fixture
def test_config():
    """Fixture to provide a test configuration"""
    return create_test_config()

@pytest.fixture
def mock_env():
    """Fixture to mock environment variables"""
    original_env = dict(os.environ)
    mock_env = {
        'OPENAI_API_KEY': 'test-openai-key',
        'OPENAI_ORG_ID': 'test-org-id',
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'DEFAULT_MODEL': 'gpt-4',
        'DEFAULT_PROVIDER': 'openai',
        'TIMEOUT_SECONDS': '30',
        'MAX_RETRIES': '2'
    }
    os.environ.clear()
    os.environ.update(mock_env)
    yield
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def base_config():
    """Base configuration without environment loading"""
    return {
        "default_model": "gpt-4",
        "default_provider": "openai",
        "timeout_seconds": 30,
        "max_retries": 2,
        "openai": {
            "api_key": "test-openai-key",
            "organization_id": "test-org-id"
        },
        "anthropic": {
            "api_key": "test-anthropic-key"
        }
    }

@pytest.fixture(autouse=True)
def mock_llm_calls(monkeypatch):
    """Mock all LLM API calls at both SDK and HTTP levels"""
    def create_openai_response(content="Test response", model="gpt-4"):
        return {
            "choices": [{
                "message": {"content": content, "role": "assistant"},
                "delta": {"content": content, "role": "assistant"}
            }],
            "model": model,
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 5,
                "total_tokens": 10
            }
        }

    def create_anthropic_response(content="Test response", model="claude-3-sonnet-20240229"):
        return {
            "content": [{"text": content}],
            "model": model,
            "usage": {
                "input_tokens": 5,
                "output_tokens": 5
            }
        }

    def create_groq_response(content="Test response", model="llama3-70b-8192"):
        return {
            "choices": [{
                "message": {"content": content, "role": "assistant"},
                "delta": {"content": content, "role": "assistant"}
            }],
            "model": model,
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 5,
                "total_tokens": 10
            }
        }

    async def mock_http_request(*args, **kwargs):
        url = str(kwargs.get('url', ''))
        messages = kwargs.get('json', {}).get('messages', [{}])
        content = messages[0].get('content', '') if messages else ''
        model = kwargs.get('json', {}).get('model', 'gpt-4')

        # Handle error cases
        if content == 'This should timeout':
            raise TimeoutError("Request timed out")
        if content == '':
            raise ValueError("Prompt cannot be empty")
        if model == 'invalid-model-name':
            raise ValueError("Unsupported model")

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        # Provider-specific responses
        if 'api.openai.com' in url:
            mock_resp.json = lambda: create_openai_response(content="Test response", model=model)
        elif 'api.anthropic.com' in url:
            mock_resp.json = lambda: create_anthropic_response(content="Test response", model=model)
        elif 'api.groq.com' in url or 'localhost:8000' in url:
            mock_resp.json = lambda: create_groq_response(content="Test response", model=model)
        else:
            # Default to OpenAI format for unknown providers
            mock_resp.json = lambda: create_openai_response(content="Test response", model=model)

        return mock_resp

    async def mock_litellm_completion(*args, **kwargs):
        messages = kwargs.get('messages', [{}])
        content = messages[0].get('content', '') if messages else ''
        model = kwargs.get('model', 'gpt-4')
        provider = kwargs.get('provider', 'openai')

        # Handle error cases
        if content == 'This should timeout':
            raise TimeoutError("Request timed out")
        if content == '':
            raise ValueError("Prompt cannot be empty")
        if model == 'invalid-model-name':
            raise ValueError("Unsupported model")

        mock_resp = MagicMock()
        
        # Provider-specific response structures
        if provider == 'anthropic':
            mock_resp.choices = [
                MagicMock(
                    message=MagicMock(content="Test response", role="assistant"),
                    delta=MagicMock(content="Test response", role="assistant")
                )
            ]
            mock_resp.usage = MagicMock(
                input_tokens=5,
                output_tokens=5
            )
        else:
            # OpenAI-compatible format for other providers
            mock_resp.choices = [
                MagicMock(
                    message=MagicMock(content="Test response", role="assistant"),
                    delta=MagicMock(content="Test response", role="assistant")
                )
            ]
            mock_resp.usage = MagicMock(
                prompt_tokens=5,
                completion_tokens=5,
                total_tokens=10
            )
        
        mock_resp.model = model
        return mock_resp

    # Patch both HTTP and SDK levels
    monkeypatch.setattr("httpx.AsyncClient.post", AsyncMock(side_effect=mock_http_request))
    monkeypatch.setattr("litellm.acompletion", AsyncMock(side_effect=mock_litellm_completion))

# Basic query tests
@pytest.mark.asyncio
async def test_basic_query(test_config):
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("Test prompt")
    assert response["status"] == "success"
    assert response["content"] == "Test response"
    assert response["model"] == "gpt-4"

@pytest.mark.asyncio
async def test_error_handling(test_config):
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("", model="invalid-model")
    assert response["status"] == "error"
    assert response["error"] is not None
    assert response["error_type"] == "validation_error"

@pytest.mark.asyncio
async def test_wrapper_configuration(test_config):
    wrapper = LLMWrapper(config=test_config)
    assert isinstance(wrapper.config, WrapperConfig)
    assert wrapper.config.openai.api_key == "test-openai-key"
    assert wrapper.config.openai.organization_id == "test-org-id"

@pytest.mark.asyncio
async def test_wrapper_comprehensive(test_config):
    wrapper = LLMWrapper(config=test_config)
    assert isinstance(wrapper.config, WrapperConfig)
    assert wrapper.config.default_model == "gpt-4"
    assert wrapper.config.timeout_seconds == 30
    assert wrapper.config.openai.api_key == "test-openai-key"

@pytest.mark.asyncio
async def test_successful_query(test_config):
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("Tell me a joke")
    assert response["status"] == "success"
    assert response["content"] == "Test response"
    assert response["model"] == "gpt-4"

@pytest.mark.asyncio
async def test_query_timeout(test_config):
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("This should timeout")
    assert response["status"] == "error"
    assert response["error_type"] == "timeout"

@pytest.mark.asyncio
async def test_default_config(test_config):
    wrapper = LLMWrapper(config=test_config)
    assert wrapper.config.default_model == "gpt-4"
    assert wrapper.config.default_provider == "openai"
    assert wrapper.config.timeout_seconds == 30
    assert wrapper.config.max_retries == 2
    assert wrapper.config.openai.api_key == "test-openai-key"

@pytest.mark.asyncio
async def test_custom_config():
    config = create_test_config()
    config.default_model = "gpt-4"
    config.default_provider = "openai"
    wrapper = LLMWrapper(config=config)
    assert wrapper.config.default_model == "gpt-4"
    assert wrapper.config.openai.api_key == "test-openai-key"

@pytest.mark.asyncio
async def test_response_format_validation(test_config):
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("A simple question")
    assert isinstance(response, dict)
    assert all(key in response for key in ["status", "content", "model", "provider"])
    assert response["status"] == "success"
    assert response["content"] == "Test response"

@pytest.mark.asyncio
async def test_empty_prompt(test_config):
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("")
    assert response["status"] == "error"
    assert response["error_type"] == "validation_error"

@pytest.mark.asyncio
async def test_invalid_model(test_config):
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("Test prompt", model="invalid-model-name")
    assert response["status"] == "error"
    assert response["error_type"] == "validation_error"

@pytest.mark.asyncio
async def test_missing_api_key():
    """Test initialization with missing provider API keys"""
    config = create_test_config()
    config.openai.api_key = None
    
    with pytest.raises(ValueError) as exc_info:
        LLMWrapper(config=config)
    assert "Openai API key not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_groq_proxy_query(test_config):
    test_config.default_model = "llama3-70b-8192"
    test_config.default_provider = "groq_proxy"
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("Test Groq query")
    assert response["status"] == "success"
    assert response["content"] == "Test response"
    assert response["model"] == "llama3-70b-8192"

@pytest.mark.asyncio
async def test_config_copy():
    """Test the WrapperConfig copy method"""
    config = create_test_config()
    config.openai.api_key = "test-key-1"
    config.anthropic.api_key = "test-key-2"
    
    # Create a copy
    copied_config = config.copy()
    
    # Verify it's a different instance
    assert id(config) != id(copied_config)
    
    # Verify all attributes are copied correctly
    assert copied_config.default_model == config.default_model
    assert copied_config.default_provider == config.default_provider
    assert copied_config.timeout_seconds == config.timeout_seconds
    assert copied_config.max_retries == config.max_retries
    
    # Verify provider configs are deep copied
    assert id(config.openai) != id(copied_config.openai)
    assert id(config.anthropic) != id(copied_config.anthropic)
    assert copied_config.openai.api_key == config.openai.api_key
    assert copied_config.anthropic.api_key == config.anthropic.api_key
    
    # Verify modifying copy doesn't affect original
    copied_config.default_model = "different-model"
    copied_config.openai.api_key = "different-key"
    assert config.default_model == "gpt-4"
    assert config.openai.api_key == "test-key-1"

@pytest.mark.asyncio
async def test_provider_selection_priority(test_config):
    """Test the provider selection priority order"""
    # Test explicit provider prefix takes precedence
    provider, _ = test_config.get_provider_config("openai/gpt-4")
    assert provider == "openai"
    
    provider, _ = test_config.get_provider_config("anthropic/claude-3")
    assert provider == "anthropic"
    
    # Test model map priority order
    test_config.openai.model_map["shared-model"] = "actual-model"
    test_config.anthropic.model_map["shared-model"] = "actual-model"
    
    provider, _ = test_config.get_provider_config("shared-model")
    assert provider == "openai"  # OpenAI should be selected due to priority

@pytest.mark.asyncio
async def test_provider_selection_errors(test_config):
    """Test error cases in provider selection"""
    # Test invalid model name
    with pytest.raises(ValueError) as exc_info:
        test_config.get_provider_config("nonexistent-model")
    assert "Unsupported model" in str(exc_info.value)
    
    # Test empty model name defaults to config default
    provider, _ = test_config.get_provider_config("")
    assert provider == test_config.default_provider

@pytest.mark.asyncio
async def test_anthropic_query(test_config):
    """Test Anthropic-specific query handling"""
    test_config.default_model = "claude-3-sonnet-20240229"
    test_config.default_provider = "anthropic"
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("Test Anthropic query")
    assert response["status"] == "success"
    assert response["content"] == "Test response"
    assert response["model"] == "claude-3-sonnet-20240229"
    assert response["provider"] == "anthropic"

@pytest.mark.asyncio
async def test_provider_response_formats(test_config):
    """Test different provider response formats are handled correctly"""
    wrapper = LLMWrapper(config=test_config)
    
    # Test OpenAI format
    response = await wrapper.query("Test OpenAI", model="openai/gpt-4")
    assert response["status"] == "success"
    assert response["provider"] == "openai"
    
    # Test Anthropic format
    response = await wrapper.query("Test Anthropic", model="anthropic/claude-3")
    assert response["status"] == "success"
    assert response["provider"] == "anthropic"
    
    # Test Groq format
    response = await wrapper.query("Test Groq", model="llama3-70b-8192")
    assert response["status"] == "success"
    assert response["provider"] == "groq"