import asyncio
from src.multi_llm_wrapper.wrapper import LLMWrapper

async def test_basic_wrapper():
    wrapper = LLMWrapper()
    
    # Test validation error handling
    response = await wrapper.query("")
    print("Empty prompt response:", response)
    assert response["status"] == "error"
    assert response["error_type"] == "validation_error"
    
    print("Basic error handling test passed!")

if __name__ == "__main__":
    asyncio.run(test_basic_wrapper())