# Streaming Implementation Plan

## Content Types & Flow

### 1. Search Status Messages
```json
{
  "type": "status",
  "stage": "search_started",
  "message": "Searching knowledge sources for: {query}"
}
```

### 2. Search Result Stream
```json
{
  "type": "search_result",
  "index": 1,
  "total_so_far": 1,
  "result": {
    "title": "Result Title",
    "description": "Brief description...",
    "url": "https://..."
  }
}
```

### 3. Intermediate Analysis (After collecting N results)
```json
{
  "type": "interim_analysis",
  "results_analyzed": 5,
  "total_results": 10,
  "patterns": ["Key pattern 1", "Key pattern 2"],
  "message": "Initial analysis from top results..."
}
```

### 4. Selection Status
```json
{
  "type": "status",
  "stage": "source_selection",
  "message": "Selected 5 most relevant sources for detailed analysis",
  "sources": [
    {"url": "https://...", "relevance": 0.95},
    // ...
  ]
}
```

### 5. Content Fetch Progress (Phase 2)
Reserved format for future implementation:
```json
{
  "type": "fetch_progress",
  "completed": 2,
  "total": 5,
  "message": "Retrieved 2 of 5 selected sources"
}
```

## Implementation 

```python
class KnowledgeAggregator:
    async def process_streaming(
        self, 
        query: str,
        min_sources: int = 5
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream search results with analysis."""
        
        # Initial status
        yield {
            "type": "status",
            "stage": "search_started",
            "message": f"Searching knowledge sources for: {query}"
        }

        # Track results for analysis
        results = []
        selected_sources = []
        
        # Process search results
        async for result in self.brave_client.search(query):
            results.append(result)
            
            # Stream each result
            yield {
                "type": "search_result",
                "index": len(results),
                "total_so_far": len(results),
                "result": self._format_result(result)
            }

            # Interim analysis every N results
            if len(results) % 3 == 0:
                yield {
                    "type": "interim_analysis",
                    "results_analyzed": len(results),
                    "patterns": self._analyze_patterns(results),
                    "message": "Processing initial results..."
                }

            # Source selection when we have enough results
            if len(results) >= min_sources and not selected_sources:
                selected_sources = self._select_sources(results, min_sources)
                yield {
                    "type": "status",
                    "stage": "source_selection",
                    "message": f"Selected {len(selected_sources)} most relevant sources",
                    "sources": selected_sources
                }

        # Final summary
        yield {
            "type": "summary",
            "total_results": len(results),
            "selected_sources": len(selected_sources),
            "key_findings": self._generate_summary(results)
        }
```

## Success Criteria

- First status: < 100ms
- First result: < 1s 
- Source selection: < 3s
- Memory usage: < 10MB
- Clear progress indication
- Meaningful interim content

## Testing Strategy

```python
@pytest.mark.asyncio
async def test_streaming_flow():
    """Verify streaming message sequence and timing."""
    results = []
    async for msg in aggregator.process_streaming("test query"):
        results.append(msg)
        
        if msg["type"] == "status":
            assert "stage" in msg
            assert "message" in msg
            
        if msg["type"] == "search_result":
            assert msg["index"] > 0
            assert "result" in msg
            
        if msg["type"] == "source_selection":
            assert len(msg["sources"]) >= 5
```
