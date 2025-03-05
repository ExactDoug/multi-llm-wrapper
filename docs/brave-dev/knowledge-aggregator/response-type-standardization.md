# BraveKnowledgeAggregator Response Type Standardization

## Overview

This document describes the standardization of response types in the `BraveKnowledgeAggregator` component to ensure compatibility with the multi-llm-wrapper's expected model formats.

## Context

The BraveKnowledgeAggregator was initially designed with a rich response format that included various response types like:
- "status" (for status updates)
- "search_result" (for individual search results)
- "interim_analysis" (for batch analysis)
- "final_synthesis" (for final results)
- "error" (for error conditions)

However, the multi-llm-wrapper and its test suite expect responses to use the standard model format, which only supports two response types:
- "content" (for any non-error content)
- "error" (for error conditions)

This mismatch was causing test failures, as the tests expected "content" but were receiving the custom types.

## Implementation Details

To address this issue, a standardization layer was implemented in the `process_query` method that:

1. Converts all non-error response types to "content"
2. Preserves the original type information in a new field called "content_type"
3. Ensures all responses have a "content" field with formatted text for display
4. Leaves "error" responses as-is since they already match the expected format

### Example Transformation

Before:
```json
{
  "type": "status",
  "stage": "search_started",
  "message": "Searching knowledge sources for: query"
}
```

After:
```json
{
  "type": "content",
  "content_type": "status",
  "stage": "search_started",
  "message": "Searching knowledge sources for: query",
  "content": "Searching knowledge sources for: query"
}
```

## Benefits

This approach:
1. Ensures compatibility with the test suite and grid display
2. Preserves all the original rich metadata for advanced use cases
3. Allows for graceful future expansion of the response format
4. Maintains backward compatibility with any code already working with the custom types

## Implementation Date

This standardization was implemented on February 27, 2025.
