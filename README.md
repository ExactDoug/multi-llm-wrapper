# Multi-LLM Wrapper

A lightweight, extensible Python wrapper for interacting with multiple Large Language Models (LLMs) through a unified interface. This project aims to simplify the integration and usage of various LLM providers while maintaining a consistent API.

## Features

- Unified interface for multiple LLM providers
- Async support for efficient processing
- Standardized response format
- Built-in error handling and logging
- Simple configuration system
- Provider-agnostic design

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd multi-llm-wrapper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
```bash
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here  # if using OpenAI models
```

### Basic Usage

```python
import asyncio
from multi_llm_wrapper import LLMWrapper

async def main():
    wrapper = LLMWrapper()
    
    response = await wrapper.query(
        "Explain how to make a peanut butter sandwich."
    )
    
    print(f"Response: {response['content']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The wrapper can be configured using the `WrapperConfig` class:

```python
from multi_llm_wrapper import WrapperConfig

config = WrapperConfig(
    default_model="claude-3-sonnet-20240229",
    default_provider="anthropic",
    timeout_seconds=30,
    max_retries=2
)

wrapper = LLMWrapper(config=config)
```

## Running Tests

```bash
pytest tests/
```

## Project Structure

```
multi_llm_wrapper/
├── src/
│   ├── __init__.py
│   ├── wrapper.py      # Core wrapper implementation
│   ├── config.py       # Configuration
│   └── utils.py        # Helper utilities
├── tests/
│   ├── __init__.py
│   └── test_wrapper.py # Tests
├── examples/
│   └── basic_usage.py  # Usage examples
├── README.md
├── requirements.txt
└── setup.py
```

## Current Status

This is the initial implementation with basic functionality. Future enhancements will include:

- Additional provider integrations
- Response synthesis capabilities
- Advanced error recovery
- Comprehensive monitoring
- Caching and optimization
- Load balancing and failover

## License

[Specify your license]

## Contributing

[Add contribution guidelines]
