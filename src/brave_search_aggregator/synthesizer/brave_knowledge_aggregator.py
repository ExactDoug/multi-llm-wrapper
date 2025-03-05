from typing import AsyncGenerator, Dict, List, Optional, Union, Any
from datetime import datetime
import logging
import asyncio
import time

from ..analyzer.query_analyzer import QueryAnalyzer, QueryAnalysis
from ..fetcher.brave_client import BraveSearchClient
from .knowledge_synthesizer import KnowledgeSynthesizer
from ..utils.config import Config, AnalyzerConfig
from ..utils.error_handler import ErrorHandler, ErrorContext
from ..utils.resource_manager import ResourceManager

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
        self.error_handler = ErrorHandler()
        self.resource_manager = ResourceManager(max_memory_mb=config.max_memory_mb)

        # Initialize streaming metrics
        self.streaming_metrics = {
            'start_time': None,
            'last_event_time': None,
            'events_emitted': 0,
            'total_chunks': 0,
            'total_delay_ms': 0,
            'max_delay_ms': 0
        }

    async def process_query(
        self, query: str
    ) -> AsyncGenerator[Dict[str, Union[str, bool, Dict[str, Any]]], None]:
        try:
            # Initialize streaming metrics
            if self.config.enable_streaming_metrics:
                self.streaming_metrics = {
                    'start_time': None,
                    'last_event_time': None,
                    'events_emitted': 0,
                    'total_chunks': 0,
                    'total_delay_ms': 0,
                    'max_delay_ms': 0
                }

            # Get enhanced query analysis
            query_analysis = await self.query_analyzer.analyze_query(query)

            # Initial status with enhanced analysis
            await self._track_streaming_event("analysis_complete")
            yield {
                "type": "content",
                "content": f"Query Analysis: {query_analysis.insights if query_analysis.insights else 'Analyzing query...'}",
                "message": f"Analyzed query: {query}",
                "timestamp": datetime.now().isoformat(),
                "query_analysis": {
                    "complexity": query_analysis.complexity,
                    "is_ambiguous": query_analysis.is_ambiguous,
                    "input_type": query_analysis.input_type.primary_type.name if query_analysis.input_type else None,
                    "confidence": query_analysis.input_type.confidence if query_analysis.input_type else None,
                    "insights": query_analysis.insights,
                    "performance_metrics": query_analysis.performance_metrics
                },
                "streaming_metrics": self._get_streaming_metrics() if self.config.enable_streaming_metrics else {}
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
                "type": "content",
                "content": f"Searching knowledge sources for: {query}",
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

            # Memory optimization - use a fixed-size buffer for results
            max_results_to_keep = min(self.config.max_results, 20)  # Limit memory usage

            final_knowledge = None  # Initialize final_knowledge to None
            try:
                # Stream search results - BYPASSING THE ORIGINAL IMPLEMENTATION
                # Create a direct implementation of the search functionality to avoid import issues
                
                # Define a local async iterator class to handle the search results
                class LocalSearchResultIterator:
                    def __init__(self, brave_client, query_string, parent_config=None):
                        self.brave_client = brave_client
                        self.query = query_string
                        self.config = parent_config  # Store parent config for access to API key
                        self._results = []
                        self._index = 0
                        self._initialized = False
                        
                    def __aiter__(self):
                        logger.debug("LocalSearchResultIterator.__aiter__ called!")
                        return self
                        
                    async def __anext__(self):
                        # Initialize on first access
                        if not self._initialized:
                            await self._initialize()
                            
                        # Check if we've reached the end
                        if self._index >= len(self._results):
                            raise StopAsyncIteration
                            
                        # Return the next result
                        result = self._results[self._index]
                        self._index += 1
                        return result
                    
                    async def _initialize(self):
                        logger.debug("LocalSearchResultIterator._initialize called!")
                        self._initialized = True
                        
                        # Call the Brave Search API directly
                        rate_limiter = getattr(self.brave_client, 'rate_limiter', None)
                        if rate_limiter is None:
                            logger.debug("No rate_limiter found in brave_client, creating a new one")
                            # Import locally to avoid circular imports
                            from ..fetcher.brave_client import RateLimiter
                            rate_limiter = RateLimiter(max_rate=20)
                            
                        await rate_limiter.acquire()
                        
                        # Handle different API key locations in different client implementations
                        api_key = None
                        parent_config = self.config  # Store reference to passed config
                        
                        # 1. Try direct api_key attribute (brave_search_aggregator client)
                        if hasattr(self.brave_client, 'api_key'):
                            api_key = self.brave_client.api_key
                            logger.debug("Using API key from brave_client.api_key")
                            
                        # 2. Try config.api_key (multi_llm_wrapper client)
                        if api_key is None and hasattr(self.brave_client, 'config'):
                            client_config = self.brave_client.config
                            if hasattr(client_config, 'api_key'):
                                api_key = client_config.api_key
                                logger.debug("Using API key from brave_client.config.api_key")
                        
                        # 3. Try parent config that was passed in
                        if api_key is None and parent_config is not None:
                            if hasattr(parent_config, 'brave_api_key'):
                                api_key = parent_config.brave_api_key
                                logger.debug("Using API key from parent_config.brave_api_key")
                            
                        # 4. Last resort: environment variable
                        if api_key is None:
                            import os
                            api_key = os.getenv("BRAVE_API_KEY", "")
                            if api_key:
                                logger.debug("Using API key from environment variable")
                            
                        # Verify we have an API key
                        if not api_key:
                            logger.error("No Brave Search API key found. Please check your configuration or environment variables.")
                            raise Exception("No Brave Search API key found")
                        
                        headers = {
                            "Accept": "application/json",
                            "X-Subscription-Token": api_key,
                            "Connection": "keep-alive",
                        }
                        
                        params = {
                            "q": self.query,
                            "count": 20,  # Fixed count for simplicity
                        }
                        
                        # Get attributes with fallbacks for different client implementations
                        session = getattr(self.brave_client, 'session', None)
                        if session is None:
                            logger.debug("No session found in brave_client, creating a new one")
                            import aiohttp
                            session = aiohttp.ClientSession()
                            
                        base_url = getattr(self.brave_client, 'base_url', "https://api.search.brave.com/res/v1/web/search")
                        timeout_value = getattr(self.brave_client, 'timeout', 30)
                        
                        logger.debug(f"Using base_url: {base_url}")
                        logger.debug(f"Using timeout: {timeout_value}")
                        
                        async with session.get(
                            base_url,
                            headers=headers,
                            params=params,
                            timeout=timeout_value,
                        ) as response:
                            if response.status != 200:
                                error_text = await response.text()
                                logger.error(f"Brave Search API error: {error_text}")
                                raise Exception(f"API error: {response.status} - {error_text}")
                                
                            data = await response.json()
                            self._results = data.get("web", {}).get("results", [])
                            logger.debug(f"Fetched {len(self._results)} results directly in LocalSearchResultIterator")
                
                # Create and use our local iterator directly, passing the parent config
                search_iterator = LocalSearchResultIterator(self.brave_client, query_analysis.search_string, self.config)
                logger.debug(f"Created LocalSearchResultIterator: {search_iterator}")
                
                # Now iterate over the custom iterator
                async for result in search_iterator:
                    # Memory optimization - only keep the most recent results
                    if len(results) >= max_results_to_keep:
                        # Keep track of total count but limit memory usage
                        results.pop(0)  # Remove oldest result

                    results.append(result)

                    # Track streaming metrics
                    self.streaming_metrics['total_chunks'] += 1

                    # Stream individual result with enhanced context
                    await self._track_streaming_event("search_result")
                    formatted_result = self._format_result(result)

                    # Memory optimization - explicitly clear any large temporary objects
                    if 'large_temp_data' in result:
                        del result['large_temp_data']
                    yield {
                        "type": "content",
                        "index": len(results),
                        "total_so_far": len(results),
                        "timestamp": datetime.now().isoformat(),
                        "content": self._format_result_as_content(formatted_result),
                        "result": formatted_result,
                        "context": {
                            "relevance_score": self._calculate_relevance(result, query_analysis),
                            "matches_segments": self._check_segment_matches(result, query_analysis)
                        },
                        "progress": {
                            "percentage": min(100, (len(results) * 100) // self.config.max_results),
                            "current": len(results),
                            "total": self.config.max_results
                        } if self.config.enable_progress_tracking else {},
                        "streaming_metrics": self._get_streaming_metrics() if self.config.enable_streaming_metrics else {}
                    }
                    # Batch analysis based on configuration
                    if len(analysis_batch) >= self.config.streaming_batch_size:
                        patterns = self._analyze_patterns(analysis_batch)
                        interim_knowledge = await self.knowledge_synthesizer.synthesize(analysis_batch)

                        if patterns or interim_knowledge:
                            await self._track_streaming_event("interim_analysis")
                            yield {
                                "type": "content",
                                "content": self._get_result_content(interim_knowledge, f"Analyzed {len(results)} results: {', '.join(patterns[:3]) if patterns else 'No patterns detected'}"),
                                "patterns": patterns,
                                "synthesis": self._get_result_content(interim_knowledge),
                                "performance": {
                                    "batch_size": len(analysis_batch),
                                    "processing_time": query_analysis.performance_metrics.get("processing_time_ms")
                                },
                                "progress": {
                                    "percentage": min(100, (len(results) * 100) // self.config.max_results),
                                    "current": len(results),
                                    "total": self.config.max_results
                                } if self.config.enable_progress_tracking else {},
                                "streaming_metrics": self._get_streaming_metrics() if self.config.enable_streaming_metrics else {}
                            }
                        analysis_batch = []

                    # Source selection when minimum reached
                    if len(results) >= self.min_sources and not selected_sources:
                        selected_sources = self._select_sources(results, query_analysis)
                        await self._track_streaming_event("source_selection")
                        yield {
                            "type": "content",
                            "message": f"Selected {len(selected_sources)} most relevant sources",
                            "sources": selected_sources,
                            "selection_criteria": {
                                "relevance_threshold": 0.7,
                                "diversity_factor": 0.3
                            },
                            "progress": {
                                "percentage": min(100, (len(results) * 100) // self.config.max_results),
                                "current": len(results),
                                "total": self.config.max_results
                            } if self.config.enable_progress_tracking else {},
                            "streaming_metrics": self._get_streaming_metrics() if self.config.enable_streaming_metrics else {}
                        }

                if not results:
                    yield {
                        "type": "error",
                        "error": "No search results found",
                        "suggestions": self._get_query_suggestions(query_analysis)
                    }
                    return

                # Final knowledge synthesis with enhanced context
                final_knowledge = await self.knowledge_synthesizer.synthesize(query, results)
                await self._track_streaming_event("final_synthesis")
                
                # Ensure dictionary format and convert from SynthesisResult object if needed
                final_result = self._ensure_dict_response(final_knowledge)
                
                # Add additional metadata
                final_result["total_results"] = len(results)
                final_result["analysis_summary"] = {
                    "complexity": query_analysis.complexity,
                    "ambiguity_handled": query_analysis.is_ambiguous,
                    "segments_analyzed": len(query_analysis.sub_queries) if query_analysis.sub_queries else 0,
                    "performance_metrics": query_analysis.performance_metrics
                }
                
                if self.config.enable_progress_tracking:
                    final_result["progress"] = {
                        "percentage": 100,  # Final synthesis is complete
                        "current": len(results),
                        "total": self.config.max_results
                    }
                    
                if self.config.enable_streaming_metrics:
                    final_result["streaming_metrics"] = self._get_streaming_metrics()
                    
                yield final_result
            except Exception as e:
                # Stream error with enhanced context using error handler
                logger.error(f"Error in search processing: {str(e)}", exc_info=True)
                error_context = ErrorContext(
                    operation="process_query.search",
                    partial_results=[self._format_result(r) for r in results],
                    metadata={
                        "query": query,
                        "stage": "search_processing",
                        "query_analysis": {
                            "complexity": query_analysis.complexity,
                            "is_ambiguous": query_analysis.is_ambiguous,
                            "input_type": query_analysis.input_type.primary_type.name if query_analysis.input_type else None
                        }
                    }
                )
                yield await self.error_handler.handle_error(e, error_context)
        except Exception as e:
            logger.error(f"Error in query processing: {str(e)}", exc_info=True)
            error_context = ErrorContext(
                operation="process_query",
                metadata={
                    "query": query,
                    "stage": "query_analysis",
                    "error_details": str(e)
                }
            )
            yield await self.error_handler.handle_error(e, error_context)

    def _format_result(self, result: Dict[str, str]) -> Dict[str, str]:
        """Format a single search result."""
        return {
            "title": result.get("title", "No title"),
            "description": result.get("description", "No description"),
            "url": result.get("url", "No URL")
        }

    def _format_result_as_content(self, result: Dict[str, str]) -> str:
        """Format a search result for the content field."""
        if not result:
            return "No result available"
        
        title = result.get("title", "No title")
        description = result.get("description", "No description")
        url = result.get("url", "No URL")
        
        return f"**{title}**\n{description}\n[{url}]({url})"

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
        content = f"{result.get('title', '')} {result.get('description', '')}.lower()"
        
        for segment in query_analysis.segmentation.segments:
            if segment.content.lower() in content:
                matches.append(segment.content)
        return matches

    async def _track_streaming_event(self, event_type: str) -> None:
        """Track streaming event metrics and enforce timing constraints."""
        if not self.config.enable_streaming_metrics:
            return

        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Initialize metrics if this is the first event
        if self.streaming_metrics['start_time'] is None:
            self.streaming_metrics['start_time'] = current_time
            self.streaming_metrics['last_event_time'] = current_time
            return

        # Calculate delay since last event
        delay = current_time - self.streaming_metrics['last_event_time']
        self.streaming_metrics['total_delay_ms'] += delay
        self.streaming_metrics['max_delay_ms'] = max(self.streaming_metrics['max_delay_ms'], delay)
        
        # Update metrics
        self.streaming_metrics['events_emitted'] += 1
        self.streaming_metrics['last_event_time'] = current_time

        # Apply event delay if configured, ensuring we don't exceed the max delay
        if self.config.max_event_delay_ms > 0:
            # Calculate the actual delay needed to maintain consistent timing
            target_delay_ms = self.config.max_event_delay_ms
            
            # If we're already running slow, reduce the delay to catch up
            if delay > target_delay_ms:
                # No additional delay needed
                pass
            else:
                # Add just enough delay to reach the target
                compensation_delay = max(0, target_delay_ms - delay)
                if compensation_delay > 0:
                    await asyncio.sleep(compensation_delay / 1000)  # Convert to seconds

    def _get_streaming_metrics(self) -> Dict[str, Any]:
        """Get current streaming metrics."""
        if not self.config.enable_streaming_metrics or self.streaming_metrics['start_time'] is None:
            return {}
        
        current_time = time.time() * 1000
        total_time = current_time - self.streaming_metrics['start_time']
        
        return {
            'total_events': self.streaming_metrics['events_emitted'],
            'total_chunks': self.streaming_metrics['total_chunks'],
            'average_delay_ms': (self.streaming_metrics['total_delay_ms'] / 
                                max(1, self.streaming_metrics['events_emitted'])),
            'max_delay_ms': self.streaming_metrics['max_delay_ms'],
            'total_time_ms': total_time,
            'events_per_second': (self.streaming_metrics['events_emitted'] * 1000 / 
                                   max(1, total_time))
        }

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
        
    def _get_result_content(self, result, default_content="No results available"):
        """Safely extract content from SynthesisResult or dictionary."""
        if result is None:
            return default_content
            
        # Try various ways to access the content
        # 1. If it has a 'content' attribute
        if hasattr(result, 'content'):
            return result.content
            
        # 2. If it has a 'get' method (dict-like)
        if hasattr(result, 'get'):
            content = result.get('content')
            if content is not None:
                return content
                
        # 3. If it's a dict with 'content' key
        if isinstance(result, dict) and 'content' in result:
            return result['content']
            
        # 4. If it's a string itself
        if isinstance(result, str):
            return result
            
        # 5. As a last resort, convert to string
        return str(result) if result else default_content
        
    def _ensure_dict_response(self, result):
        """Convert any SynthesisResult objects to dictionaries for consistency."""
        if result is None:
            return {"type": "content", "content": "No results available"}
            
        # If it's a SynthesisResult, convert to dict
        if hasattr(result, 'content') and not isinstance(result, dict):
            return {
                "type": "content",
                "content": result.content if hasattr(result, 'content') else str(result),
                "confidence": result.confidence_score if hasattr(result, 'confidence_score') else 1.0,
                "sources": result.sources if hasattr(result, 'sources') else [],
                "mode": result.mode.value if hasattr(result, 'mode') and result.mode else "research"
            }
            
        # If it's already a dict but missing type, add it
        if isinstance(result, dict):
            if "type" not in result:
                result["type"] = "content"
            return result
            
        # If it's a string, wrap it
        if isinstance(result, str):
            return {"type": "content", "content": result}
            
        # Last resort: convert to string
        return {"type": "content", "content": str(result) if result else "No results available"}