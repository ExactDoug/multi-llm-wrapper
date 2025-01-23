# Brave Search Knowledge Aggregator

A sophisticated component for the multi-llm-wrapper project that enhances search capabilities by intelligently processing and synthesizing web search results.

## Features

- Intelligent query analysis and optimization
- Efficient content fetching with rate limiting
- Advanced knowledge synthesis
- Azure integration with enterprise security
- Comprehensive monitoring and logging

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Configuration

1. Create a `.env` file:
```bash
cp .env.example .env
```

2. Configure environment variables:
```plaintext
BRAVE_API_KEY=your_api_key_here
MAX_RESULTS_PER_QUERY=20
TIMEOUT_SECONDS=30
RATE_LIMIT=20
```

3. Azure configuration (if using Azure deployment):
```plaintext
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
```

## Usage

```python
from brave_search_aggregator import BraveSearchAggregator

# Initialize the aggregator
aggregator = BraveSearchAggregator()

# Process a query
result = await aggregator.process_query("latest developments in AI")

# Access the synthesized response
print(result.content)

# Access references
for ref in result.references:
    print(f"[{ref.index}] {ref.title}: {ref.url}")
```

## Development

1. Set up development environment:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

2. Run tests:
```bash
pytest
```

3. Run linting:
```bash
pylint src/brave_search_aggregator
```

4. Run type checking:
```bash
mypy src/brave_search_aggregator
```

## Documentation

- [Architecture Overview](knowledge-aggregator/architecture.md)
- [Implementation Guide](knowledge-aggregator/implementation.md)
- [Configuration Guide](knowledge-aggregator/configuration.md)

## Azure Deployment

1. Create Azure resources:
```bash
az webapp create \
    --resource-group apps-rg \
    --plan <app-service-plan> \
    --name brave-search-aggregator \
    --runtime "PYTHON:3.11"
```

2. Configure environment variables:
```bash
az webapp config appsettings set \
    --name brave-search-aggregator \
    --resource-group apps-rg \
    --settings @azure-settings.json
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Authors

- Exact Technology Partners (dmortensen@exactpartners.com)
