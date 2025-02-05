# Multi-LLM Wrapper Project

## Overview
A lightweight abstraction layer for integrating multiple LLM providers while minimizing the need for code refactoring when changing backend providers, libraries, or proxies. This project focuses on maintaining code flexibility and provider independence through a minimal but effective abstraction layer.

## Core Components

### 1. Multi-LLM Wrapper (Core)
A lightweight abstraction layer designed to reduce the need to refactor code when changing LLM providers or libraries. Instead of hard-coding specific provider implementations (litellm, langchain, openrouter, etc.), this wrapper provides a consistent interface while isolating provider-specific code.

Key Features:
- Provider-agnostic interface
- Minimal dependencies
- Async support
- Standardized response formats
- Simple configuration

Currently Using:
- LiteLLM for provider connectivity (abstracted for future flexibility)
- Support for OpenAI, Anthropic, Groq, Google, and Perplexity
- Integration with custom providers (e.g., Brave Search Knowledge Aggregator)

### 2. Brave Search Knowledge Aggregator
A sophisticated search and knowledge synthesis component designed to integrate with the Multi-LLM Wrapper as though it were another LLM provider. Features streaming response capabilities to maintain compatibility with the wrapper's interface.

Status: Active development
Current Focus: 
- Implementing streaming responses
- Enhancing knowledge synthesis
- Integrating with the core wrapper

### 3. LiteLLM Proxy
A standardized LiteLLM proxy server providing OpenAI API compatibility for any LiteLLM-supported provider. 

Key Uses:
- Rapid testing of different LLM providers
- Tool for occasional one-off LLM access
- Backend support for tools like CLINE/Roo-Code
- Access to providers not natively supported by other tools

### 4. Groq Proxy (Deprecated)
A simple OpenAI API-compatible proxy specifically for Groq. Being phased out in favor of the more versatile LiteLLM Proxy.

## Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/exactdoug/multi-llm-wrapper.git
cd multi-llm-wrapper

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration
```bash
# Copy configuration examples
cp .env.example .env
cp litellm_proxy/config.yaml.example litellm_proxy/config.yaml

# Configure your .env file with required API keys
```

### Basic Usage
```python
import asyncio
from multi_llm_wrapper import LLMWrapper

async def main():
    wrapper = LLMWrapper()
    
    # Basic query using any configured provider
    response = await wrapper.query(
        "What is the capital of France?",
        model="claude-3-sonnet-20240229"  # Optional
    )
    
    print(f"Response: {response['content']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Component Setup

### LiteLLM Proxy
```bash
cd litellm_proxy
python proxy.py
# Server runs on http://localhost:8010
```

### Brave Search Knowledge Aggregator
```bash
# Development/Test Server
python -m brave_search_aggregator.test_server
# Runs on http://localhost:8001

# Production Server
python -m multi_llm_wrapper.web.run
# Runs on http://localhost:8000
```

## Project Structure
```
multi-llm-wrapper/
├── src/
│   ├── multi_llm_wrapper/     # Core wrapper implementation
│   └── brave_search_aggregator/ # Search component
├── litellm_proxy/            # LiteLLM proxy server
├── groq_proxy/              # Groq proxy (deprecated)
├── docs/                    # Documentation
└── tests/                  # Test suites
```

## Testing
```bash
# Run all tests
pytest

# Test specific components
pytest tests/test_wrapper/
pytest tests/brave_search_aggregator/
pytest litellm_proxy/tests/
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Run tests
4. Submit pull request

## License
MIT License - see LICENSE file for details.

## Authors
- Exact Technology Partners (dmortensen@exactpartners.com)