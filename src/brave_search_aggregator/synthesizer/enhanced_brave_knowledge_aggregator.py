"""
Enhanced Brave Knowledge Aggregator for Phase 2 content enhancement.
Builds upon the streaming foundation from Phase 1 to include content fetching and analysis.
"""
import logging
import time
import asyncio
from typing import Dict, List, Set, Any, Optional, AsyncGenerator, Union, Tuple
from datetime import datetime
import json

from ..utils.config import Config
from ..utils.error_handler import ErrorHandler, ErrorContext
from ..fetcher.brave_client import BraveSearchClient
from ..fetcher.content_fetcher import ContentFetcher
from ..analyzer.query_analyzer import QueryAnalyzer
from .content_analyzer import ContentAnalyzer, AnalysisResult
from .enhanced_knowledge_synthesizer import EnhancedKnowledgeSynthesizer, SynthesisResult

logger = logging.getLogger(__name__)

class EnhancedBraveKnowledgeAggregator:
    """
    Enhanced Brave Knowledge Aggregator with content enhancement capabilities.
    Orchestrates the process of searching, fetching content, analyzing, and synthesizing knowledge.
    """
    
    def __init__(
        self, 
        brave_client: BraveSearchClient, 
        config: Config,
        content_fetcher: Optional[ContentFetcher] = None,
        content_analyzer: Optional[ContentAnalyzer] = None,
        knowledge_synthesizer: Optional[EnhancedKnowledgeSynthesizer] = None,
        query_analyzer: Optional[QueryAnalyzer] = None
    ):
        """
        Initialize the enhanced Brave Knowledge Aggregator.
        
        Args:
            brave_client: BraveSearchClient instance for API access
            config: Configuration object
            content_fetcher: Optional ContentFetcher instance (created if not provided)
            content_analyzer: Optional ContentAnalyzer instance (created if not provided)
            knowledge_synthesizer: Optional EnhancedKnowledgeSynthesizer instance (created if not provided)
            query_analyzer: Optional QueryAnalyzer instance (created if not provided)
        """
        self.brave_client = brave_client
        self.config = config
        
        # Initialize components if not provided
        self.query_analyzer = query_analyzer or QueryAnalyzer(config)
        self.content_fetcher = content_fetcher or ContentFetcher(self.brave_client.session, config)
        self.content_analyzer = content_analyzer or ContentAnalyzer(config)
        self.knowledge_synthesizer = knowledge_synthesizer or EnhancedKnowledgeSynthesizer(config)
        
        # Error handling
        self.error_handler = ErrorHandler()
        self.error_handler.register_recovery_strategy(
            Exception,
            self._handle_general_error
        )
        
        # Streaming metrics
        self.streaming_metrics = {
            'start_time': None,
            'last_event_time': None,
            'events_emitted': 0,
            'total_delay_ms': 0,
            'max_delay_ms': 0,
            'average_delay_ms': 0
        }
    
    async def process_query(
        self, 
        query: str, 
        enable_content_enhancement: bool = True
    ) -> AsyncGenerator[Dict[str, Union[str, bool, Dict[str, Any]]], None]:
        """
        Process a search query with content enhancement.
        
        Args:
            query: The search query
            enable_content_enhancement: Whether to enable content enhancement (Phase 2)
            
        Yields:
            Status updates, search results, and synthesized knowledge
        """
        try:
            # Reset streaming metrics for this query
            self._reset_streaming_metrics()
            
            # Get query analysis first
            query_analysis = await self.query_analyzer.analyze_query(query)
            
            # Yield initial status with enhanced analysis
            yield {
                "type": "content",
                "content_type": "analysis_status",
                "stage": "analysis_complete",
                "message": f"Analyzed query: {query}",
                "query_analysis": {
                    "optimized_query": query_analysis.search_string,
                    "complexity": query_analysis.complexity_score,
                    "confidence": query_analysis.confidence_score,
                    "segments": query_analysis.segments if query_analysis.segments else [],
                    "insights": query_analysis.insights if query_analysis.insights else "",
                    "search_parameters": query_analysis.search_parameters
                }
            }
            await self._track_streaming_event("initial_status")
            
            # Stream search initialization
            yield {
                "type": "content",
                "content_type": "search_status",
                "stage": "search_started",
                "message": f"Searching knowledge sources for: {query}",
                "search_parameters": {
                    "query": query_analysis.search_string,
                    "count": self.config.max_results_per_query
                }
            }
            await self._track_streaming_event("search_started")
            
            # Initialize result tracking
            results = []
            analysis_batch = []
            batch_size = self.config.batch_size
            selected_sources = []
            analyzed_contents = []
            
            # Get search results using async iterator
            search_iterator = self.brave_client.search(query_analysis.search_string)
            
            # Process search results
            async for result in search_iterator:
                # Add to results list
                results.append(result)
                analysis_batch.append(result)
                
                # Stream result to user
                yield {
                    "type": "content",
                    "content_type": "search_result",
                    "index": len(results),
                    "total_so_far": len(results),
                    "result": self._format_result(result)
                }
                await self._track_streaming_event("search_result")
                
                # Perform interim analysis when batch is complete
                if len(analysis_batch) >= batch_size:
                    patterns = self._analyze_patterns(analysis_batch)
                    yield {
                        "type": "content",
                        "content_type": "interim_analysis",
                        "results_analyzed": len(results),
                        "patterns": patterns,
                        "message": "Processing initial results..."
                    }
                    await self._track_streaming_event("interim_analysis")
                    analysis_batch = []
            
            # Perform source selection if we have results
            if results:
                selected_sources = self._select_sources(results, query_analysis)
                yield {
                    "type": "content",
                    "content_type": "source_selection",
                    "stage": "source_selection",
                    "message": f"Selected {len(selected_sources)} most relevant sources",
                    "sources": [
                        {"url": source.get("link", ""), "relevance": relevance, "title": source.get("title", "")}
                        for source, relevance in selected_sources
                    ]
                }
                await self._track_streaming_event("source_selection")
            
            # Phase 2: Content Enhancement
            if enable_content_enhancement and selected_sources:
                # Indicate content fetching is starting
                urls_to_fetch = [source[0].get("link", "") for source in selected_sources if source[0].get("link")]
                yield {
                    "type": "content",
                    "content_type": "fetch_status",
                    "stage": "fetch_started",
                    "message": f"Fetching content from {len(urls_to_fetch)} sources",
                    "urls": urls_to_fetch
                }
                await self._track_streaming_event("fetch_started")
                
                # Fetch content from selected sources
                fetch_count = 0
                async for content in self.content_fetcher.fetch_stream(urls_to_fetch):
                    fetch_count += 1
                    
                    # Stream fetch progress
                    yield {
                        "type": "content",
                        "content_type": "fetch_progress",
                        "completed": fetch_count,
                        "total": len(urls_to_fetch),
                        "url": content["url"],
                        "success": content.get("content_type") != "error",
                        "message": f"Retrieved {fetch_count} of {len(urls_to_fetch)} sources"
                    }
                    await self._track_streaming_event("fetch_progress")
                    
                    # If fetch was successful, analyze the content
                    if content.get("content_type") != "error" and content.get("content", ""):
                        # Indicate analysis is happening
                        yield {
                            "type": "content",
                            "content_type": "analysis_status",
                            "stage": "content_analysis",
                            "message": f"Analyzing content from {content['url']}",
                            "url": content["url"]
                        }
                        await self._track_streaming_event("analysis_status")
                        
                        # Analyze content
                        try:
                            analysis_result = await self.content_analyzer.analyze(content, query)
                            analyzed_contents.append(analysis_result)
                            
                            # Stream analysis result
                            yield {
                                "type": "content",
                                "content_type": "analysis_result",
                                "url": content["url"],
                                "quality_score": analysis_result.quality_score,
                                "relevance_score": analysis_result.relevance_score,
                                "category": analysis_result.category,
                                "sentiment": analysis_result.sentiment,
                                "key_points": analysis_result.key_points[:3],  # Just show top 3 points
                                "is_reliable": analysis_result.is_reliable
                            }
                            await self._track_streaming_event("analysis_result")
                        except Exception as e:
                            logger.error(f"Error analyzing content from {content['url']}: {str(e)}")
                            yield {
                                "type": "content",
                                "content_type": "analysis_error",
                                "url": content["url"],
                                "error": str(e)
                            }
                            await self._track_streaming_event("analysis_error")
                
                # If we have analyzed contents, synthesize them
                if analyzed_contents:
                    # Indicate synthesis is happening
                    yield {
                        "type": "content",
                        "content_type": "synthesis_status",
                        "stage": "knowledge_synthesis",
                        "message": f"Synthesizing knowledge from {len(analyzed_contents)} sources",
                        "sources_count": len(analyzed_contents)
                    }
                    await self._track_streaming_event("synthesis_status")
                    
                    # Synthesize knowledge
                    try:
                        synthesis_result = await self.knowledge_synthesizer.synthesize(analyzed_contents, query)
                        
                        # Stream final synthesis
                        yield {
                            "type": "content",
                            "content_type": "final_synthesis",
                            "content": synthesis_result.content,
                            "confidence_score": synthesis_result.confidence_score,
                            "synthesis_time_ms": synthesis_result.synthesis_time_ms,
                            "sources_count": len(synthesis_result.sources),
                            "key_insights_count": len(synthesis_result.key_insights)
                        }
                        await self._track_streaming_event("final_synthesis")
                    except Exception as e:
                        logger.error(f"Error synthesizing knowledge: {str(e)}")
                        yield {
                            "type": "content",
                            "content_type": "synthesis_error",
                            "error": str(e)
                        }
                        await self._track_streaming_event("synthesis_error")
            else:
                # Phase 1: Basic search result synthesis
                if results:
                    # Format search results for basic synthesis
                    content = self._generate_basic_synthesis(results, query)
                    
                    # Stream basic synthesis
                    yield {
                        "type": "content",
                        "content_type": "search_synthesis",
                        "content": content,
                        "results_count": len(results)
                    }
                    await self._track_streaming_event("search_synthesis")
                else:
                    # No results
                    yield {
                        "type": "content",
                        "content_type": "no_results",
                        "content": f"No results found for: {query}",
                        "message": "No results found"
                    }
                    await self._track_streaming_event("no_results")
            
            # Final metrics
            if self.config.enable_streaming_metrics:
                metrics = self._get_streaming_metrics()
                yield {
                    "type": "content",
                    "content_type": "metrics",
                    "message": "Stream processing complete",
                    "metrics": metrics
                }
                await self._track_streaming_event("metrics")
        
        except Exception as e:
            # Handle general error
            error_context = ErrorContext(
                operation="process_query",
                partial_results={
                    "query": query,
                    "results_count": len(results) if 'results' in locals() else 0,
                    "analyzed_count": len(analyzed_contents) if 'analyzed_contents' in locals() else 0
                },
                metadata={
                    "enable_content_enhancement": enable_content_enhancement,
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )
            logger.error(f"Error processing query: {str(e)}")
            
            # Try to handle error and return partial results
            error_result = await self.error_handler.handle_error(e, error_context)
            
            # Yield error result
            yield {
                "type": "content",
                "content_type": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "partial_results": error_result.get("partial_results", {}),
                "recoverable": error_result.get("recoverable", False)
            }
            await self._track_streaming_event("error")
    
    def _format_result(self, result: Dict[str, str]) -> Dict[str, str]:
        """
        Format a search result for display.
        
        Args:
            result: The search result to format
            
        Returns:
            Formatted search result
        """
        return {
            "title": result.get("title", ""),
            "description": result.get("description", ""),
            "url": result.get("link", ""),
            "display_url": result.get("display_link", ""),
            "age": result.get("age", ""),
            "favicon": result.get("favicon", "")
        }
    
    def _format_result_as_content(self, result: Dict[str, str]) -> str:
        """
        Format a search result as content text.
        
        Args:
            result: The search result to format
            
        Returns:
            Formatted search result as text
        """
        return f"## {result.get('title', '')}\n\n" \
               f"{result.get('description', '')}\n\n" \
               f"[{result.get('display_link', '')}]({result.get('link', '')})"
    
    def _analyze_patterns(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Analyze patterns in search results.
        
        Args:
            results: List of search results to analyze
            
        Returns:
            List of patterns found
        """
        # Skip if no results
        if not results:
            return []
        
        # Extract text from results
        titles = [result.get("title", "") for result in results]
        descriptions = [result.get("description", "") for result in results]
        
        # Extract common terms from titles and descriptions
        title_terms = self._extract_common_terms(titles)
        description_terms = self._extract_common_terms(descriptions)
        
        # Combine patterns
        patterns = []
        
        # Add title patterns
        if title_terms:
            patterns.append(f"Common terms in titles: {', '.join(title_terms[:5])}")
        
        # Add description patterns
        if description_terms:
            patterns.append(f"Common terms in descriptions: {', '.join(description_terms[:5])}")
        
        return patterns
    
    def _extract_common_terms(self, texts: List[str]) -> List[str]:
        """
        Extract common terms from a list of texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of common terms
        """
        # Skip if no texts
        if not texts:
            return []
        
        # Combine texts
        all_text = " ".join(texts).lower()
        
        # Split into words
        words = all_text.split()
        
        # Remove common words
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about",
                       "of", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
                       "did", "will", "would", "should", "can", "could", "may", "might", "must", "shall", "should"}
        
        # Count word frequencies
        word_counts = {}
        for word in words:
            # Skip short words and common words
            if len(word) <= 3 or word in common_words:
                continue
            
            # Count occurrence
            if word not in word_counts:
                word_counts[word] = 0
            word_counts[word] += 1
        
        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Extract top words
        top_words = [word for word, count in sorted_words[:10] if count > 1]
        
        return top_words
    
    def _detect_content_type(self, result: Dict[str, Any]) -> str:
        """
        Detect content type from a search result.
        
        Args:
            result: The search result to analyze
            
        Returns:
            Detected content type
        """
        # Get URL
        url = result.get("link", "")
        
        # Check URL patterns
        if "youtube.com" in url or "youtu.be" in url or "vimeo.com" in url:
            return "video"
        elif "wikipedia.org" in url:
            return "encyclopedia"
        elif "github.com" in url:
            return "code_repository"
        elif "stackoverflow.com" in url:
            return "q_and_a"
        elif "docs." in url or "documentation" in url:
            return "documentation"
        elif "blog." in url or "medium.com" in url:
            return "blog"
        elif ".edu" in url:
            return "educational"
        elif ".gov" in url:
            return "government"
        elif "news." in url or "cnn.com" in url or "bbc." in url or "nytimes.com" in url:
            return "news"
        else:
            return "webpage"
    
    def _select_sources(self, results: List[Dict[str, Any]], query_analysis: Any) -> List[Tuple[Dict[str, Any], float]]:
        """
        Select the most relevant sources from search results.
        
        Args:
            results: List of search results
            query_analysis: Query analysis result
            
        Returns:
            List of selected sources with relevance scores
        """
        # Skip if no results
        if not results:
            return []
        
        # Calculate relevance for each result
        scored_results = []
        for result in results:
            relevance = self._calculate_relevance(result, query_analysis)
            scored_results.append((result, relevance))
        
        # Sort by relevance
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results (maximum 5)
        return scored_results[:5]
    
    def _calculate_relevance(self, result: Dict[str, Any], query_analysis: Any) -> float:
        """
        Calculate relevance score for a search result.
        
        Args:
            result: The search result to score
            query_analysis: Query analysis result
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Extract result components
        title = result.get("title", "").lower()
        description = result.get("description", "").lower()
        url = result.get("link", "").lower()
        
        # Calculate base score
        base_score = 0.5  # Start with middle score
        
        # Add score for title match
        if query_analysis.search_string.lower() in title:
            base_score += 0.3
        
        # Add score for description match
        if query_analysis.search_string.lower() in description:
            base_score += 0.2
        
        # Check segment matches
        segment_matches = self._check_segment_matches(result, query_analysis)
        segment_score = len(segment_matches) / max(1, len(query_analysis.segments or []))
        base_score += segment_score * 0.2
        
        # Add score for content type
        content_type = self._detect_content_type(result)
        if content_type in ["documentation", "encyclopedia", "educational"]:
            base_score += 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))
    
    def _check_segment_matches(self, result: Dict[str, Any], query_analysis: Any) -> List[str]:
        """
        Check which query segments match a result.
        
        Args:
            result: The search result to check
            query_analysis: Query analysis result
            
        Returns:
            List of matching segment texts
        """
        # Skip if no segments
        if not hasattr(query_analysis, "segments") or not query_analysis.segments:
            return []
        
        # Extract result components
        title = result.get("title", "").lower()
        description = result.get("description", "").lower()
        combined = title + " " + description
        
        # Check each segment
        matches = []
        for segment in query_analysis.segments:
            segment_text = segment.get("text", "").lower()
            if segment_text and segment_text in combined:
                matches.append(segment_text)
        
        return matches
    
    def _generate_basic_synthesis(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        Generate a basic synthesis of search results.
        
        Args:
            results: List of search results
            query: The original query
            
        Returns:
            Synthesized content
        """
        # Skip if no results
        if not results:
            return f"No results found for: {query}"
        
        # Start with introduction
        synthesis = [f"Search results for: {query}"]
        
        # Add results
        for i, result in enumerate(results[:5], 1):  # Include only top 5 results
            result_content = self._format_result_as_content(result)
            synthesis.append(f"{result_content}\n")
        
        # Add reference
        synthesis.append(f"\nResults from Brave Search ({len(results)} total results)")
        
        # Combine
        return "\n\n".join(synthesis)
    
    def _get_query_suggestions(self, query_analysis: Any) -> List[str]:
        """
        Get query suggestions based on query analysis.
        
        Args:
            query_analysis: Query analysis result
            
        Returns:
            List of query suggestions
        """
        # Skip if no insights
        if not hasattr(query_analysis, "insights") or not query_analysis.insights:
            return []
        
        # Split insights by sentence
        sentences = query_analysis.insights.split(".")
        
        # Extract suggestions
        suggestions = []
        for sentence in sentences:
            if "try" in sentence.lower() or "consider" in sentence.lower() or "suggest" in sentence.lower():
                suggestions.append(sentence.strip())
        
        return suggestions
    
    async def _track_streaming_event(self, event_type: str) -> None:
        """
        Track streaming event metrics.
        
        Args:
            event_type: Type of event
        """
        if not self.config.enable_streaming_metrics:
            return
        
        # Get current time in milliseconds
        current_time = time.time() * 1000
        
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
        
        # Calculate average delay
        if self.streaming_metrics['events_emitted'] > 0:
            self.streaming_metrics['average_delay_ms'] = self.streaming_metrics['total_delay_ms'] / self.streaming_metrics['events_emitted']
        
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
    
    def _reset_streaming_metrics(self) -> None:
        """Reset streaming metrics for a new query."""
        self.streaming_metrics = {
            'start_time': None,
            'last_event_time': None,
            'events_emitted': 0,
            'total_delay_ms': 0,
            'max_delay_ms': 0,
            'average_delay_ms': 0
        }
    
    def _get_streaming_metrics(self) -> Dict[str, Any]:
        """
        Get current streaming metrics.
        
        Returns:
            Streaming metrics
        """
        metrics = self.streaming_metrics.copy()
        
        # Calculate total time if we have a start time
        if metrics['start_time'] is not None and metrics['last_event_time'] is not None:
            metrics['total_time_ms'] = metrics['last_event_time'] - metrics['start_time']
        else:
            metrics['total_time_ms'] = 0
        
        return metrics
    
    async def _handle_general_error(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """
        Handle general errors and create recovery response.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            Recovery response
        """
        logger.error(f"Handling general error: {str(error)}")
        
        # Extract partial results if available
        partial_results = {}
        if hasattr(context, "partial_results") and context.partial_results:
            partial_results = context.partial_results
        
        # Create recovery response
        return {
            "error": str(error),
            "error_type": type(error).__name__,
            "partial_results": partial_results,
            "recoverable": False,
            "timestamp": time.time()
        }
