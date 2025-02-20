"""Quality scoring component for content enhancement."""
import time
import asyncio
from dataclasses import dataclass
from typing import Dict, Any, Optional, AsyncIterator, List
import logging

from ..utils.config import QualityConfig

logger = logging.getLogger(__name__)

@dataclass
class QualityScore:
    """Represents the quality assessment of content."""
    quality_score: float
    confidence_score: float
    depth_rating: str
    details: Optional[Dict[str, Any]] = None
    timestamp: float = time.time()

@dataclass
class ProcessingState:
    """Maintains state for error recovery."""
    processed_count: int = 0
    error_count: int = 0
    last_successful_timestamp: float = 0
    last_error_timestamp: float = 0
    successful_items: List[Dict[str, Any]] = None
    current_batch: List[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize lists."""
        self.successful_items = []
        self.current_batch = []

    def record_success(self, item: Dict[str, Any]):
        """Record successful processing."""
        self.processed_count += 1
        self.last_successful_timestamp = time.time()
        self.successful_items.append(item)

    def record_error(self):
        """Record processing error."""
        self.error_count += 1
        self.last_error_timestamp = time.time()

    def get_error_rate(self) -> float:
        """Calculate current error rate."""
        total = self.processed_count + self.error_count
        return self.error_count / total if total > 0 else 0

    def should_trigger_cleanup(self) -> bool:
        """Determine if cleanup should be triggered."""
        return (self.get_error_rate() > 0.01 or  # > 1% error rate
                len(self.current_batch) >= 100)   # Batch size limit

class ResourceManager:
    """Manages resources for quality scoring."""
    def __init__(self, max_memory_mb: int = 10):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024  # Convert MB to bytes
        self.current_memory_bytes = 0
        self._resources = set()
        self._cleanup_required = False
        self.peak_memory_bytes = 0
        self.last_cleanup = time.time()
        self.cleanup_interval = 1  # seconds (reduced from 5)
        self._monitoring_task = None

    async def __aenter__(self):
        """Initialize resources and start monitoring."""
        self._monitoring_task = asyncio.create_task(self._monitor_resources())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources and stop monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        await self.cleanup()

    async def cleanup(self):
        """Clean up allocated resources."""
        try:
            self.current_memory_bytes = 0
            self._resources.clear()
            self._cleanup_required = False
            self.last_cleanup = time.time()
            await asyncio.sleep(0.01)  # Reduced sleep time
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

    async def _monitor_resources(self):
        """Monitor resource usage and trigger cleanup if needed."""
        try:
            while True:
                current_time = time.time()
                if (current_time - self.last_cleanup >= self.cleanup_interval and
                    self._cleanup_required):
                    await self.cleanup()
                self.peak_memory_bytes = max(self.peak_memory_bytes, self.current_memory_bytes)
                await asyncio.sleep(0.1)  # Reduced from 1s to 100ms
        except asyncio.CancelledError:
            await self.cleanup()
            raise

    def check_memory_usage(self) -> bool:
        """Check if memory usage is within limits."""
        current = self.current_memory_bytes
        self.peak_memory_bytes = max(self.peak_memory_bytes, current)
        return current < self.max_memory_bytes

    def track_allocation(self, size: int):
        """Track memory allocation."""
        self.current_memory_bytes += size
        if self.current_memory_bytes >= self.max_memory_bytes * 0.8:  # 80% threshold
            self._cleanup_required = True

    @property
    def current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.current_memory_bytes / (1024 * 1024)

    @property
    def peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        return self.peak_memory_bytes / (1024 * 1024)

class QualityScorer:
    """Evaluates content quality using streaming-first approach."""
    
    def __init__(self, config: QualityConfig):
        """Initialize QualityScorer with configuration."""
        self.config = config
        self.resource_manager = ResourceManager(max_memory_mb=config.max_memory_mb)
        self.source_weights = config.source_weights
        self.quality_metrics = config.quality_metrics
        self.processing_state = ProcessingState()
        self.start_time = time.time()
        self.throughput_counter = 0
        self.last_throughput_check = time.time()

    async def evaluate_stream(self, content_stream: AsyncIterator[Dict[str, Any]]) -> AsyncIterator[QualityScore]:
        """
        Evaluates content quality using streaming approach.
        
        Args:
            content_stream: AsyncIterator yielding content items
            
        Yields:
            QualityScore objects containing quality metrics
        """
        try:
            async with self.resource_manager:
                async for content in content_stream:
                    processing_start = time.time()
                    
                    # Update throughput metrics
                    current_time = time.time()
                    if current_time - self.last_throughput_check >= 1.0:
                        logger.info(f"Current throughput: {self.throughput_counter} items/second")
                        self.throughput_counter = 0
                        self.last_throughput_check = current_time

                    if not self._validate_content(content):
                        self.processing_state.record_error()
                        if self.processing_state.get_error_rate() > 0.01:
                            logger.warning("Error rate exceeded threshold")
                        continue

                    try:
                        # Add to current batch
                        self.processing_state.current_batch.append(content)
                        
                        # Process content
                        quality_score = await self._calculate_quality_score(content)
                        confidence_score = await self._calculate_confidence_score(content)
                        depth_rating = await self._assess_depth(content)

                        # Track memory allocation
                        estimated_size = len(str(content)) * 2  # Rough estimation
                        self.resource_manager.track_allocation(estimated_size)

                        result = QualityScore(
                            quality_score=quality_score,
                            confidence_score=confidence_score,
                            depth_rating=depth_rating,
                            details=self._generate_details(content),
                            timestamp=time.time()
                        )

                        # Update state
                        self.processing_state.record_success(content)
                        self.throughput_counter += 1

                        # Check processing time
                        processing_time = time.time() - processing_start
                        if processing_time > 0.1:  # > 100ms
                            logger.warning(f"Slow processing detected: {processing_time*1000:.2f}ms")

                        yield result

                        # Check if cleanup needed
                        if self.processing_state.should_trigger_cleanup():
                            await self.resource_manager.cleanup()
                            self.processing_state.current_batch.clear()

                    except Exception as e:
                        logger.error(f"Error processing content: {str(e)}")
                        self.processing_state.record_error()
                        if self.processing_state.get_error_rate() > 0.01:
                            logger.warning("Error rate exceeded threshold")
                        continue

        except Exception as e:
            logger.error(f"Stream processing error: {str(e)}")
            # Attempt state recovery
            if self.processing_state.successful_items:
                logger.info("Attempting state recovery")
                for item in self.processing_state.successful_items:
                    try:
                        result = await self.evaluate(item)
                        yield result
                    except Exception as recovery_error:
                        logger.error(f"Recovery failed: {str(recovery_error)}")
            raise
        finally:
            # Log final metrics
            total_time = time.time() - self.start_time
            total_processed = self.processing_state.processed_count
            logger.info(f"Total processing time: {total_time:.2f}s")
            logger.info(f"Items processed: {total_processed}")
            logger.info(f"Average throughput: {total_processed/total_time:.2f} items/second")
            logger.info(f"Peak memory usage: {self.resource_manager.peak_memory/1024/1024:.2f}MB")
            logger.info(f"Error rate: {self.processing_state.get_error_rate()*100:.2f}%")

    async def evaluate(self, content: Dict[str, Any]) -> QualityScore:
        """
        Evaluates single content item quality with enhanced error handling.
        
        Args:
            content: Dictionary containing content details
            
        Returns:
            QualityScore object containing quality metrics
        """
        try:
            if not self._validate_content(content):
                logger.warning("Invalid content format, using default scores")
                return QualityScore(
                    quality_score=0.5,
                    confidence_score=0.5,
                    depth_rating="shallow",
                    details={"error": "Invalid content format"}
                )

            async with self.resource_manager:
                try:
                    quality_score = await self._calculate_quality_score(content)
                except Exception as e:
                    logger.warning(f"Error calculating quality score: {str(e)}")
                    quality_score = 0.5

                try:
                    confidence_score = await self._calculate_confidence_score(content)
                except Exception as e:
                    logger.warning(f"Error calculating confidence score: {str(e)}")
                    confidence_score = 0.5

                try:
                    depth_rating = await self._assess_depth(content)
                except Exception as e:
                    logger.warning(f"Error assessing depth: {str(e)}")
                    depth_rating = "shallow"

                try:
                    details = self._generate_details(content)
                except Exception as e:
                    logger.warning(f"Error generating details: {str(e)}")
                    details = {"error": "Failed to generate details"}

                return QualityScore(
                    quality_score=float(quality_score),
                    confidence_score=float(confidence_score),
                    depth_rating=str(depth_rating),
                    details=details
                )

        except Exception as e:
            logger.error(f"Critical error evaluating content: {str(e)}")
            # Return safe default scores instead of raising
            return QualityScore(
                quality_score=0.5,
                confidence_score=0.5,
                depth_rating="shallow",
                details={"error": f"Evaluation failed: {str(e)}"}
            )

    def _validate_content(self, content: Dict[str, Any]) -> bool:
        """Validates content has required fields."""
        if not content or not isinstance(content, dict):
            return False
            
        required_fields = {"text", "sources", "depth"}
        return all(field in content for field in required_fields)

    async def _calculate_quality_score(self, content: Dict[str, Any]) -> float:
        """Calculates overall quality score with enhanced error handling."""
        try:
            weights = {
                "technical_accuracy": 0.4,
                "source_quality": 0.3,
                "depth_score": 0.2,
                "citation_score": 0.1
            }

            scores = {}

            # Handle technical accuracy with type validation
            try:
                tech_acc = content.get("technical_accuracy", 0)
                if isinstance(tech_acc, (int, float)):
                    scores["technical_accuracy"] = float(tech_acc)
                else:
                    scores["technical_accuracy"] = 0.5
            except (ValueError, TypeError):
                scores["technical_accuracy"] = 0.5

            # Handle source quality with error handling
            try:
                sources = content.get("sources", [])
                if isinstance(sources, (list, tuple)):
                    scores["source_quality"] = self._calculate_source_quality(sources)
                else:
                    scores["source_quality"] = 0.5
            except Exception:
                scores["source_quality"] = 0.5

            # Handle depth score with type validation
            try:
                depth = str(content.get("depth", "shallow"))
                scores["depth_score"] = self._calculate_depth_score(depth)
            except Exception:
                scores["depth_score"] = 0.5

            # Handle citation score with error handling
            try:
                citations = content.get("citations", 0)
                scores["citation_score"] = self._calculate_citation_score(citations)
            except Exception:
                scores["citation_score"] = 0.5

            # Calculate weighted sum with validation
            total_score = 0.0
            for metric, score in scores.items():
                try:
                    total_score += float(score) * weights[metric]
                except (ValueError, TypeError):
                    total_score += 0.5 * weights[metric]

            return min(max(total_score, 0.0), 1.0)  # Ensure score is between 0 and 1

        except Exception as e:
            logger.error(f"Critical error in quality score calculation: {str(e)}")
            return 0.5  # Return middle-ground score on critical error

    async def _calculate_confidence_score(self, content: Dict[str, Any]) -> float:
        """Calculates confidence in quality assessment with enhanced error handling."""
        try:
            factors = {}

            # Handle source reliability
            try:
                sources = content.get("sources", [])
                factors["source_reliability"] = self._assess_source_reliability(sources)
            except Exception as e:
                logger.warning(f"Error calculating source reliability: {str(e)}")
                factors["source_reliability"] = 0.5

            # Handle content completeness
            try:
                factors["content_completeness"] = self._assess_completeness(content)
            except Exception as e:
                logger.warning(f"Error calculating completeness: {str(e)}")
                factors["content_completeness"] = 0.5

            # Handle verification level
            try:
                factors["verification_level"] = self._assess_verification_level(content)
            except Exception as e:
                logger.warning(f"Error calculating verification level: {str(e)}")
                factors["verification_level"] = 0.5

            # Calculate average with validation
            total = 0.0
            count = len(factors)
            for value in factors.values():
                try:
                    total += float(value)
                except (ValueError, TypeError):
                    total += 0.5
                    
            return total / count if count > 0 else 0.5

        except Exception as e:
            logger.error(f"Critical error in confidence calculation: {str(e)}")
            return 0.5

    async def _assess_depth(self, content: Dict[str, Any]) -> str:
        """Assesses content depth level."""
        depth_mapping = {
            "comprehensive": 1.0,
            "intermediate": 0.7,
            "shallow": 0.4
        }
        return content["depth"] if content["depth"] in depth_mapping else "shallow"

    def _calculate_source_quality(self, sources: list) -> float:
        """Calculates source quality score."""
        if not sources:
            return 0.0
            
        return sum(self.source_weights.get(source, 0.1) for source in sources) / len(sources)

    def _calculate_depth_score(self, depth: str) -> float:
        """Calculates depth score."""
        depth_scores = {
            "comprehensive": 1.0,
            "intermediate": 0.7,
            "shallow": 0.4
        }
        return depth_scores.get(depth, 0.1)

    def _calculate_citation_score(self, citations: Any) -> float:
        """Calculates citation score."""
        try:
            if isinstance(citations, (list, tuple, set)):
                citation_count = len(citations)
            else:
                citation_count = int(citations)

            if citation_count >= 10:
                return 1.0
            elif citation_count >= 5:
                return 0.7
            elif citation_count > 0:
                return 0.4
            return 0.1
        except (ValueError, TypeError):
            return 0.1

    def _assess_source_reliability(self, sources: list) -> float:
        """Assesses source reliability."""
        reliable_sources = {"research_paper", "academic_journal", "expert_review"}
        if not sources:
            return 0.0
        return len([s for s in sources if s in reliable_sources]) / len(sources)

    def _assess_completeness(self, content: Dict[str, Any]) -> float:
        """Assesses content completeness."""
        optional_fields = {"citations", "technical_accuracy"}
        present_fields = sum(1 for field in optional_fields if field in content)
        return 0.7 + (0.3 * (present_fields / len(optional_fields)))

    def _assess_verification_level(self, content: Dict[str, Any]) -> float:
        """Assesses content verification level."""
        has_citations = "citations" in content and content["citations"] > 0
        has_accuracy = "technical_accuracy" in content
        reliable_sources = any(s in {"research_paper", "academic_journal"} for s in content["sources"])
        
        factors = [has_citations, has_accuracy, reliable_sources]
        return sum(1 for f in factors if f) / len(factors)

    def _calculate_freshness_score(self, sources: list) -> float:
        """Calculates freshness score based on source types."""
        high_freshness_sources = {"research_paper", "academic_journal"}
        if any(source in high_freshness_sources for source in sources):
            return 1.0
        medium_freshness_sources = {"expert_review", "educational_site"}
        if any(source in medium_freshness_sources for source in sources):
            return 0.8
        return 0.7

    def _generate_details(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generates detailed quality assessment information."""
        sources = content["sources"]
        reliable_sources = {"research_paper", "academic_journal", "expert_review"}
        authority_sources = {"research_paper", "academic_journal"}
        
        return {
            "source_count": len(sources),
            "reliable_sources": len([s for s in sources if s in reliable_sources]),
            "authority_sources": len([s for s in sources if s in authority_sources]),
            "has_citations": "citations" in content,
            "depth_level": content["depth"],
            "technical_accuracy": content.get("technical_accuracy", None),
            "timestamp": None
        }