# BraveKnowledgeAggregator Implementation Guide

## Overview
The BraveKnowledgeAggregator provides enhanced search result processing with streaming support, error handling, and integration with the multi-llm synthesis web service.

## Components

### Core Components
1. BraveKnowledgeAggregator
   - Handles search result processing
   - Manages streaming responses
   - Integrates query analysis and knowledge synthesis
   - Provides robust error handling

2. QueryAnalyzer (Optional)
   - Analyzes search queries
   - Provides query insights
   - Enhances search context

3. KnowledgeSynthesizer (Optional)
   - Synthesizes search results
   - Generates knowledge insights
   - Enhances result context

## Implementation Details

### Streaming Support

#### Async Iterator Pattern
The BraveKnowledgeAggregator implements proper async iteration for streaming results:

1. Search Client Implementation
```python
class SearchResultIterator:
    """Async iterator for search results."""
    async def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.results:
            # Fetch results on first iteration
            await self._fetch_results()
        if self.index >= len(self.results):
            raise StopAsyncIteration
        result = self.results[self.index]
        self.index += 1
        return result

async def search(self, query: str) -> AsyncIterator:
    """Returns an async iterator for search results."""
    return self.SearchResultIterator(self, query)
```

2. Aggregator Implementation
```python
async def process_query(self, query: str) -> AsyncGenerator[Dict[str, Union[str, bool]], None]:
    """Process a query and yield results."""
    try:
        # Get query analysis first
        query_analysis = await self.query_analyzer.analyze_query(query)
        
        # Get search results using async iterator
        search_iterator = await self.brave_client.search(query)
        async for result in search_iterator:
            # Process and yield each result
            yield self._format_response(result, query_analysis)
```

This pattern ensures:
- Proper async iteration protocol implementation
- Efficient streaming of results
- Correct coroutine handling
- Proper error propagation

### Error Handling
1. Early Error Detection
   - Verify search functionality before yielding content
   - Handle StopAsyncIteration for no results
   - Catch and handle API errors

2. Partial Results
   - Yield partial content before errors when available
   - Include error details in response
   - Maintain proper response structure

3. Error Response Format
```python
{
    "type": "error",
    "error": str(error_message)
}
```

### Web Service Integration
1. Optional Dependencies
   - QueryAnalyzer and KnowledgeSynthesizer are optional
   - Default implementations provided
   - Flexible configuration

2. Response Formats
#### Internal Rich Format
```python
{
    "type": "content",
    "title": str,
    "content": str,
    "metadata": Dict[str, Any]
}
```

#### Model Interface Format
```python
{
    "type": "content",
    "content": str
}
```

3. Format Transformation
```python
def transform_to_model_format(rich_response: Dict) -> Dict:
    """Transform rich internal response to model format."""
    if rich_response["type"] == "error":
        return {
            "type": "error",
            "message": rich_response["error"]  # Standard error format
        }
    return {
        "type": "content",
        "content": rich_response["content"]  # Standard content format
    }
```

4. Integration Points
   - Port 8000 for production
   - Streaming response handling
   - Error propagation
   - Synthesis integration
   - Model interface compatibility

## Production Setup

### Environment Configuration
1. API Key Setup
```bash
# .env file
BRAVE_SEARCH_API_KEY=your_api_key_here
```

2. Rate Limiting
```python
# Configure in config.py
max_requests_per_second = 20
timeout_seconds = 30
```

3. Logging Configuration
```python
# Configure in config.py
log_level = "INFO"
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Package Installation
```bash
pip install -e .
```

### Server Configuration
1. Production Settings
```python
# Configure in app.py
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))
```

2. Error Monitoring
```python
# Configure error handlers
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)}
    )
```

## Testing Requirements

### Streaming Tests
1. Response Timing
   - First chunk within 1 second
   - Complete within 5 seconds
   - At least 3 chunks

2. Chunk Size
   - Under 16KB per chunk
   - Non-empty content

3. Error Handling
   - Yield partial content
   - Include error message
   - Proper response format

4. Load Testing
   - 5 concurrent queries
   - Complete within 10 seconds
   - All queries receive responses

## Monitoring Setup

### Error Tracking
1. Log Configuration
```python
logging.config.dictConfig({
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'production.log',
            'formatter': 'standard'
        }
    }
})
```

2. Metrics Collection
```python
# Track API usage
api_calls = 0
error_count = 0
average_response_time = 0
```

### Health Checks
1. API Status
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

2. Rate Limit Monitoring
```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Track and enforce rate limits
```

## Troubleshooting Guide

### Common Issues
1. API Key Issues
   - Verify key in .env
   - Check rate limits
   - Monitor usage

2. Streaming Issues
   - Check chunk sizes
   - Monitor timing
   - Verify error handling

3. Integration Issues
   - Verify dependencies
   - Check configurations
   - Monitor logs

### Error Resolution
1. API Errors
   - Check API key
   - Verify rate limits
   - Review error logs

2. Streaming Errors
   - Check network
   - Verify timeouts
   - Monitor memory

3. Integration Errors
   - Check dependencies
   - Verify configurations
   - Review logs