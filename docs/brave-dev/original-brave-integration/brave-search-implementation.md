# Brave Search API Integration
Last Updated: January 4, 2025 10:32pm Mountain Time

## Overview
Integration of Brave Search API into the multi-llm-wrapper project to enhance LLM responses with real-time web search results. This integration provides additional context to LLM queries by incorporating relevant search results before processing, and serves as a standalone 10th knowledge source in our multi-LLM grid interface.

## Architecture

### 1. Core Components

#### BraveSearchClient (src/multi_llm_wrapper/web/brave_search.py)
- Handles API communication
- Implements rate limiting
- Processes search results
- Tracks usage statistics
- Lazy initialization to prevent circular imports

#### Configuration (src/multi_llm_wrapper/config_types.py)
```python
@dataclass
class BraveSearchConfig:
    api_key: str
    max_results_per_query: int = 10
    max_rate: int = 20
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 1
```

#### Web Interface (src/multi_llm_wrapper/web/)
- service.py: Business logic and LLM integration
- app.py: FastAPI routes and endpoints
- Streaming response support
- Session management
- 5x2 grid layout for 10 knowledge sources

### 2. Integration Points

#### LLMWrapper Enhancement
- Optional search context for queries
- Configurable result count
- Automatic rate limiting
- Usage tracking
- Lazy loading pattern for circular import prevention

#### Web UI
- Streaming responses
- Result synthesis
- Error handling
- Session management
- Responsive 5x2 grid layout
- Dynamic title updates

## Implementation Status

### Phase 1: MVP (COMPLETED)
- [x] Basic API integration
- [x] Rate limiting
- [x] Error handling
- [x] Configuration management
- [x] Web interface integration
- [x] Grid layout adaptation
- [x] Synthesis integration
- [x] Lazy loading implementation
- [x] Title updates

### Phase 2: Enhancements (IN PROGRESS)
- [x] Advanced error handling
- [x] Responsive grid layout
- [x] Search result formatting
- [x] Synthesis prompt enhancement
- [ ] Caching layer
- [ ] Advanced rate limiting
- [ ] Result filtering
- [ ] Metrics collection
- [ ] Performance optimization

### Phase 3: Advanced Features (PLANNED)
- [ ] Smart context integration
- [ ] Result ranking
- [ ] Query optimization
- [ ] Parallel search requests
- [ ] Custom result formatting

### Phase 4: Production Readiness (PLANNED)
- [ ] Comprehensive testing
- [x] Basic documentation
- [ ] Advanced documentation
- [ ] Monitoring
- [ ] Deployment guides
- [ ] Performance benchmarks

## Technical Details

### API Endpoints
```
Base URL: https://api.search.brave.com/res/v1/web/search
Rate Limit: 20 queries/second
Authentication: X-Subscription-Token header
```

### Rate Limiting Implementation
```python
class RateLimiter:
    def __init__(self, max_rate: int = 20):
        self.max_rate = max_rate
        self.tokens = max_rate
        self.last_update = time.monotonic()
        self.token_rate = max_rate / 1.0
        self.lock = asyncio.Lock()
```

### Error Handling
- Custom BraveSearchError exception
- HTTP status code handling
- Rate limit detection
- Timeout management
- User-friendly error messages
- API key validation

### Response Processing
```python
@dataclass
class SearchResult:
    title: str
    url: str
    description: str
    metadata: Dict[str, Any]
```

### Lazy Loading Pattern
```python
@property
def brave_search(self):
    """Lazy initialization of Brave Search client"""
    if self._brave_search is None and self.config.brave_search.api_key:
        from .web.brave_search import BraveSearchClient
        self._brave_search = BraveSearchClient(self.config.brave_search)
    return self._brave_search
```

## Configuration

### Environment Variables
```
BRAVE_SEARCH_API_KEY=your_api_key_here
```

### Optional Settings
- max_results_per_query (default: 10)
- timeout_seconds (default: 30)
- retry_attempts (default: 3)

## Usage Examples

### Basic Search
```python
client = BraveSearchClient(config)
results = await client.search("quantum computing")
```

### Enhanced LLM Query
```python
response = await wrapper.query(
    prompt="Explain quantum computing",
    enhance_with_search=True,
    search_results_count=5
)
```

### Grid Integration
```python
# Brave Search is available as the 10th knowledge source
models = [
    "claude-3-opus-20240229",    # 0: Claude 3 Opus
    "claude-3-sonnet-20240229",  # 1: Claude 3 Sonnet
    "gpt-4",                     # 2: GPT-4
    "gpt-3.5-turbo",            # 3: GPT-3.5 Turbo
    "mixtral-8x7b-32768",       # 4: Groq Mixtral
    "llama3-8b-8192",           # 5: Groq LLaMA 3
    "sonar-small",              # 6: Perplexity Sonar Small
    "sonar-large",              # 7: Perplexity Sonar Large
    "gemini-1.5-flash",         # 8: Google Gemini Pro
    "brave_search"              # 9: Brave Search
]
```

## Best Practices

### Rate Limiting
1. Use token bucket algorithm
2. Respect API limits
3. Implement backoff strategy

### Error Handling
1. Catch specific exceptions
2. Provide meaningful errors
3. Implement retry logic
4. Validate API key configuration

### Response Processing
1. Validate results
2. Handle missing fields
3. Format consistently
4. Preserve URLs for verification

## Next Steps

### Immediate
1. Implement caching layer
2. Add retry logic
3. Enhance error reporting

### Short Term
1. Add metrics collection
2. Implement result filtering
3. Optimize performance

### Long Term
1. Smart context integration
2. Advanced result ranking
3. Query optimization

## Known Issues
1. No caching implementation
2. Basic error handling
3. Limited result filtering

## Dependencies
- aiohttp for async requests
- FastAPI for web interface
- Python 3.8+ required
- dataclasses for configuration

## Testing
- Basic functionality tested
- Unit tests needed
- Integration tests needed
- Performance benchmarks needed

## Documentation
- API documentation complete
- Integration guide needed
- Deployment guide needed
- Grid integration documented

## Monitoring
- Basic usage tracking implemented
- Advanced metrics needed
- Performance monitoring needed