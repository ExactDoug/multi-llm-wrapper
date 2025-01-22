import asyncio
from src.multi_llm_wrapper.wrapper import LLMWrapper
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api_call():
    # Load environment variables
    load_dotenv()
    
    wrapper = LLMWrapper()
    
    # Test with Anthropic
    logger.info("Testing Anthropic API call...")
    response = await wrapper.query(
        "Hello, how are you?",
        model="claude-3-sonnet-20240229"
    )
    print("\nAnthropic response:", response)
    
    # Test with OpenAI
    logger.info("Testing OpenAI API call...")
    response = await wrapper.query(
        "Hello, how are you?",
        model="gpt-4"
    )
    print("\nOpenAI response:", response)

if __name__ == "__main__":
    asyncio.run(test_api_call())