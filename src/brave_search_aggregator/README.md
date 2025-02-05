# Brave Search Knowledge Aggregator

A sophisticated search and knowledge synthesis component designed to integrate with the Multi-LLM Wrapper by providing streaming responses compatible with the LLM interface pattern.

## Quick Start

```python
from brave_search_aggregator import BraveSearchAggregator

async def main():
    # Initialize aggregator
    aggregator = BraveSearchAggregator()
    
    # Process query with streaming
    async for result in aggregator.process_query("quantum computing advances"):
        print(result.content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Development Setup

```bash
# Set up virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Current Status

- Streaming implementation in progress
- Grid integration support
- Knowledge synthesis capabilities
- LLM-compatible interface

## Documentation

Full documentation available in `/docs/brave-dev/knowledge-aggregator/`:
- [Main Documentation](../../docs/brave-dev/knowledge-aggregator/README.md)
- [Architecture Overview](../../docs/brave-dev/knowledge-aggregator/architecture.md)
- [Implementation Guide](../../docs/brave-dev/knowledge-aggregator/implementation.md)
- [Configuration Guide](../../docs/brave-dev/knowledge-aggregator/configuration.md)

## Development Servers

```bash
# Test Server (Port 8001)
python -m brave_search_aggregator.test_server

# Production Server (Port 8000)
python -m multi_llm_wrapper.web.run
```

## Support

For issues or questions:
- Check the comprehensive documentation in `/docs/brave-dev/knowledge-aggregator/`
- Open an issue in the repository
- Contact development team (dmortensen@exactpartners.com)