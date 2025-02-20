from typing import AsyncGenerator, Dict, List, Optional, Union, Any
from datetime import datetime
import logging
import asyncio

from ..analyzer.query_analyzer import QueryAnalyzer, QueryAnalysis
from ..fetcher.brave_client import BraveSearchClient
from .knowledge_synthesizer import KnowledgeSynthesizer
from ..utils.config import Config, AnalyzerConfig

logger = logging.getLogger(__name__)


class BraveKnowledgeAggregator:
    def __init__(
        self,
        brave_client: BraveSearchClient,
        config: Config,
        query_analyzer: Optional[QueryAnalyzer] = None,
        knowledge_synthesizer: Optional[KnowledgeSynthesizer] = None,
    ):
        self.brave_client = brave_client
        self.config = config
        self.query_analyzer = query_analyzer or QueryAnalyzer()
        self.knowledge_synthesizer = knowledge_synthesizer or KnowledgeSynthesizer()
        self.min_sources = 5

    async def process_query(
        self, query: str
    ) -> AsyncGenerator[Dict[str, Union[str, bool, Dict[str, Any]]], None]:
        """Process a query and yield results with streaming support."""
        try:
            # Get enhanced query analysis
            query_analysis = await self.query_analyzer.analyze_query(query)
            
            # Initial status with enhanced analysis
            yield {
                "type": "status",
                "stage": "analysis_complete",
                "message": f"Analyzed query: {query}",
                "timestamp": datetime.now().isoformat(),
                "query_analysis": {
                    "complexity": query_analysis.complexity,
                    "is_ambiguous": query_analysis.is_ambiguous,
                    "input_type": query_analysis.input_type.primary_type.name if query_analysis.input_type else None,
                    "confidence": query_analysis.input_type.confidence if query_analysis.input_type else None,
                    "insights": query_analysis.insights,
                    "performance_metrics": query_analysis.performance_metrics
                }
            }

            # Handle unsuitable queries early
            if not query_analysis.is_suitable_for_search:
                yield {
                    "type": "error",
                    "stage": "analysis",
                    "message": f"Query unsuitable: {query_analysis.reason_unsuitable}",
                    "timestamp": datetime.now().isoformat(),
                    "details": {
                        "reason": query_analysis.reason_unsuitable,
                        "suggestions": self._get_query_suggestions(query_analysis)
                    }
                }
                return

            # Stream search initialization
            yield {
                "type": "status",
                "stage": "search_started",
                "message": f"Searching knowledge sources for: {query}",
                "timestamp": datetime.now().isoformat(),
                "search_parameters": {
                    "original_query": query,
                    "optimized_query": query_analysis.search_string,
                    "complexity": query_analysis.complexity
                }
            }

            # Process search results with streaming
            results = []
            selected_sources = []
            analysis_batch = []
            
            try:
                # Stream search results
                async for result in self.brave_client.search(query_analysis.search_string):
                    results.append(result)
                    analysis_batch.append(result)
                    
                    # Stream individual result with enhanced context
                    yield {
                        "type": "search_result",
                        "index": len(results),
                        "total_so_far": len(results),
                        "timestamp": datetime.now().isoformat(),
                        "result": self._format_result(result),
                        "context": {
                            "relevance_score": self._calculate_relevance(result, query_analysis),
                            "matches_segments": self._check_segment_matches(result, query_analysis)
                        }
                    }

                    # Batch analysis based on configuration
                    if len(analysis_batch) >= self.config.analyzer.analysis_batch_size:
                        patterns = self._analyze_patterns(analysis_batch)
                        interim_knowledge = await self.knowledge_synthesizer.synthesize(analysis_batch)
                        
                        if patterns or interim_knowledge:
                            yield {
                                "type": "interim_analysis",
                                "results_analyzed": len(results),
                                "timestamp": datetime.now().isoformat(),
                                "patterns": patterns,
                                "synthesis": interim_knowledge,
                                "performance": {
                                    "batch_size": len(analysis_batch),
                                    "processing_time": query_analysis.performance_metrics.get("processing_time_ms")
                                }
                            }
                        analysis_batch = []

                    # Source selection when minimum reached
                    if len(results) >= self.min_sources and not selected_sources:
                        selected_sources = self._select_sources(results, query_analysis)
                        yield {
                            "type": "status",
                            "stage": "source_selection",
                            "timestamp": datetime.now().isoformat(),
                            "message": f"Selected {len(selected_sources)} most relevant sources",
                            "sources": selected_sources,
                            "selection_criteria": {
                                "relevance_threshold": 0.7,
                                "diversity_factor": 0.3
                            }
                        }

                if not results:
                    yield {
                        "type": "error",
                        "error": "No search results found",
                        "suggestions": self._get_query_suggestions(query_analysis)
                    }
                    return

                # Final knowledge synthesis with enhanced context
                final_knowledge = await self.knowledge_synthesizer.synthesize(results)
                yield {
                    "type": "final_synthesis",
                    "timestamp": datetime.now().isoformat(),
                    "content": final_knowledge,
                    "total_results": len(results),
                    "analysis_summary": {
                        "complexity": query_analysis.complexity,
                        "ambiguity_handled": query_analysis.is_ambiguous,
                        "segments_analyzed": len(query_analysis.sub_queries) if query_analysis.sub_queries else 0,
                        "performance_metrics": query_analysis.performance_metrics
                    }
                }

            except Exception as e:
                # Stream error with enhanced context
                logger.error(f"Error in search processing: {str(e)}", exc_info=True)
                yield {
                    "type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "partial_results": [self._format_result(r) for r in results],
                    "context": {
                        "processed_count": len(results),
                        "last_successful_stage": "result_processing" if results else "initialization",
                        "query_analysis": query_analysis.insights if query_analysis else None
                    }
                }

        except Exception as e:
            logger.error(f"Error in query processing: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "context": {
                    "stage": "query_analysis",
                    "query": query
                }
            }

    def _format_result(self, result: Dict[str, str]) -> Dict[str, str]:
        """Format a single search result."""
        return {
            "title": result.get("title", "No title"),
            "description": result.get("description", "No description"),
            "url": result.get("url", "No URL")
        }

    def _analyze_patterns(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract patterns from results with enhanced analysis."""
        if not results:
            return []
        
        patterns = []
        
        # Analyze domains
        domains = [r.get("url", "").split("/")[2] for r in results if "url" in r]
        domain_counts = {d: domains.count(d) for d in set(domains)}
        top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        patterns.extend(f"Multiple results from {domain}" for domain, count in top_domains if count > 1)
        
        # Analyze content types
        content_types = [self._detect_content_type(r) for r in results]
        if len(set(content_types)) > 1:
            patterns.append(f"Mixed content types: {', '.join(set(content_types))}")
            
        return patterns

    def _detect_content_type(self, result: Dict[str, Any]) -> str:
        """Detect the type of content in a result."""
        url = result.get("url", "").lower()
        if any(ext in url for ext in [".pdf", ".doc", ".docx"]):
            return "document"
        elif any(ext in url for ext in [".jpg", ".png", ".gif"]):
            return "image"
        elif "youtube.com" in url or "vimeo.com" in url:
            return "video"
        return "webpage"

    def _select_sources(
        self, 
        results: List[Dict[str, Any]], 
        query_analysis: QueryAnalysis
    ) -> List[Dict[str, Any]]:
        """Select most relevant sources using enhanced criteria."""
        scored_sources = []
        
        for result in results:
            # Base relevance score
            relevance = 0.5
            
            # Title and description presence
            if result.get("title") and result.get("description"):
                relevance += 0.3
                
            # Content type matching
            if query_analysis.input_type:
                content_type = self._detect_content_type(result)
                if content_type == "document" and query_analysis.input_type.primary_type.name == "TECHNICAL":
                    relevance += 0.2
                    
            # Segment matching
            if query_analysis.segmentation and query_analysis.segmentation.segments:
                matches = self._check_segment_matches(result, query_analysis)
                relevance += 0.1 * len(matches)
                
            scored_sources.append({
                "url": result.get("url", ""),
                "relevance": min(relevance, 1.0),
                "content_type": self._detect_content_type(result)
            })
            
        return sorted(scored_sources, key=lambda x: x["relevance"], reverse=True)[:self.min_sources]

    def _calculate_relevance(self, result: Dict[str, Any], query_analysis: QueryAnalysis) -> float:
        """Calculate relevance score for a result."""
        relevance = 0.5
        
        # Content completeness
        if result.get("title") and result.get("description"):
            relevance += 0.2
            
        # Content type matching
        if query_analysis.input_type:
            content_type = self._detect_content_type(result)
            if content_type == "document" and query_analysis.input_type.primary_type.name == "TECHNICAL":
                relevance += 0.2
                
        # Segment matching
        if query_analysis.segmentation and query_analysis.segmentation.segments:
            matches = self._check_segment_matches(result, query_analysis)
            relevance += 0.1 * len(matches)
            
        return min(relevance, 1.0)

    def _check_segment_matches(self, result: Dict[str, Any], query_analysis: QueryAnalysis) -> List[str]:
        """Check which query segments match the result."""
        if not query_analysis.segmentation or not query_analysis.segmentation.segments:
            return []
            
        matches = []
        content = f"{result.get('title', '')} {result.get('description', '')}".lower()
        
        for segment in query_analysis.segmentation.segments:
            if segment.content.lower() in content:
                matches.append(segment.content)
                
        return matches

    def _get_query_suggestions(self, query_analysis: QueryAnalysis) -> List[str]:
        """Generate query suggestions based on analysis."""
        suggestions = []
        
        # Handle ambiguity
        if query_analysis.is_ambiguous and query_analysis.possible_interpretations:
            suggestions.extend([
                f"Did you mean '{interp}'?"
                for interp in query_analysis.possible_interpretations[:2]
            ])
            
        # Handle complexity
        if query_analysis.complexity == "very complex":
            if query_analysis.sub_queries:
                suggestions.append("Try breaking your query into smaller parts:")
                suggestions.extend([f"- {q}" for q in query_analysis.sub_queries[:3]])
                
        # Handle input type
        if query_analysis.input_type:
            if query_analysis.input_type.primary_type.name == "CODE":
                suggestions.append("For code-related queries, try focusing on specific programming concepts or error messages")
            elif query_analysis.input_type.primary_type.name == "TECHNICAL":
                suggestions.append("For technical queries, try including specific technologies or frameworks")
                
        return suggestions