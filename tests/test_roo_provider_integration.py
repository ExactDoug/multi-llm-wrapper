import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from multi_llm_wrapper import LLMWrapper
from multi_llm_wrapper.config import WrapperConfig, OpenAIConfig, AnthropicConfig
import os
import asyncio

@pytest.fixture
def test_configs():
    openai_config = OpenAIConfig(
        api_key="test-openai-key",
        organization_id="test-org-id"
    )
    anthropic_config = AnthropicConfig(
        api_key="test-anthropic-key"
    )
    return {
        "openai": WrapperConfig(
            default_model="gpt-4",
            default_provider="openai",
            openai=openai_config
        ),
        "anthropic": WrapperConfig(
            default_model="claude-3-sonnet-20240229",
            default_provider="anthropic",
            anthropic=anthropic_config
        )
    }

@pytest.fixture
def mock_completion():
    mock = AsyncMock()
    with patch('litellm.acompletion', mock):
        yield mock

@pytest.fixture
def mock_completion_no_delay():
    async def mock_async_completion(*args, **kwargs):
        mock_message = MagicMock(content="Test response")
        mock_choice = MagicMock(message=mock_message)
        mock_response = MagicMock(
            choices=[mock_choice],
            usage=MagicMock(total_tokens=10)
        )
        return mock_response

    mock = AsyncMock(side_effect=mock_async_completion)
    with patch('multi_llm_wrapper.wrapper.completion', mock):
        yield mock

@pytest.mark.asyncio
async def test_provider_switching(mock_completion, test_configs):
    """Test seamless switching between providers"""
    wrapper = LLMWrapper(config=test_configs["openai"])

    # Test OpenAI
    response = await wrapper.query("Test prompt", model="gpt-4")
    assert response["provider"] == "openai"

    # Switch to Anthropic
    response = await wrapper.query("Test prompt", model="claude-3-sonnet-20240229")
    assert response["provider"] == "anthropic"

@pytest.mark.asyncio
async def test_provider_specific_configurations(mock_completion, test_configs):
    """Test provider-specific configuration handling"""
    wrapper = LLMWrapper(config=test_configs["openai"])

    # OpenAI with org ID
    await wrapper.query("Test prompt")
    mock_completion.assert_called_with(
        model="gpt-4",
        messages=[{"role": "user", "content": "Test prompt"}],
        timeout=30,
        api_key="test-openai-key",
        headers={"OpenAI-Organization": "test-org-id"}
    )

    # Anthropic without org ID
    await wrapper.query("Test prompt", model="claude-3-sonnet-20240229")
    mock_completion.assert_called_with(
        model="claude-3-sonnet-20240229",
        messages=[{"role": "user", "content": "Test prompt"}],
        timeout=30,
        api_key="test-anthropic-key",
        headers={}
    )

@pytest.mark.asyncio
async def test_usage_tracking_accuracy(mock_completion_no_delay, test_configs):
    """Test accurate usage tracking across providers"""
    wrapper = LLMWrapper(config=test_configs["openai"])

    # Make requests to both providers
    await wrapper.query("Test OpenAI", model="gpt-4")
    await wrapper.query("Test Anthropic", model="claude-3-sonnet-20240229")

    usage = wrapper.get_usage_stats()
    assert usage["openai"]["requests"] == 1
    assert usage["anthropic"]["requests"] == 1
    assert usage["openai"]["tokens"] == 10
    assert usage["anthropic"]["tokens"] == 10

@pytest.mark.asyncio
async def test_response_time_monitoring(mock_completion, test_configs):
    """Test response time tracking per provider"""
    wrapper = LLMWrapper(config=test_configs["openai"])

    # Test multiple requests
    for _ in range(3):
        await wrapper.query("Test OpenAI", model="gpt-4")
        await wrapper.query("Test Anthropic", model="claude-3-sonnet-20240229")

    # Check average response times
    openai_avg = wrapper.get_average_response_time("openai")
    anthropic_avg = wrapper.get_average_response_time("anthropic")

    assert openai_avg > 0
    assert anthropic_avg > 0
    assert isinstance(openai_avg, float)
    assert isinstance(anthropic_avg, float)

@pytest.mark.asyncio
async def test_provider_stability(mock_completion, test_configs):
    """Test provider stability under continuous usage"""
    wrapper = LLMWrapper(config=test_configs["openai"])
    responses = []

    # Simulate continuous usage
    for _ in range(10):
        r1 = await wrapper.query("Test OpenAI", model="gpt-4")
        r2 = await wrapper.query("Test Anthropic", model="claude-3-sonnet-20240229")
        responses.extend([r1, r2])

    # Verify stability
    success_count = sum(1 for r in responses if r["status"] == "success")
    assert success_count == 20  # All requests should succeed
    assert len(set(r["content"] for r in responses)) == 1  # All should have same test response

@pytest.mark.asyncio
async def test_provider_edge_cases(mock_completion, test_configs):
    """Test provider edge cases and boundary conditions"""
    wrapper = LLMWrapper(config=test_configs["openai"])

    # Test empty prompt
    response = await wrapper.query("", model="gpt-4")
    assert response["status"] == "error"
    assert response["error_type"] == "validation_error"

    # Test timeout handling
    with patch('multi_llm_wrapper.wrapper.completion',
              AsyncMock(side_effect=TimeoutError("Request timed out"))):
        response = await wrapper.query("Test prompt", model="gpt-4")
        assert response["status"] == "error"
        assert response["error_type"] == "timeout"

    # Test rate limit handling
    with patch('multi_llm_wrapper.wrapper.completion',
              AsyncMock(side_effect=Exception("Rate limit exceeded"))):
        response = await wrapper.query("Test prompt", model="gpt-4")
        assert response["status"] == "error"
        assert "rate limit" in response["error"].lower()

@pytest.mark.asyncio
async def test_caching_mechanism(mock_completion):
    """Test that the caching mechanism is working correctly."""
    openai_config = OpenAIConfig(api_key="test-openai-key")
    anthropic_config = AnthropicConfig(api_key="test-anthropic-key")
    config = WrapperConfig(openai=openai_config, anthropic=anthropic_config)
    wrapper = LLMWrapper(config=config)
    prompt = "This is a test prompt"
    model = "gpt-4"

    # First call should not be cached
    await wrapper.query(prompt, model=model)
    mock_completion.assert_called_once()