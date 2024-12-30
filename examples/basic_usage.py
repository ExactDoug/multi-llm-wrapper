import asyncio
from multi_llm_wrapper import LLMWrapper

async def main():
    # Initialize wrapper
    wrapper = LLMWrapper()
    
    # Test Gemini 1.5 Flash
    print("\nTesting Gemini 1.5 Flash...")
    response = await wrapper.query(
        "What is the capital of France?",
        model="gemini-1.5-flash"
    )
    print(f"\nGemini 1.5 Flash response: {response['content']}")

if __name__ == "__main__":
    asyncio.run(main())
