"""
Content analyzer for analyzing and extracting insights from content.
"""
import logging
import time
import re
import asyncio
from typing import Dict, List, Set, Any, Optional, AsyncIterator, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse

from ..utils.config import Config, AnalyzerConfig
from ..utils.error_handler import ErrorHandler, ErrorContext

logger = logging.getLogger(__name__)

class ContentAnalysisError(Exception):
    """Exception raised for content analysis errors."""
    pass

@dataclass
class AnalysisResult:
    """Result of content analysis."""
    source_url: str
    quality_score: float
    relevance_score: float
    key_points: List[str]
    entities: List[str]
    sentiment: str
    category: str
    tags: List[str]
    summary: str
    processing_time_ms: float
    content_type: str
    word_count: int
    is_reliable: bool
    processing_metadata: Dict[str, Any] = field(default_factory=dict)

class ContentAnalyzer:
    """
    Analyzes content to extract insights, categorize, and score quality and relevance.
    Supports streaming for real-time analysis of content as it's fetched.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the content analyzer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.analyzer_config = config.analyzer
        self.error_handler = ErrorHandler()
        
        # Known categories for classification
        self.categories = {
            "technical": ["code", "programming", "technology", "software", "hardware", "data", "api"],
            "educational": ["tutorial", "guide", "learn", "education", "course", "training"],
            "news": ["news", "report", "latest", "update", "today", "current events"],
            "academic": ["research", "study", "paper", "journal", "findings", "experiment"],
            "opinion": ["opinion", "editorial", "viewpoint", "perspective", "commentary"],
            "product": ["product", "review", "comparison", "specification", "features"]
        }
        
        # Entity patterns for basic entity extraction
        self.entity_patterns = {
            "organization": r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b(?:\s+(?:Inc|Corp|Ltd|LLC|Company|Organization))?",
            "person": r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b",
            "location": r"\b([A-Z][a-z]+(?:,\s+[A-Z][a-z]+)?)\b",
            "date": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:[,|\s]\s*\d{2,4})?)\b",
            "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
            "url": r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!$&'()*+,;=:~.]+)*(?:\?[-\w%.!$&'()*+,;=:/?~]+)?(?:#[-\w%.!$&'()*+,;=:/?~]+)?",
            "version": r"\b\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?\b",
            "technology": r"\b(?:Python|JavaScript|Java|C\+\+|Ruby|PHP|Go|Rust|TypeScript|SQL|HTML|CSS|AWS|Azure|GCP|React|Angular|Vue|Node\.js|Django|Flask|Spring|TensorFlow|PyTorch)\b"
        }
        
        # Sentiment words for basic sentiment analysis
        self.sentiment_words = {
            "positive": ["excellent", "great", "good", "best", "outstanding", "impressive", "amazing", "wonderful", 
                        "fantastic", "superb", "brilliant", "perfect", "recommend", "superior", "exceptional",
                        "helpful", "impressive", "effective", "useful", "valuable"],
            "negative": ["poor", "bad", "worst", "terrible", "awful", "disappointing", "mediocre", "inadequate",
                        "ineffective", "useless", "flawed", "defective", "inferior", "fails", "frustrating",
                        "confusing", "difficult", "buggy", "slow", "expensive"],
            "neutral": ["average", "moderate", "normal", "standard", "typical", "common", "routine", "regular",
                        "conventional", "usual", "ordinary"]
        }
    
    async def analyze(self, content: Dict[str, Any], query: Optional[str] = None) -> AnalysisResult:
        """
        Analyze content to extract insights, categorize, and score.
        
        Args:
            content: Content data including text content and metadata
            query: Optional query for relevance scoring
            
        Returns:
            AnalysisResult with analysis results
        """
        try:
            # Start timing
            start_time = time.time()
            
            # Extract fields
            url = content.get("url", "")
            text_content = content.get("content", "")
            content_type = content.get("content_type", "unknown")
            
            # Skip empty content
            if not text_content:
                raise ContentAnalysisError("Empty content")
            
            # Analyze content
            key_points = await self._extract_key_points(text_content, query)
            entities = await self._extract_entities(text_content)
            sentiment = await self._analyze_sentiment(text_content)
            category = await self._categorize_content(text_content)
            tags = await self._generate_tags(text_content, category)
            summary = await self._generate_summary(text_content, key_points)
            quality_score = await self._calculate_quality_score(text_content, url)
            relevance_score = await self._calculate_relevance_score(text_content, query)
            is_reliable = await self._check_reliability(url, text_content)
            word_count = len(text_content.split())
            
            # Calculate processing time
            processing_time_ms = round((time.time() - start_time) * 1000)
            
            # Create result
            result = AnalysisResult(
                source_url=url,
                quality_score=quality_score,
                relevance_score=relevance_score,
                key_points=key_points,
                entities=entities,
                sentiment=sentiment,
                category=category,
                tags=tags,
                summary=summary,
                processing_time_ms=processing_time_ms,
                content_type=content_type,
                word_count=word_count,
                is_reliable=is_reliable,
                processing_metadata={
                    "timestamp": time.time(),
                    "analyzer_version": "0.1.0",
                    "analyzer_config": self.analyzer_config.__dict__
                }
            )
            
            return result
        
        except Exception as e:
            # Handle error with context
            error_context = ErrorContext(
                operation="analyze_content",
                partial_results={
                    "url": content.get("url", ""),
                    "content_type": content.get("content_type", "unknown")
                },
                metadata={
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )
            logger.error(f"Error analyzing content from {content.get('url', '')}: {str(e)}")
            
            # Raise as ContentAnalysisError
            raise ContentAnalysisError(f"Analysis failed: {str(e)}")
    
    async def analyze_multiple(self, contents: List[Dict[str, Any]], query: Optional[str] = None) -> List[AnalysisResult]:
        """
        Analyze multiple content items concurrently.
        
        Args:
            contents: List of content items to analyze
            query: Optional query for relevance scoring
            
        Returns:
            List of AnalysisResult objects
        """
        # Create tasks for each content item
        tasks = [self.analyze(content, query) for content in contents]
        
        # Run tasks concurrently with controlled concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, converting exceptions to None (filtered out later)
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error analyzing content: {str(result)}")
                # Skip failed analyses
                continue
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def analyze_stream(self, content_stream: AsyncIterator[Dict[str, Any]], query: Optional[str] = None) -> AsyncIterator[AnalysisResult]:
        """
        Analyze a stream of content items and yield results as they complete.
        
        Args:
            content_stream: Async iterator that yields content items
            query: Optional query for relevance scoring
            
        Yields:
            AnalysisResult objects as they become available
        """
        pending_tasks = {}  # Mapping of tasks to their source URLs
        
        # Process content stream
        async for content in content_stream:
            # Create task for this content
            url = content.get("url", "")
            task = asyncio.create_task(self.analyze(content, query))
            pending_tasks[task] = url
        
            # Check for completed tasks
            done, pending = await asyncio.wait(
                pending_tasks.keys(),
                return_when=asyncio.FIRST_COMPLETED,
                timeout=0.1  # Small timeout to avoid blocking
            )
            
            # Process completed tasks
            for task in done:
                url = pending_tasks.pop(task)
                try:
                    result = task.result()
                    yield result
                except Exception as e:
                    logger.error(f"Error analyzing content from {url}: {str(e)}")
                    # Skip failed analyses
        
        # Process remaining tasks
        while pending_tasks:
            done, pending = await asyncio.wait(
                pending_tasks.keys(),
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Process completed tasks
            for task in done:
                url = pending_tasks.pop(task)
                try:
                    result = task.result()
                    yield result
                except Exception as e:
                    logger.error(f"Error analyzing content from {url}: {str(e)}")
                    # Skip failed analyses
    
    async def _extract_key_points(self, content: str, query: Optional[str] = None) -> List[str]:
        """
        Extract key points from content.
        
        Args:
            content: Text content to analyze
            query: Optional query to guide extraction
            
        Returns:
            List of key points
        """
        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Skip if too little content
        if not paragraphs:
            return []
        
        # Extract sentences that are likely to be key points
        key_points = []
        
        # Process each paragraph
        for paragraph in paragraphs:
            # Skip very short paragraphs
            if len(paragraph) < 50:
                continue
            
            # Split into sentences (simple split by period)
            sentences = [s.strip() + '.' for s in paragraph.split('.') if s.strip()]
            
            # Basic criteria for key sentences:
            # 1. Not too short or too long
            # 2. Contains important indicators (key phrase, numbers, etc.)
            # 3. Contains query terms (if provided)
            for sentence in sentences:
                # Skip too short or too long sentences
                if len(sentence) < 30 or len(sentence) > 200:
                    continue
                
                # Check for key indicators
                has_key_indicator = any(
                    indicator in sentence.lower() 
                    for indicator in [
                        "important", "significant", "key", "main", "critical", 
                        "essential", "crucial", "primary", "major", "fundamental"
                    ]
                )
                
                # Check for statistics/numbers
                has_numbers = bool(re.search(r'\d+(?:\.\d+)?(?:\s*%)?', sentence))
                
                # Check for query terms (if provided)
                has_query_terms = True
                if query:
                    query_terms = [t.lower() for t in query.split() if len(t) > 3]
                    has_query_terms = any(term in sentence.lower() for term in query_terms)
                
                # Add if it meets criteria
                if (has_key_indicator or has_numbers) and has_query_terms:
                    # Clean up the sentence (remove extra spaces, newlines)
                    clean_sentence = ' '.join(sentence.split())
                    if clean_sentence and clean_sentence not in key_points:
                        key_points.append(clean_sentence)
        
        # If not enough key points found using strict criteria, use less strict criteria
        if len(key_points) < 3:
            # Find sentences with query terms (if provided)
            if query:
                query_terms = [t.lower() for t in query.split() if len(t) > 3]
                for paragraph in paragraphs:
                    sentences = [s.strip() + '.' for s in paragraph.split('.') if s.strip()]
                    for sentence in sentences:
                        if len(sentence) < 30 or len(sentence) > 200:
                            continue
                        if any(term in sentence.lower() for term in query_terms):
                            clean_sentence = ' '.join(sentence.split())
                            if clean_sentence and clean_sentence not in key_points:
                                key_points.append(clean_sentence)
            
            # If still not enough, take sentences from beginning of paragraphs
            if len(key_points) < 3:
                for paragraph in paragraphs[:5]:  # Only from first 5 paragraphs
                    sentences = [s.strip() + '.' for s in paragraph.split('.') if s.strip()]
                    if sentences:
                        clean_sentence = ' '.join(sentences[0].split())  # First sentence
                        if clean_sentence and clean_sentence not in key_points:
                            key_points.append(clean_sentence)
        
        # Limit number of key points
        return key_points[:5]  # Maximum 5 key points
    
    async def _extract_entities(self, content: str) -> List[str]:
        """
        Extract entities from content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of extracted entities
        """
        entities = set()
        
        # Apply entity patterns
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Take first group if multiple capturing groups
                if match and len(match) > 3:  # Skip very short matches
                    entities.add(match)
        
        # Convert to list and sort
        return sorted(list(entities))
    
    async def _analyze_sentiment(self, content: str) -> str:
        """
        Analyze sentiment of content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Sentiment classification ("positive", "negative", "neutral", or "mixed")
        """
        # Convert to lowercase for matching
        content_lower = content.lower()
        
        # Count sentiment words
        sentiment_counts = {
            "positive": 0,
            "negative": 0,
            "neutral": 0
        }
        
        # Count occurrences of sentiment words
        for sentiment, words in self.sentiment_words.items():
            for word in words:
                # Count word occurrences (simple word matching)
                sentiment_counts[sentiment] += content_lower.count(f" {word} ")
        
        # Determine overall sentiment
        total_count = sum(sentiment_counts.values())
        if total_count == 0:
            return "neutral"  # No sentiment words found
        
        # Calculate percentages
        sentiment_percentages = {
            sentiment: count / total_count
            for sentiment, count in sentiment_counts.items()
        }
        
        # Determine dominant sentiment
        dominant_sentiment = max(sentiment_percentages, key=sentiment_percentages.get)
        dominant_percentage = sentiment_percentages[dominant_sentiment]
        
        # If dominant sentiment is not clear, classify as mixed
        if dominant_percentage < 0.5:
            return "mixed"
        
        return dominant_sentiment
    
    async def _categorize_content(self, content: str) -> str:
        """
        Categorize content based on its content.
        
        Args:
            content: Text content to categorize
            
        Returns:
            Category label
        """
        # Convert to lowercase for matching
        content_lower = content.lower()
        
        # Count category keywords
        category_scores = {}
        for category, keywords in self.categories.items():
            score = 0
            for keyword in keywords:
                # Count keyword occurrences
                score += content_lower.count(f" {keyword} ")
            category_scores[category] = score
        
        # Get category with highest score
        if any(category_scores.values()):
            return max(category_scores, key=category_scores.get)
        
        # Default if no categories match
        return "general"
    
    async def _generate_tags(self, content: str, category: str) -> List[str]:
        """
        Generate tags for content.
        
        Args:
            content: Text content to analyze
            category: Content category
            
        Returns:
            List of tags
        """
        tags = set()
        
        # Add category as a tag
        tags.add(category)
        
        # Add keywords from content
        content_lower = content.lower()
        
        # Check for common keywords based on category
        if category in self.categories:
            # Add keywords that appear in the content
            for keyword in self.categories[category]:
                if f" {keyword} " in content_lower:
                    tags.add(keyword)
        
        # Add entities as tags (using simpler entity extraction for speed)
        for entity_type in ["technology", "organization"]:
            if entity_type in self.entity_patterns:
                pattern = self.entity_patterns[entity_type]
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]  # Take first group if multiple capturing groups
                    if match and len(match) > 3:  # Skip very short matches
                        tags.add(match.lower())
        
        # Limit number of tags
        return sorted(list(tags))[:10]  # Maximum 10 tags
    
    async def _generate_summary(self, content: str, key_points: List[str]) -> str:
        """
        Generate a summary of the content.
        
        Args:
            content: Text content to summarize
            key_points: Already extracted key points
            
        Returns:
            Summary text
        """
        # If we have key points, use them to create a summary
        if key_points:
            return " ".join(key_points)
        
        # Otherwise, extract from beginning of content
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Get first few paragraphs
        if paragraphs:
            # Take first paragraph if it's substantial
            if len(paragraphs[0]) > 100:
                return paragraphs[0]
            
            # Otherwise, combine first few paragraphs
            summary = " ".join(paragraphs[:2])
            if len(summary) > 500:
                # Truncate if too long
                return summary[:497] + "..."
            return summary
        
        # Fallback for very short content
        if len(content) > 500:
            return content[:497] + "..."
        return content
    
    async def _calculate_quality_score(self, content: str, url: str) -> float:
        """
        Calculate a quality score for the content.
        
        Args:
            content: Text content to analyze
            url: Source URL
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        # Basic quality metrics
        quality_metrics = {
            "length": 0.0,  # Length score
            "structure": 0.0,  # Structure score
            "language": 0.0,  # Language quality score
            "source": 0.0  # Source credibility score
        }
        
        # 1. Length score - longer content tends to be more informative
        word_count = len(content.split())
        if word_count > 1000:
            quality_metrics["length"] = 1.0
        elif word_count > 500:
            quality_metrics["length"] = 0.8
        elif word_count > 200:
            quality_metrics["length"] = 0.6
        elif word_count > 100:
            quality_metrics["length"] = 0.4
        else:
            quality_metrics["length"] = 0.2
        
        # 2. Structure score - well-structured content has paragraphs, headings, etc.
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) > 5:
            quality_metrics["structure"] = 1.0
        elif len(paragraphs) > 3:
            quality_metrics["structure"] = 0.8
        elif len(paragraphs) > 1:
            quality_metrics["structure"] = 0.6
        else:
            quality_metrics["structure"] = 0.4
        
        # 3. Language quality score - based on sentence structure, vocabulary
        sentences = []
        for paragraph in paragraphs:
            sentences.extend([s.strip() + '.' for s in paragraph.split('.') if s.strip()])
        
        # Calculate average sentence length
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        
        # Penalize very short or very long sentences
        if 10 <= avg_sentence_length <= 25:
            quality_metrics["language"] = 1.0
        elif 8 <= avg_sentence_length <= 30:
            quality_metrics["language"] = 0.8
        elif 5 <= avg_sentence_length <= 40:
            quality_metrics["language"] = 0.6
        else:
            quality_metrics["language"] = 0.4
        
        # 4. Source credibility score - based on domain
        domain = urlparse(url).netloc
        
        # High-quality domains (educational, government, well-known publications)
        high_quality_domains = [".edu", ".gov", "wikipedia.org", "github.com", "stackoverflow.com", 
                              "medium.com", "nytimes.com", "washingtonpost.com", "bbc.com", 
                              "reuters.com", "bloomberg.com", "nature.com", "science.org"]
        
        # Medium-quality domains (established companies, popular blogs)
        medium_quality_domains = [".org", "blog.", "docs.", "developer.", "support."]
        
        # Check domain quality
        if any(hqd in domain for hqd in high_quality_domains):
            quality_metrics["source"] = 1.0
        elif any(mqd in domain for mqd in medium_quality_domains):
            quality_metrics["source"] = 0.8
        else:
            quality_metrics["source"] = 0.6
        
        # Calculate overall quality score (weighted average)
        weights = {
            "length": 0.2,
            "structure": 0.3,
            "language": 0.3,
            "source": 0.2
        }
        
        quality_score = sum(
            quality_metrics[metric] * weights[metric]
            for metric in quality_metrics
        )
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, quality_score))
    
    async def _calculate_relevance_score(self, content: str, query: Optional[str]) -> float:
        """
        Calculate relevance score of content to the query.
        
        Args:
            content: Text content to analyze
            query: Query to check relevance against (can be None)
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        # If no query, assume maximum relevance
        if not query:
            return 1.0
        
        # Convert to lowercase for matching
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Extract query terms (skip common words)
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about"}
        query_terms = [term for term in query_lower.split() if term not in common_words and len(term) > 2]
        
        # If no significant query terms, assume maximum relevance
        if not query_terms:
            return 1.0
        
        # Calculate term frequency in content
        term_counts = {}
        for term in query_terms:
            term_counts[term] = content_lower.count(term)
        
        # Calculate relevance score based on term frequencies
        relevance_metrics = {
            "occurrence": 0.0,  # Basic term occurrence
            "density": 0.0,  # Term density
            "exact_match": 0.0  # Exact phrase match
        }
        
        # 1. Term occurrence - how many query terms appear in the content
        terms_present = sum(1 for term, count in term_counts.items() if count > 0)
        if terms_present == len(query_terms):
            relevance_metrics["occurrence"] = 1.0
        elif terms_present > 0:
            relevance_metrics["occurrence"] = terms_present / len(query_terms)
        
        # 2. Term density - how frequently query terms appear relative to content length
        content_word_count = len(content_lower.split())
        if content_word_count > 0:
            total_term_occurrences = sum(term_counts.values())
            term_density = total_term_occurrences / content_word_count
            # Scale density (empirical values)
            if term_density > 0.05:
                relevance_metrics["density"] = 1.0
            elif term_density > 0.02:
                relevance_metrics["density"] = 0.8
            elif term_density > 0.01:
                relevance_metrics["density"] = 0.6
            elif term_density > 0.005:
                relevance_metrics["density"] = 0.4
            elif term_density > 0:
                relevance_metrics["density"] = 0.2
        
        # 3. Exact phrase match - check if the exact query appears in content
        if query_lower in content_lower:
            relevance_metrics["exact_match"] = 1.0
        elif len(query_terms) > 1:
            # Check for partial phrase matches
            query_bigrams = set()
            for i in range(len(query_terms) - 1):
                query_bigrams.add(f"{query_terms[i]} {query_terms[i+1]}")
            
            # Count matching bigrams
            matching_bigrams = sum(1 for bigram in query_bigrams if bigram in content_lower)
            if matching_bigrams > 0:
                relevance_metrics["exact_match"] = matching_bigrams / len(query_bigrams)
        
        # Calculate overall relevance score (weighted average)
        weights = {
            "occurrence": 0.3,
            "density": 0.4,
            "exact_match": 0.3
        }
        
        relevance_score = sum(
            relevance_metrics[metric] * weights[metric]
            for metric in relevance_metrics
        )
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, relevance_score))
    
    async def _check_reliability(self, url: str, content: str) -> bool:
        """
        Check if content is from a reliable source.
        
        Args:
            url: Source URL
            content: Text content to check
            
        Returns:
            True if considered reliable, False otherwise
        """
        # Domain-based reliability check
        domain = urlparse(url).netloc
        
        # Known reliable domains
        reliable_domains = [".edu", ".gov", "wikipedia.org", "github.com", "stackoverflow.com", 
                          "medium.com", "nytimes.com", "washingtonpost.com", "bbc.com", 
                          "reuters.com", "bloomberg.com", "nature.com", "science.org"]
        
        # Check domain reliability
        domain_reliable = any(rd in domain for rd in reliable_domains)
        
        # Content-based reliability indicators
        content_indicators = {
            "citations": False,  # Has citations/references
            "balanced": False,  # Presents balanced viewpoints
            "structured": False  # Well-structured content
        }
        
        # Check for citations/references
        citation_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\(\d{4}\)',  # (2020), (2021), etc.
            r'(?:according to|cited by|source|reference)',  # Citation phrases
            r'(?:https?://|www\.)',  # URLs
        ]
        
        for pattern in citation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                content_indicators["citations"] = True
                break
        
        # Check for balanced viewpoints
        balanced_phrases = [
            r'on the other hand',
            r'however',
            r'nevertheless',
            r'alternatively',
            r'in contrast',
            r'conversely',
            r'while',
            r'although',
            r'despite',
            r'pros and cons',
            r'advantages and disadvantages'
        ]
        
        for phrase in balanced_phrases:
            if re.search(phrase, content, re.IGNORECASE):
                content_indicators["balanced"] = True
                break
        
        # Check for well-structured content
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        content_indicators["structured"] = len(paragraphs) >= 3
        
        # Determine overall reliability
        # Domain reliability has high weight
        if domain_reliable:
            # Already high reliability, content factors can't make it fail
            return True
        
        # If not a reliable domain, need strong content indicators
        # At least 2 out of 3 indicators should be positive
        content_reliability_score = sum(1 for indicator in content_indicators.values() if indicator)
        return content_reliability_score >= 2