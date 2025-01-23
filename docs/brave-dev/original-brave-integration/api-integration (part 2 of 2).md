self.last_update = time.monotonic()
        self.token_rate = max_rate / 1.0  # tokens per second
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire rate limit token"""
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(
                self.max_rate,
                self.tokens + elapsed * self.token_rate
            )
            self.last_update = now
            
            if self.tokens < 1:
                raise RateLimitError("Rate limit exceeded")
            
            self.tokens -= 1

### 4. Result Processing
```python
@dataclass
class SearchResult:
    """Structured search result"""
    title: str
    url: str
    description: str
    metadata: Dict[str, Any]

class ResultProcessor:
    def process_raw_results(
        self,
        raw_results: Dict[str, Any]
    ) -> List[SearchResult]:
        """
        Process raw API response into structured results
        
        Args:
            raw_results: Raw API response
            
        Returns:
            List of processed SearchResult objects
        """
        processed = []
        for result in raw_results.get("web", {}).get("results", []):
            processed.append(SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                description=result.get("description", ""),
                metadata={
                    "age": result.get("age"),
                    "language": result.get("language"),
                    "family_friendly": result.get("family_friendly", True)
                }
            ))
        return processed

### 5. Usage Tracking
```python
class UsageTracker:
    def __init__(self):
        self.queries_count = 0
        self.total_results = 0
        self.errors_count = 0
        self.start_time = time.monotonic()
    
    def track_query(
        self,
        results_count: int,
        error: Optional[Exception] = None
    ):
        """Track query execution and results"""
        self.queries_count += 1
        self.total_results += results_count
        if error:
            self.errors_count += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        elapsed = time.monotonic() - self.start_time
        return {
            "queries": self.queries_count,
            "results": self.total_results,
            "errors": self.errors_count,
            "uptime": elapsed,
            "queries_per_hour": self.queries_count / (elapsed / 3600),
            "error_rate": self.errors_count / max(1, self.queries_count)
        }

### 6. Configuration Management
```python
@dataclass
class BraveSearchConfig:
    """Configuration for Brave Search integration"""
    api_key: str
    max_results_per_query: int = 10
    max_rate: int = 20  # queries per second
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 1
    
    def validate(self):
        """Validate configuration values"""
        if not self.api_key:
            raise ValueError("API key is required")
        if self.max_results_per_query > 20:
            raise ValueError("Max results cannot exceed 20")
        if self.max_rate > 20:
            raise ValueError("Max rate cannot exceed 20 qps")

### 7. Integration Manager
```python
class BraveSearchManager:
    """Main integration manager"""
    def __init__(self, config: BraveSearchConfig):
        self.config = config
        self.config.validate()
        self.client = BraveSearchClient(config.api_key)
        self.rate_limiter = RateLimiter(config.max_rate)
        self.processor = ResultProcessor()
        self.usage = UsageTracker()
    
    async def search(
        self,
        query: str,
        results_count: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Execute search with full integration features
        
        Args:
            query: Search query string
            results_count: Optional override for result count
            
        Returns:
            List of processed search results
            
        Raises:
            BraveSearchError: For API or processing errors
            RateLimitError: When rate limit is exceeded
        """
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()
            
            # Execute search
            count = results_count or self.config.max_results_per_query
            raw_results = await self.client.search(query, count)
            
            # Process results
            processed = self.processor.process_raw_results(raw_results)
            
            # Track usage
            self.usage.track_query(len(processed))
            
            return processed
            
        except Exception as e:
            self.usage.track_query(0, error=e)
            raise

## Integration Guidelines

### Setup
1. Create configuration:
```python
config = BraveSearchConfig(
    api_key="your-api-key",
    max_results_per_query=10
)
```

2. Initialize manager:
```python
search_manager = BraveSearchManager(config)
```

3. Execute searches:
```python
results = await search_manager.search("your query")
```

### Error Handling
1. Handle specific exceptions:
```python
try:
    results = await search_manager.search(query)
except RateLimitError:
    # Handle rate limiting
    pass
except BraveSearchError as e:
    # Handle API errors
    pass
```

### Usage Monitoring
1. Get usage statistics:
```python
stats = search_manager.usage.get_statistics()
print(f"Queries executed: {stats['queries']}")
print(f"Error rate: {stats['error_rate']:.2%}")
```

## Best Practices
1. Always use rate limiting
2. Implement proper error handling
3. Monitor usage statistics
4. Validate configurations
5. Process results consistently
6. Handle cleanup properly
7. Use appropriate timeouts
8. Implement retry logic

## Cost Management
1. Track query counts
2. Monitor error rates
3. Optimize result counts
4. Implement caching when appropriate
5. Regular usage audits
