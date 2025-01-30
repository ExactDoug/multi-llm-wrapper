import asyncio
import logging
from multi_llm_wrapper import LLMWrapper
from multi_llm_wrapper.config import WrapperConfig, GroqConfig

logging.basicConfig(level=logging.DEBUG)

async def main():
    config = WrapperConfig(
        default_model="deepseek-r1-distill-llama-70b",
        default_provider="groq",
        groq=GroqConfig(base_url="http://localhost:8000/groq-proxy/v1/completions")
    )
    wrapper = LLMWrapper(config=config)
    logging.debug("Wrapper configuration: %s", wrapper.config)
    response = await wrapper.query("Test Groq query", model="deepseek-r1-distill-llama-70b")
    logging.debug(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())