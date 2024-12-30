import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from multi_llm_wrapper import LLMWrapper
from multi_llm_wrapper.config import WrapperConfig, get_default_config
from dataclasses import dataclass

# Test API key
TEST_API_KEY = "test_api_key_12345"

def create_mock_response():
    """Create a mock response object with the expected structure"""
    mock_message = MagicMock()
    mock_message.content = "Test response"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response

@dataclass
class TestConfig(WrapperConfig):
    """Test configuration class without any environment loading"""
    api_key: str = None

@pytest.fixture
def mock_env():
    """Fixture to mock environment variables"""
    original_env = dict(os.environ)
    mock_env = {
        'ANTHROPIC_API_KEY': TEST_API_KEY,
        'DEFAULT_MODEL': 'claude-3-sonnet-20240229',
        'DEFAULT_PROVIDER': 'anthropic',
        'TIMEOUT_SECONDS': '30',
        'MAX_RETRIES': '2'
    }
    os.environ.clear()
    os.environ.update(mock_env)
    yield
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def test_config():
    """Fixture to provide a test configuration"""
    return TestConfig(api_key=TEST_API_KEY)

@pytest.fixture
def mock_completion():
    """Fixture to mock litellm completion with async support"""
    async def mock_async_completion(*args, **kwargs):
        return create_mock_response()
        
    mock = AsyncMock(side_effect=mock_async_completion)
    with patch('multi_llm_wrapper.wrapper.completion', mock):
        yield mock

# Basic query tests
@pytest.mark.asyncio
async def test_basic_query(test_config, mock_completion):
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("Test prompt")
    assert response["status"] == "success"
    assert response["content"] == "Test response"
    assert response["model"] == "claude-3-sonnet-20240229"
    mock_completion.assert_called_once()

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
    assert isinstance(wrapper.config, TestConfig)
    assert wrapper.config.api_key == TEST_API_KEY

@pytest.mark.asyncio
async def test_wrapper_comprehensive(test_config):
    wrapper = LLMWrapper(config=test_config)
    assert isinstance(wrapper.config, TestConfig)
    assert wrapper.config.default_model == "claude-3-sonnet-20240229"
    assert wrapper.config.timeout_seconds == 30
    assert wrapper.config.api_key == TEST_API_KEY

@pytest.mark.asyncio
async def test_successful_query(test_config, mock_completion):
    wrapper = LLMWrapper(config=test_config)
    response = await wrapper.query("Tell me a joke")
    assert response["status"] == "success"
    assert response["content"] == "Test response"
    mock_completion.assert_called_once()

@pytest.mark.asyncio
async def test_query_timeout(test_config):
    wrapper = LLMWrapper(config=test_config)

    async def mock_timeout(*args, **kwargs):
        await asyncio.sleep(0.1)  # Small delay to simulate processing
        raise TimeoutError("Request timed out")

    with patch('multi_llm_wrapper.wrapper.completion', AsyncMock(side_effect=mock_timeout)):
        response = await wrapper.query("This should timeout")
        assert response["status"] == "error"
        assert response["error_type"] == "timeout"

@pytest.mark.asyncio
async def test_default_config(test_config):
    wrapper = LLMWrapper(config=test_config)
    assert isinstance(wrapper.config, TestConfig)
    assert wrapper.config.default_model == "claude-3-sonnet-20240229"
    assert wrapper.config.default_provider == "anthropic"
    assert wrapper.config.timeout_seconds == 30
    assert wrapper.config.max_retries == 2
    assert wrapper.config.api_key == TEST_API_KEY

@pytest.mark.asyncio
async def test_custom_config():
    custom_config = TestConfig(
        default_model="gpt-4",
        api_key=TEST_API_KEY
    )
    wrapper = LLMWrapper(config=custom_config)
    assert wrapper.config.default_model == "gpt-4"
    assert wrapper.config.api_key == TEST_API_KEY

@pytest.mark.asyncio
async def test_response_format_validation(test_config, mock_completion):
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

@pytest.mark.asyncio
async def test_missing_api_key():
    # Test without any API key in environment or config
    with patch.dict('os.environ', {}, clear=True):  # Clear environment variables
        with patch('multi_llm_wrapper.config.load_dotenv'): # Prevent .env loading
            config = TestConfig()  # This will have api_key=None
            with pytest.raises(ValueError) as exc_info:
                wrapper = LLMWrapper(config=config)
    assert "API key not found" in str(exc_info.value)