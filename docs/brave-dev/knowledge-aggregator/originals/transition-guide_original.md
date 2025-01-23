# Brave Search Knowledge Aggregator - Transition Guide

## Overview

This guide details the transition from the current BraveSearchIntegration to the new BraveSearchAggregator component. The transition is designed to be gradual and controlled through feature flags to maintain system stability.

## Architecture Changes

### Before (BraveSearchIntegration)
```
Web Interface (Grid)
└── BraveSearchIntegration
    ├── Direct API calls
    ├── Simple response processing
    └── Basic integration with grid
```

### After (BraveSearchAggregator)
```
Web Interface (Grid)
└── BraveSearchAggregator
    ├── Query Analyzer
    ├── Content Fetcher
    ├── Knowledge Synthesizer
    │   ├── MoE Routing
    │   ├── Task Vectors
    │   └── SLERP Merging
    └── Knowledge Aggregator
        ├── Parallel Processing
        ├── Source Processing
        └── Conflict Resolution
```

## Feature Flag Configuration

### Environment Variables
```bash
# Feature States: "on", "off", "beta"
FEATURE_MOE_ROUTING=beta
FEATURE_MOE_ROUTING_ROLLOUT=50.0

FEATURE_TASK_VECTORS=beta
FEATURE_TASK_VECTORS_ROLLOUT=30.0

FEATURE_SLERP_MERGING=beta
FEATURE_SLERP_MERGING_ROLLOUT=30.0

FEATURE_PARALLEL_PROCESSING=on
FEATURE_SOURCE_SPECIFIC=beta
FEATURE_SOURCE_SPECIFIC_ROLLOUT=50.0

FEATURE_GRID_COMPAT=on
```

### Rollout Phases

1. **Phase 1: Infrastructure (Current)**
   - Parallel processing enabled
   - Grid compatibility maintained
   - Basic aggregation active

2. **Phase 2: Enhanced Processing (Beta)**
   - MoE routing at 50% rollout
   - Source-specific processing at 50% rollout
   - Monitor performance and errors

3. **Phase 3: Advanced Features (Beta)**
   - Task vectors at 30% rollout
   - SLERP merging at 30% rollout
   - Gather feedback on result quality

4. **Phase 4: Full Rollout**
   - All features enabled
   - Old integration deprecated
   - Complete grid transition

## Grid Integration

### Grid Layout Changes
```
Before:                     After:
+----------------+         +----------------+
|      5x2      |         |      5x2      |
| Simple Layout |         | Enhanced Grid  |
| Direct Output |         | With Synthesis |
+----------------+         +----------------+
```

### Integration Points
1. **Response Format**
   ```python
   # Before
   response = {
       "content": str,
       "source": "brave_search"
   }

   # After
   response = {
       "content": str,
       "source": "brave_search",
       "confidence": float,
       "synthesis_mode": str,
       "coherence_score": float,
       "references": List[str]
   }
   ```

2. **Grid Cell Updates**
   - Enhanced progress indicators
   - Synthesis status display
   - Source contribution visualization
   - Confidence score indicators

## Backward Compatibility

### Compatibility Layer
```python
def adapt_response(new_response):
    """Convert new response format to old format if needed."""
    if not feature_flags.is_enabled("grid_compatibility"):
        return {
            "content": new_response["content"],
            "source": new_response["source"]
        }
    return new_response
```

### Fallback Mechanism
```python
async def get_search_results(query: str):
    """Get search results with fallback."""
    try:
        return await new_aggregator.process(query)
    except Exception as e:
        logger.error(f"New aggregator failed: {e}")
        return await legacy_integration.search(query)
```

## Monitoring and Metrics

### Key Metrics
1. Response Quality
   - Coherence scores
   - User engagement
   - Error rates

2. Performance
   - Processing time
   - Resource usage
   - Cache hit rates

3. Feature Usage
   - Feature flag status
   - Rollout percentages
   - Error rates per feature

### Dashboards
- Azure Application Insights
- Custom monitoring endpoints
- A/B testing results

## Error Handling

### Common Issues
1. **Synthesis Failures**
   ```python
   try:
       result = await synthesizer.process(query)
   except SynthesisError:
       # Fallback to basic processing
       result = await basic_processor.process(query)
   ```

2. **Grid Integration Issues**
   ```python
   try:
       await grid.update_cell(result)
   except GridError:
       # Use compatibility layer
       legacy_result = adapt_response(result)
       await grid.update_cell(legacy_result)
   ```

## Testing Strategy

### Integration Tests
```python
@pytest.mark.integration
async def test_grid_compatibility():
    """Verify grid compatibility layer."""
    aggregator = BraveSearchAggregator()
    result = await aggregator.process("test query")
    assert is_grid_compatible(result)
```

### A/B Testing
```python
async def process_query(query: str, user_id: str):
    """Process query with A/B testing."""
    if feature_flags.is_beta_enabled("moe_routing", user_id):
        return await process_with_moe(query)
    return await process_legacy(query)
```

## Rollback Procedures

### Emergency Rollback
1. Set all feature flags to "off"
2. Restart application
3. Verify legacy integration
4. Monitor error rates

### Gradual Rollback
1. Reduce feature rollout percentages
2. Monitor metrics
3. Adjust based on feedback
4. Maintain grid functionality

## Timeline

1. **Week 1-2: Infrastructure**
   - Deploy parallel processing
   - Set up monitoring
   - Enable grid compatibility

2. **Week 3-4: Beta Features**
   - Start MoE routing rollout
   - Begin source-specific processing
   - Gather initial feedback

3. **Week 5-6: Advanced Features**
   - Introduce task vectors
   - Enable SLERP merging
   - Expand monitoring

4. **Week 7-8: Full Transition**
   - Complete feature rollout
   - Remove legacy code
   - Finalize documentation

## Support and Maintenance

### Contact Information
- Technical Lead: dmortensen@exactpartners.com
- Support Team: support@exactpartners.com
- Emergency Contact: oncall@exactpartners.com

### Documentation
- Architecture: [architecture.md](architecture.md)
- Implementation: [implementation.md](implementation.md)
- API Reference: [api.md](api.md)

### Regular Maintenance
- Daily monitoring review
- Weekly performance analysis
- Bi-weekly feature flag adjustment
- Monthly comprehensive review