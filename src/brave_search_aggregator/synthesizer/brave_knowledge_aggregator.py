from typing import AsyncGenerator, Dict, List, Optional, Union, Any
from datetime import datetime
import logging

from ..analyzer.query_analyzer import QueryAnalyzer
from ..fetcher.brave_client import BraveSearchClient
from .knowledge_synthesizer import KnowledgeSynthesizer

logger = logging.getLogger(__name__)


class BraveKnowledgeAggregator:
    def __init__(
        self,
        brave_client: BraveSearchClient,
        query_analyzer: Optional[QueryAnalyzer] = None,
        knowledge_synthesizer: Optional[KnowledgeSynthesizer] = None,
    ):
        self.brave_client = brave_client
        self.query_analyzer = query_analyzer or QueryAnalyzer()
        self.knowledge_synthesizer = knowledge_synthesizer or KnowledgeSynthesizer()

    async def process_query(
        self, query: str
    ) -> AsyncGenerator[Dict[str, Union[str, bool, Dict[str, Any]]], None]:
        """Process a query and yield results with streaming support."""
        try:
            # Get query analysis
            query_analysis = await self.query_analyzer.analyze_query(query)
            
            # Initial status
            yield {
                "type": "status",
                "stage": "search_started",
                "message": f"Searching knowledge sources for: {query}",
                "timestamp": datetime.now().isoformat(),
                "query_analysis": query_analysis
            }

            # Process search results with streaming
            results = []
            selected_sources = []
            min_sources = 5

            try:
                # Stream search results
                async for result in self.brave_client.search(query):
                    results.append(result)
                    
                    # Stream individual result
                    yield {
                        "type": "search_result",
                        "index": len(results),
                        "total_so_far": len(results),
                        "timestamp": datetime.now().isoformat(),
                        "result": self._format_result(result),
                        "query_analysis": query_analysis
                    }

                    # Interim synthesis every N results
                    if len(results) % 3 == 0:
                        patterns = self._analyze_patterns(results)
                        interim_knowledge = await self.knowledge_synthesizer.synthesize(results[:len(results)])
                        
                        if patterns:
                            yield {
                                "type": "interim_analysis",
                                "results_analyzed": len(results),
                                "timestamp": datetime.now().isoformat(),
                                "patterns": patterns,
                                "synthesis": interim_knowledge,
                                "message": "Analyzing results..."
                            }

                    # Source selection when minimum reached
                    if len(results) >= min_sources and not selected_sources:
                        selected_sources = self._select_sources(results, min_sources)
                        yield {
                            "type": "status",
                            "stage": "source_selection",
                            "timestamp": datetime.now().isoformat(),
                            "message": f"Selected {len(selected_sources)} most relevant sources",
                            "sources": selected_sources
                        }

                if not results:
                    yield {"type": "error", "error": "No search results found"}
                    return

                # Final knowledge synthesis
                final_knowledge = await self.knowledge_synthesizer.synthesize(results)
                yield {
                    "type": "final_synthesis",
                    "timestamp": datetime.now().isoformat(),
                    "content": final_knowledge,
                    "total_results": len(results)
                }

            except Exception as e:
                # Stream error with any results so far
                logger.error(f"Error in search processing: {str(e)}", exc_info=True)
                yield {
                    "type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "partial_results": [self._format_result(r) for r in results]
                }

        except Exception as e:
            logger.error(f"Error in query processing: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    def _format_result(self, result: Dict[str, str]) -> Dict[str, str]:
        """Format a single search result."""
        return {
            "title": result.get("title", "No title"),
            "description": result.get("description", "No description"),
            "url": result.get("url", "No URL")
        }

    def _analyze_patterns(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract patterns from results."""
        if not results:
            return []
        
        domains = [r.get("url", "").split("/")[2] for r in results if "url" in r]
        top_domains = list({d for d in domains if domains.count(d) > 1})
        return [f"Multiple results from {domain}" for domain in top_domains[:3]]

    def _select_sources(
        self, 
        results: List[Dict[str, Any]], 
        min_sources: int
    ) -> List[Dict[str, Any]]:
        """Select most relevant sources."""
        scored = [{
            "url": r.get("url", ""),
            "relevance": 0.8 if r.get("title") and r.get("description") else 0.5
        } for r in results]
        
        return sorted(scored, key=lambda x: x["relevance"], reverse=True)[:min_sources]