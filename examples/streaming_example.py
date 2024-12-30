import asyncio
from multi_llm_wrapper import LLMWrapper

async def main():
    # Initialize wrapper
    wrapper = LLMWrapper()
    
    # Example prompts
    prompts = {
        "default": "Write a story about a curious cat",
        "groq": "Explain quantum computing in simple terms",
        "perplexity": "Describe the process of photosynthesis"
    }
    
    # Test streaming with default model (Anthropic)
    print("\nStreaming with Anthropic Claude:")
    async for chunk in await wrapper.query(prompt=prompts["default"], stream=True):
        if chunk["status"] == "error":
            print(f"Error: {chunk['error']}")
            break
        if chunk["content"]:
            print(chunk["content"], end="", flush=True)
    print("\n")
    
    # Test streaming with Groq
    print("\nStreaming with Groq:")
    async for chunk in await wrapper.query(
        prompt=prompts["groq"],
        stream=True,
        model="mixtral-8x7b-32768"
    ):
        if chunk["status"] == "error":
            print(f"Error: {chunk['error']}")
            break
        if chunk["content"]:
            print(chunk["content"], end="", flush=True)
    print("\n")
    
    # Test streaming with Perplexity
    print("\nStreaming with Perplexity:")
    async for chunk in await wrapper.query(
        prompt=prompts["perplexity"],
        stream=True,
        model="sonar-small"
    ):
        if chunk["status"] == "error":
            print(f"Error: {chunk['error']}")
            break
        if chunk["content"]:
            print(chunk["content"], end="", flush=True)
    print("\n")
    
    # Non-streaming example
    print("\nNon-streaming response (default model):")
    response = await wrapper.query(prompt=prompts["default"], stream=False)
    if response["status"] == "error":
        print(f"Error: {response['error']}")
    else:
        print(response["content"])

if __name__ == "__main__":
    asyncio.run(main())