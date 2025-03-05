"""
Enhanced knowledge synthesizer for combining insights from multiple content analyses.
"""
import logging
import time
import asyncio
from typing import Dict, List, Set, Any, Optional, AsyncIterator, Tuple
from dataclasses import dataclass, field
from collections import Counter

from ..utils.config import Config
from ..utils.error_handler import ErrorHandler, ErrorContext
from .content_analyzer import AnalysisResult

logger = logging.getLogger(__name__)

class SynthesisError(Exception):
    """Exception raised for synthesis errors."""
    pass

@dataclass
class SynthesisResult:
    """Result of knowledge synthesis."""
    content: str
    sources: List[str]
    key_insights: List[str]
    source_quality: Dict[str, float]
    entity_map: Dict[str, List[str]]
    synthesis_time_ms: float
    confidence_score: float
    processing_metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedKnowledgeSynthesizer:
    """
    Synthesizes knowledge from multiple analyzed content sources.
    Combines insights, entities, and other data points into coherent knowledge.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the knowledge synthesizer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.error_handler = ErrorHandler()
        
        # Register error recovery strategies
        self.error_handler.register_recovery_strategy(
            SynthesisError,
            self._handle_synthesis_error
        )
    
    async def synthesize(self, analyses: List[AnalysisResult], query: Optional[str] = None) -> SynthesisResult:
        """
        Synthesize knowledge from multiple analysis results.
        
        Args:
            analyses: List of content analysis results
            query: Optional query for context
            
        Returns:
            SynthesisResult containing synthesized knowledge
        """
        try:
            start_time = time.time()
            
            # Skip if no analyses
            if not analyses:
                raise SynthesisError("No content analyses to synthesize")
            
            # Extract key insights across all analyses
            key_insights = await self._extract_key_insights(analyses, query)
            
            # Build entity map
            entity_map = await self._build_entity_map(analyses)
            
            # Calculate source quality mapping
            source_quality = {
                analysis.source_url: analysis.quality_score
                for analysis in analyses
            }
            
            # Generate synthesis content
            synthesis_content = await self._generate_synthesis(analyses, key_insights, query)
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence(analyses)
            
            # Calculate processing time
            synthesis_time_ms = round((time.time() - start_time) * 1000)
            
            # Create source list
            sources = [analysis.source_url for analysis in analyses]
            
            # Create result
            result = SynthesisResult(
                content=synthesis_content,
                sources=sources,
                key_insights=key_insights,
                source_quality=source_quality,
                entity_map=entity_map,
                synthesis_time_ms=synthesis_time_ms,
                confidence_score=confidence_score,
                processing_metadata={
                    "timestamp": time.time(),
                    "synthesizer_version": "0.1.0",
                    "query": query,
                    "num_sources": len(analyses),
                    "average_quality": sum(source_quality.values()) / len(source_quality) if source_quality else 0
                }
            )
            
            return result
        
        except Exception as e:
            # Handle error with context
            error_context = ErrorContext(
                operation="synthesize_knowledge",
                partial_results={
                    "num_analyses": len(analyses),
                    "query": query
                },
                metadata={
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )
            logger.error(f"Error synthesizing knowledge: {str(e)}")
            
            # Try to recover with error handler
            try:
                return await self.error_handler.handle_error(e, error_context)
            except Exception as recovery_error:
                # If recovery fails, raise original error
                logger.error(f"Error recovery failed: {str(recovery_error)}")
                raise SynthesisError(f"Synthesis failed: {str(e)}")
    
    async def _extract_key_insights(self, analyses: List[AnalysisResult], query: Optional[str] = None) -> List[str]:
        """
        Extract key insights from multiple analyses.
        
        Args:
            analyses: List of content analysis results
            query: Optional query for relevance filtering
            
        Returns:
            List of key insights
        """
        # Collect all key points from all analyses
        all_key_points = []
        for analysis in analyses:
            all_key_points.extend([(point, analysis.source_url, analysis.relevance_score) for point in analysis.key_points])
        
        # Filter out duplicates and near-duplicates
        unique_insights = []
        seen_content = set()
        
        for point, source, relevance in all_key_points:
            # Skip if too similar to existing insights
            point_lower = point.lower()
            is_unique = True
            
            for existing in seen_content:
                # Check for significant overlap (simple approach)
                if len(set(point_lower.split()) & set(existing.split())) / len(set(point_lower.split())) > 0.7:
                    is_unique = False
                    break
            
            if is_unique:
                seen_content.add(point_lower)
                unique_insights.append((point, source, relevance))
        
        # Sort insights by relevance and quality
        if query:
            # If query provided, prioritize by relevance
            unique_insights.sort(key=lambda x: x[2], reverse=True)
        
        # Extract just the insight text, keeping original formatting
        insights = [insight[0] for insight in unique_insights]
        
        # Limit number of insights
        max_insights = min(len(insights), 10)  # Maximum 10 insights
        return insights[:max_insights]
    
    async def _build_entity_map(self, analyses: List[AnalysisResult]) -> Dict[str, List[str]]:
        """
        Build a mapping of entities to their sources.
        
        Args:
            analyses: List of content analysis results
            
        Returns:
            Dictionary mapping entity strings to source URLs
        """
        entity_map = {}
        
        # Process each analysis
        for analysis in analyses:
            source_url = analysis.source_url
            
            # Add entities to map
            for entity in analysis.entities:
                if entity not in entity_map:
                    entity_map[entity] = []
                entity_map[entity].append(source_url)
        
        return entity_map
    
    async def _generate_synthesis(self, analyses: List[AnalysisResult], key_insights: List[str], query: Optional[str] = None) -> str:
        """
        Generate synthesized content from analyses and key insights.
        
        Args:
            analyses: List of content analysis results
            key_insights: Extracted key insights
            query: Optional query for context
            
        Returns:
            Synthesized content as string
        """
        # Determine predominant sentiment and category
        sentiment_counter = Counter(analysis.sentiment for analysis in analyses)
        category_counter = Counter(analysis.category for analysis in analyses)
        
        predominant_sentiment = sentiment_counter.most_common(1)[0][0] if sentiment_counter else "neutral"
        predominant_category = category_counter.most_common(1)[0][0] if category_counter else "general"
        
        # Build synthesis sections
        sections = []
        
        # 1. Introduction
        if query:
            introduction = f"Based on information from {len(analyses)} sources about '{query}':"
        else:
            introduction = f"Based on information from {len(analyses)} sources:"
        sections.append(introduction)
        
        # 2. Key Insights section
        if key_insights:
            insights_section = "\n\n## Key Insights\n\n"
            for i, insight in enumerate(key_insights, 1):
                insights_section += f"{i}. {insight}\n"
            sections.append(insights_section)
        
        # 3. Main perspectives section (based on sentiment)
        perspective_sections = {}
        
        # Group analyses by sentiment
        sentiment_groups = {}
        for analysis in analyses:
            if analysis.sentiment not in sentiment_groups:
                sentiment_groups[analysis.sentiment] = []
            sentiment_groups[analysis.sentiment].append(analysis)
        
        # Generate perspective sections for different sentiments
        if "positive" in sentiment_groups and len(sentiment_groups["positive"]) > 0:
            positive_points = self._extract_sentiment_points(sentiment_groups["positive"], "positive")
            if positive_points:
                perspective_sections["Positive Perspectives"] = positive_points
        
        if "negative" in sentiment_groups and len(sentiment_groups["negative"]) > 0:
            negative_points = self._extract_sentiment_points(sentiment_groups["negative"], "negative")
            if negative_points:
                perspective_sections["Challenges and Concerns"] = negative_points
        
        if "neutral" in sentiment_groups and len(sentiment_groups["neutral"]) > 0:
            neutral_points = self._extract_sentiment_points(sentiment_groups["neutral"], "neutral")
            if neutral_points:
                perspective_sections["Neutral Information"] = neutral_points
        
        # Add perspective sections to synthesis
        for title, points in perspective_sections.items():
            section_text = f"\n\n## {title}\n\n"
            for point in points:
                section_text += f"- {point}\n"
            sections.append(section_text)
        
        # 4. Technical information (if category is technical or educational)
        if predominant_category in ["technical", "educational"]:
            technical_points = []
            for analysis in analyses:
                # Extract technical information from summaries and key points
                for key_point in analysis.key_points:
                    # Look for technical indicators
                    technical_indicators = ["how to", "implementation", "technique", "method", 
                                            "approach", "technology", "framework", "library", 
                                            "version", "specification", "function", "code"]
                    if any(indicator in key_point.lower() for indicator in technical_indicators):
                        technical_points.append(key_point)
            
            if technical_points:
                technical_section = "\n\n## Technical Details\n\n"
                for point in technical_points[:5]:  # Limit to 5 technical points
                    technical_section += f"- {point}\n"
                sections.append(technical_section)
        
        # 5. Sources section
        sources_section = "\n\n## Sources\n\n"
        for i, analysis in enumerate(sorted(analyses, key=lambda a: a.quality_score, reverse=True), 1):
            source_url = analysis.source_url
            quality_indicator = ""
            if analysis.quality_score >= 0.8:
                quality_indicator = " (High quality)"
            elif analysis.quality_score >= 0.6:
                quality_indicator = " (Medium quality)"
            sources_section += f"{i}. [{source_url}]{quality_indicator}\n"
        sections.append(sources_section)
        
        # Combine all sections
        synthesis = "\n".join(sections)
        
        return synthesis
    
    def _extract_sentiment_points(self, analyses: List[AnalysisResult], sentiment_type: str) -> List[str]:
        """
        Extract points from analyses of a specific sentiment type.
        
        Args:
            analyses: List of content analysis results with the specified sentiment
            sentiment_type: Type of sentiment (positive, negative, neutral)
            
        Returns:
            List of extracted points
        """
        points = []
        seen_content = set()
        
        # Extract points from each analysis
        for analysis in analyses:
            for key_point in analysis.key_points:
                # Check if this point is unique
                key_point_lower = key_point.lower()
                is_unique = True
                
                for existing in seen_content:
                    # Simple overlap check
                    overlap_ratio = len(set(key_point_lower.split()) & set(existing.split())) / len(set(key_point_lower.split()))
                    if overlap_ratio > 0.6:  # 60% overlap threshold
                        is_unique = False
                        break
                
                if is_unique:
                    seen_content.add(key_point_lower)
                    points.append(key_point)
        
        # If no direct key points found, extract from summaries
        if not points:
            for analysis in analyses:
                # Try to extract a sentence from the summary
                sentences = [s.strip() + '.' for s in analysis.summary.split('.') if s.strip()]
                for sentence in sentences[:2]:  # Use at most 2 sentences per summary
                    # Check for uniqueness
                    sentence_lower = sentence.lower()
                    is_unique = True
                    
                    for existing in seen_content:
                        overlap_ratio = len(set(sentence_lower.split()) & set(existing.split())) / len(set(sentence_lower.split()))
                        if overlap_ratio > 0.6:
                            is_unique = False
                            break
                    
                    if is_unique:
                        seen_content.add(sentence_lower)
                        points.append(sentence)
        
        # Limit number of points
        return points[:7]  # Maximum 7 points per sentiment
    
    async def _calculate_confidence(self, analyses: List[AnalysisResult]) -> float:
        """
        Calculate confidence score for the synthesis.
        
        Args:
            analyses: List of content analysis results
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Confidence factors
        factors = {
            "source_quality": 0.0,  # Average quality score of sources
            "source_count": 0.0,    # Number of sources factor
            "consistency": 0.0,     # Consistency across sources
            "reliability": 0.0      # Reliability of sources
        }
        
        # 1. Source quality factor
        quality_scores = [analysis.quality_score for analysis in analyses]
        factors["source_quality"] = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # 2. Source count factor (more sources = higher confidence, up to a point)
        source_count = len(analyses)
        if source_count >= 5:
            factors["source_count"] = 1.0
        elif source_count >= 3:
            factors["source_count"] = 0.8
        elif source_count >= 2:
            factors["source_count"] = 0.6
        else:
            factors["source_count"] = 0.4
        
        # 3. Consistency factor (agreement in categories and sentiment)
        categories = [analysis.category for analysis in analyses]
        sentiments = [analysis.sentiment for analysis in analyses]
        
        # Calculate category consistency
        category_counts = Counter(categories)
        top_category, top_category_count = category_counts.most_common(1)[0] if category_counts else ("", 0)
        category_consistency = top_category_count / len(categories) if categories else 0.0
        
        # Calculate sentiment consistency
        sentiment_counts = Counter(sentiments)
        top_sentiment, top_sentiment_count = sentiment_counts.most_common(1)[0] if sentiment_counts else ("", 0)
        sentiment_consistency = top_sentiment_count / len(sentiments) if sentiments else 0.0
        
        # Combined consistency score
        factors["consistency"] = (category_consistency + sentiment_consistency) / 2
        
        # 4. Reliability factor
        reliable_count = sum(1 for analysis in analyses if analysis.is_reliable)
        factors["reliability"] = reliable_count / len(analyses) if analyses else 0.0
        
        # Calculate weighted confidence score
        weights = {
            "source_quality": 0.3,
            "source_count": 0.2,
            "consistency": 0.2,
            "reliability": 0.3
        }
        
        confidence_score = sum(
            factors[factor] * weights[factor]
            for factor in factors
        )
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, confidence_score))
    
    def _calculate_point_relevance(self, point: str, query: Optional[str]) -> float:
        """
        Calculate relevance of a point to the query.
        
        Args:
            point: The text point to evaluate
            query: The query string (can be None)
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        if not query:
            return 1.0  # No query means all points are equally relevant
        
        # Convert to lowercase for matching
        point_lower = point.lower()
        query_lower = query.lower()
        
        # Extract query terms (skip common words)
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about"}
        query_terms = [term for term in query_lower.split() if term not in common_words and len(term) > 2]
        
        # If no significant query terms, all points are relevant
        if not query_terms:
            return 1.0
        
        # Count matching terms
        matching_terms = sum(1 for term in query_terms if term in point_lower)
        match_ratio = matching_terms / len(query_terms) if query_terms else 0.0
        
        # Check for exact phrase match (gives high relevance)
        if query_lower in point_lower:
            return 1.0
        
        # Calculate relevance based on matching ratio
        if match_ratio > 0.7:
            return 0.9
        elif match_ratio > 0.5:
            return 0.7
        elif match_ratio > 0.3:
            return 0.5
        elif match_ratio > 0.0:
            return 0.3
        else:
            return 0.1
    
    async def _handle_synthesis_error(self, error: Exception, context: ErrorContext) -> SynthesisResult:
        """
        Handle synthesis errors and create fallback response.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            A basic SynthesisResult with error information
        """
        logger.error(f"Handling synthesis error: {str(error)}")
        
        # Create basic error synthesis
        error_content = f"Error synthesizing knowledge: {str(error)}"
        
        if "partial_results" in context.metadata and "analyses" in context.metadata["partial_results"]:
            analyses = context.metadata["partial_results"]["analyses"]
            if analyses and isinstance(analyses, list):
                # Try to extract some basic information from analyses
                sources = [analysis.source_url for analysis in analyses if hasattr(analysis, "source_url")]
                entity_map = {}
                
                return SynthesisResult(
                    content=error_content,
                    sources=sources,
                    key_insights=[],
                    source_quality={},
                    entity_map=entity_map,
                    synthesis_time_ms=0,
                    confidence_score=0.0,
                    processing_metadata={
                        "error": str(error),
                        "error_type": type(error).__name__,
                        "timestamp": time.time()
                    }
                )
        
        # Fallback for complete failure
        return SynthesisResult(
            content=error_content,
            sources=[],
            key_insights=[],
            source_quality={},
            entity_map={},
            synthesis_time_ms=0,
            confidence_score=0.0,
            processing_metadata={
                "error": str(error),
                "error_type": type(error).__name__,
                "timestamp": time.time()
            }
        )
