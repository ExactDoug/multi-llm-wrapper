# API Integration Details

## Brave Search API Overview
1. Base URL: https://api.search.brave.com/res/v1/web/search
2. Authentication: X-Subscription-Token header
3. Rate Limits: 20 queries/second (paid tier)
4. Response Format: JSON

## Implementation Details

### 1. API Client
```python
class BraveSearchClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.session = aiohttp.ClientSession()
        
    async def search(
        self,
        query: str,
        count: int = 5
    ) -> Dict[str, Any]:
        """
        Execute search query
        
        Args:
            query: Search string
            count: Number of results (max 20)
            
        Returns:
            Dict containing search results
        """
        headers = {
            "X-Subscription-Token": self.api_key,
            "Accept": "application/json"
        }
        params = {
            "q": query,
            "count": min(count, 20)
        }
        
        try:
            async with self.session.get(
                self.base_url,
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise BraveSearchError(
                        f"API error: {response.status}"
                    )
        except Exception as e:
            raise BraveSearchError(f"Search failed: {str(e)}")
```

### 2. Error Handling
```python
class BraveSearchError(Exception):
    """Custom exception for Brave Search errors"""
    pass

class ErrorHandler:
    def handle_error(
        self,
        error: Exception
    ) -> Dict[str, Any]:
        """Handle various error types"""
        # Implementation...
```

### 3. Rate Limiting
```python
class RateLimiter:
    def __init__(self, max_rate: int = 20):
        self.max_rate = max_rate
        self.tokens = max_rate