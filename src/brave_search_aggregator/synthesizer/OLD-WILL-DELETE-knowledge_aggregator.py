"""
Knowledge aggregation with parallel processing and source-specific handling.
"""
from dataclasses import dataclass
from typing import List, Dict, Any
import asyncio
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SourceType(Enum):
    """Types of knowledge sources."""
    BRAVE_SEARCH = "brave_search"
    LLM = "llm"
    CUSTOM = "custom"

@dataclass
class AggregationResult:
    """Result of knowledge aggregation process."""
    content: str
    all_sources_processed: bool
    conflicts_resolved: bool
    nuances_preserved: bool
    source_metrics: Dict[str, Dict[str, float]]
    processing_time: float

@dataclass
class SourceConfig:
    """Configuration for a specific knowledge source."""
    source_type: SourceType
    processing_weight: float
    timeout_seconds: int
    max_retries: int

class KnowledgeAggregator:
    """
    Aggregates knowledge from multiple sources with parallel processing.
    """
    
    def __init__(self):
        """Initialize the knowledge aggregator."""
        self.source_configs = {
            "brave_search": SourceConfig(
                source_type=SourceType.BRAVE_SEARCH,
                processing_weight=0.8,
                timeout_seconds=30,
                max_retries=3
            ),
            "llm1": SourceConfig(
                source_type=SourceType.LLM,
                processing_weight=0.9,
                timeout_seconds=60,
                max_retries=2
            ),
            "llm2": SourceConfig(
                source_type=SourceType.LLM,
                processing_weight=0.9,
                timeout_seconds=60,
                max_retries=2
            )
        }
        self._raw_results = {}

    def _process_brave_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Process raw Brave Search results into a structured format."""
        processed_content = []
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            description = result.get('description', 'No description')
            url = result.get('url', 'No URL')
            
            entry = (
                f"{i}. {title}\n"
                f"   {description}\n"
                f"   Source: {url}\n"
            )
            processed_content.append(entry)
            
        return "\n".join(processed_content)

    async def process_source(
        self,
        source: str,
        query: str,
        preserve_nuances: bool = True
    ) -> Dict[str, Any]:
        """Process a single knowledge source."""
        config = self.source_configs.get(source)
        if not config:
            raise ValueError(f"Unknown source: {source}")
            
        logger.debug(f"Processing source: {source}")
        
        if source == "brave_search":
            raw_results = self._raw_results.get(query, [])
            content = self._process_brave_search_results(raw_results)
            confidence = config.processing_weight
            
            metrics = {
                "result_count": len(raw_results),
                "confidence": confidence
            }
            
            return {
                "source": source,
                "content": content,
                "confidence": confidence,
                "nuances": {
                    "result_count": len(raw_results),
                    "source_type": "web_search"
                } if preserve_nuances else {},
                "metrics": metrics
            }
        else:
            # Placeholder for other source types
            await asyncio.sleep(0.1)
            return {
                "source": source,
                "content": f"Processed content from {source}",
                "confidence": config.processing_weight,
                "nuances": {"key": "value"} if preserve_nuances else {}
            }

    async def resolve_conflicts(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Resolve conflicts between source results."""
        return sorted(
            results,
            key=lambda x: (
                x.get("confidence", 0),
                x.get("metrics", {}).get("result_count", 0)
            ),
            reverse=True
        )

    async def process_parallel(
        self,
        query: str,
        sources: List[str],
        preserve_nuances: bool = True,
        raw_results: List[Dict[str, Any]] = None
    ) -> AggregationResult:
        """Process multiple sources in parallel."""
        start_time = asyncio.get_event_loop().time()
        
        if raw_results is not None:
            self._raw_results[query] = raw_results
        
        tasks = [
            self.process_source(source, query, preserve_nuances)
            for source in sources
        ]
        
        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )
        
        successful_results = [
            result for result in results
            if not isinstance(result, Exception)
        ]
        
        resolved_results = await self.resolve_conflicts(successful_results)
        
        source_metrics = {
            result["source"]: {
                "confidence": result.get("confidence", 0),
                "result_count": result.get("metrics", {}).get("result_count", 0)
            }
            for result in resolved_results
        }
        
        combined_content = "\n\n".join([
            f"Source: {result['source']}\n{result['content']}"
            for result in resolved_results
        ])
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        self._raw_results.pop(query, None)
        
        return AggregationResult(
            content=combined_content,
            all_sources_processed=len(successful_results) == len(sources),
            conflicts_resolved=True,
            nuances_preserved=preserve_nuances,
            source_metrics=source_metrics,
            processing_time=processing_time
        )