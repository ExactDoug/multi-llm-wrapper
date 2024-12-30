import pytest
from unittest.mock import patch, MagicMock
import os
from multi_llm_wrapper import LLMWrapper, WrapperConfig, OpenAIConfig

@pytest.fixture
async def mock_completion():
    """Mock the litellm completion function"""
    async def mock_async_completion(*args, **kwargs):
        await asyncio.sleep(0.01)  # Simulate a small delay
        return MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="Test response"
                    )
                )
            ],
            usage=MagicMock(
                total_tokens=10
            )
        )
    mock = AsyncMock(side_effect=mock_async_completion)
    with patch('multi_llm_wrapper.wrapper.completion', mock):
        yield mock

@pytest.fixture
def openai_config():
    """Create a test OpenAI configuration"""
    return WrapperConfig(
        default_model="gpt-4",
        default_provider="openai",
        openai=OpenAIConfig(
            api_key="test-openai-key",
            organization_id="test-org-id"
        )
    )

@pytest.mark.asyncio
async def test_openai_query(mock_completion, openai_config):
    """Test basic OpenAI query"""
    wrapper = LLMWrapper(config=openai_config)
    response = await wrapper.query("Test prompt")
    
    assert response["status"] == "success"
    assert response["provider"] == "openai"
    assert response["content"] == "Test response"
    
    # Verify API call
    mock_completion.assert_called_once()
    kwargs = mock_completion.call_args[1]
    assert kwargs["model"] == "gpt-4"
    assert kwargs["api_key"] == "test-openai-key"
    assert kwargs["headers"]["OpenAI-Organization"] == "test-org-id"

@pytest.mark.asyncio
async def test_openai_usage_tracking(mock_completion, openai_config):
    """Test usage tracking for OpenAI"""
    wrapper = LLMWrapper(config=openai_config)
    
    # Make multiple queries
    for _ in range(3):
        await wrapper.query("Test prompt")
    
    usage = wrapper.get_usage_stats()
    assert usage["openai"]["requests"] == 3
    assert usage["openai"]["tokens"] == 30  # 10 tokens per request

@pytest.mark.asyncio
async def test_openai_error_handling(openai_config):
    """Test OpenAI error handling"""
    with patch('multi_llm_wrapper.wrapper.completion', side_effect=Exception("API Error")):
        wrapper = LLMWrapper(config=openai_config)
        response = await wrapper.query("Test prompt")
        
        assert response["status"] == "error"
        assert "API Error" in response["error"]
        assert response["provider"] == "openai"

@pytest.mark.asyncio
async def test_response_time_tracking(mock_completion, openai_config):
    """Test response time tracking"""
    wrapper = LLMWrapper(config=openai_config)
    await wrapper.query("Test prompt")
    
    avg_time = wrapper.get_average_response_time("openai")
    assert avg_time > 0

@pytest.mark.asyncio
async def test_model_validation(openai_config):
    """Test invalid model handling"""
    wrapper = LLMWrapper(config=openai_config)
    response = await wrapper.query("Test prompt", model="invalid-model")
    
    assert response["status"] == "error"
    assert "Unsupported model" in response["error"]