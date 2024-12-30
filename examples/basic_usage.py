import asyncio
from multi_llm_wrapper import LLMWrapper

async def main():
    # Initialize wrapper
    wrapper = LLMWrapper()
    
    # Query using default model (Anthropic Claude)
    response = await wrapper.query(
        "Explain how to make a peanut butter sandwich."
    )
    print(f"\nDefault model (Anthropic) response: {response['content']}")
    
    # Query using Groq
    response = await wrapper.query(
        "What is the capital of France?",
        model="mixtral-8x7b-32768"
    )
    print(f"\nGroq response: {response['content']}")
    
    # Query using Perplexity
    response = await wrapper.query(
        "What are the benefits of exercise?",
        model="sonar-small"
    )
    print(f"\nPerplexity response: {response['content']}")

if __name__ == "__main__":
    asyncio.run(main())
