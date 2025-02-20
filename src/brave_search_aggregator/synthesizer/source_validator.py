"""Source validation component for content enhancement."""
import time
import asyncio
from dataclasses import dataclass
from typing import Dict, Any, Optional, AsyncIterator, List
import logging

from ..utils.config import SourceValidationConfig

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Represents the validation assessment of a source."""
    trust_score: float
    reliability_score: float
    authority_score: float
    freshness_score: float
    is_valid: bool
    details: Optional[Dict[str, Any]] = None
    timestamp: float = time.time()

@dataclass
class ValidationState:
    """Maintains state for validation processing and error recovery."""
    processed_count: int = 0
    error_count: int = 0
    last_successful_timestamp: float = 0
    last_error_timestamp: float = 0
    successful_items: List[Dict[str, Any]] = None
    current_batch: List[Dict[str, Any]] = None
    batch_size: int = 3

    def __post_init__(self):
        """Initialize lists."""
        self.successful_items = []
        self.current_batch = []

    def record_success(self, item: Dict[str, Any]):
        """Record successful validation."""
        self.processed_count += 1
        self.last_successful_timestamp = time.time()
        self.successful_items.append(item)

    def record_error(self):
        """Record validation error."""
        self.error_count += 1
        self.last_error_timestamp = time.time()

    def get_error_rate(self) -> float:
        """Calculate current error rate."""
        total = self.processed_count + self.error_count
        return self.error_count / total if total > 0 else 0

    def should_trigger_cleanup(self) -> bool:
        """Determine if cleanup should be triggered."""
        return (self.get_error_rate() > 0.01 or  # > 1% error rate
                len(self.current_batch) >= self.batch_size)  # Batch size limit

class ResourceManager:
    """Manages resources for source validation."""
    def __init__(self, max_memory_mb: int = 10):
        self.max_memory = max_memory_mb * 1024 * 1024
        self.current_memory_mb = 0
        self._resources = set()
        self._cleanup_required = False
        self.peak_memory = 0
        self.last_cleanup = time.time()
        self.cleanup_interval = 5  # seconds
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
            self.current_memory_mb = 0
            self._resources.clear()
            self._cleanup_required = False
            self.last_cleanup = time.time()
            await asyncio.sleep(0)  # Allow other tasks to run
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
                self.peak_memory = max(self.peak_memory, self.current_memory_mb)
                await asyncio.sleep(1)  # Check every second
        except asyncio.CancelledError:
            await self.cleanup()
            raise

    def check_memory_usage(self) -> bool:
        """Check if memory usage is within limits."""
        current = self.current_memory_mb
        self.peak_memory = max(self.peak_memory, current)
        return current < self.max_memory

    def track_allocation(self, size: int):
        """Track memory allocation."""
        self.current_memory_mb += size
        if self.current_memory_mb >= self.max_memory * 0.8:  # 80% threshold
            self._cleanup_required = True

class SourceValidator:
    """Validates content sources using streaming-first approach."""
    
    def __init__(self, config: SourceValidationConfig):
        """Initialize SourceValidator with configuration."""
        self.config = config
        self.resource_manager = ResourceManager(max_memory_mb=config.max_memory_mb)
        self.validation_state = ValidationState(batch_size=config.batch_size)
        self.start_time = time.time()
        self.throughput_counter = 0
        self.last_throughput_check = time.time()
        self.reliable_sources = {"research_paper", "academic_journal", "expert_review"}
        self.authority_sources = {"research_paper", "academic_journal"}

    async def validate_stream(self, content_stream: AsyncIterator[Dict[str, Any]]) -> AsyncIterator[Dict[str, Any]]:
        """
        Validates content sources using streaming approach.
        
        Args:
            content_stream: AsyncIterator yielding content items
            
        Yields:
            Status updates and ValidationResult objects
        """
        try:
            async with self.resource_manager:
                # Initial status
                yield {
                    "type": "status",
                    "stage": "validation_started",
                    "message": "Starting source validation process"
                }

                results = []
                async for content in content_stream:
                    processing_start = time.time()
                    
                    # Update throughput metrics
                    current_time = time.time()
                    if current_time - self.last_throughput_check >= 1.0:
                        logger.info(f"Current throughput: {self.throughput_counter} items/second")
                        self.throughput_counter = 0
                        self.last_throughput_check = current_time

                    if not self._validate_content_format(content):
                        self.validation_state.record_error()
                        if self.validation_state.get_error_rate() > 0.01:
                            logger.warning("Error rate exceeded threshold")
                        continue

                    try:
                        # Add to current batch
                        self.validation_state.current_batch.append(content)
                        
                        # Perform validation steps
                        trust_score = await self._calculate_trust_score(content)
                        reliability_score = await self._calculate_reliability_score(content)
                        authority_score = await self._calculate_authority_score(content)
                        freshness_score = await self._calculate_freshness_score(content)

                        # Track memory allocation
                        estimated_size = len(str(content)) * 2  # Rough estimation
                        self.resource_manager.track_allocation(estimated_size)

                        # Determine overall validity
                        is_valid = (
                            trust_score >= self.config.min_trust_score and
                            reliability_score >= self.config.min_reliability_score and
                            authority_score >= self.config.min_authority_score and
                            freshness_score >= self.config.min_freshness_score
                        )

                        result = ValidationResult(
                            trust_score=trust_score,
                            reliability_score=reliability_score,
                            authority_score=authority_score,
                            freshness_score=freshness_score,
                            is_valid=is_valid,
                            details=self._generate_details(content),
                            timestamp=time.time()
                        )
                        results.append(result)

                        # Update state
                        self.validation_state.record_success(content)
                        self.throughput_counter += 1

                        # Stream result
                        yield {
                            "type": "validation_result",
                            "index": len(results),
                            "total_so_far": len(results),
                            "result": result
                        }

                        # Interim analysis every N results
                        if len(results) % self.config.batch_size == 0:
                            yield {
                                "type": "interim_analysis",
                                "results_analyzed": len(results),
                                "validation_metrics": {
                                    "avg_trust_score": sum(r.trust_score for r in results) / len(results),
                                    "avg_reliability_score": sum(r.reliability_score for r in results) / len(results),
                                    "valid_sources": sum(1 for r in results if r.is_valid)
                                },
                                "message": "Processing validation results..."
                            }

                        # Check processing time
                        processing_time = time.time() - processing_start
                        if processing_time > 0.1:  # > 100ms
                            logger.warning(f"Slow validation detected: {processing_time*1000:.2f}ms")

                        # Check if cleanup needed
                        if self.validation_state.should_trigger_cleanup():
                            await self.resource_manager.cleanup()
                            self.validation_state.current_batch.clear()

                    except Exception as e:
                        logger.error(f"Error processing content: {str(e)}")
                        self.validation_state.record_error()
                        if self.validation_state.get_error_rate() > 0.01:
                            logger.warning("Error rate exceeded threshold")
                        continue

                # Final summary
                yield {
                    "type": "summary",
                    "total_processed": len(results),
                    "valid_sources": sum(1 for r in results if r.is_valid),
                    "validation_metrics": {
                        "avg_trust_score": sum(r.trust_score for r in results) / len(results) if results else 0,
                        "avg_reliability_score": sum(r.reliability_score for r in results) / len(results) if results else 0,
                        "error_rate": self.validation_state.get_error_rate()
                    }
                }

        except Exception as e:
            logger.error(f"Stream processing error: {str(e)}")
            # Attempt state recovery
            if self.validation_state.successful_items:
                logger.info("Attempting state recovery")
                for item in self.validation_state.successful_items:
                    try:
                        result = await self.validate(item)
                        yield {
                            "type": "validation_result",
                            "index": -1,  # Recovery result
                            "result": result
                        }
                    except Exception as recovery_error:
                        logger.error(f"Recovery failed: {str(recovery_error)}")
            raise
        finally:
            # Log final metrics
            total_time = time.time() - self.start_time
            total_processed = self.validation_state.processed_count
            logger.info(f"Total processing time: {total_time:.2f}s")
            logger.info(f"Items processed: {total_processed}")
            logger.info(f"Average throughput: {total_processed/total_time:.2f} items/second")
            logger.info(f"Peak memory usage: {self.resource_manager.peak_memory/1024/1024:.2f}MB")
            logger.info(f"Error rate: {self.validation_state.get_error_rate()*100:.2f}%")

    async def validate(self, content: Dict[str, Any]) -> ValidationResult:
        """
        Validates a single content item with enhanced error handling.
        
        Args:
            content: Dictionary containing content details
            
        Returns:
            ValidationResult object containing validation metrics
        """
        try:
            if not self._validate_content_format(content):
                logger.warning("Invalid content format, using default scores")
                return ValidationResult(
                    trust_score=0.5,
                    reliability_score=0.5,
                    authority_score=0.5,
                    freshness_score=0.5,
                    is_valid=False,
                    details={"error": "Invalid content format"}
                )

            async with self.resource_manager:
                # Calculate scores with individual error handling
                try:
                    trust_score = await self._calculate_trust_score(content)
                except Exception as e:
                    logger.warning(f"Error calculating trust score: {str(e)}")
                    trust_score = 0.5

                try:
                    reliability_score = await self._calculate_reliability_score(content)
                except Exception as e:
                    logger.warning(f"Error calculating reliability score: {str(e)}")
                    reliability_score = 0.5

                try:
                    authority_score = await self._calculate_authority_score(content)
                except Exception as e:
                    logger.warning(f"Error calculating authority score: {str(e)}")
                    authority_score = 0.5

                try:
                    freshness_score = await self._calculate_freshness_score(content)
                except Exception as e:
                    logger.warning(f"Error calculating freshness score: {str(e)}")
                    freshness_score = 0.5

                # Safe type conversion for comparison
                try:
                    is_valid = (
                        float(trust_score) >= float(self.config.min_trust_score) and
                        float(reliability_score) >= float(self.config.min_reliability_score) and
                        float(authority_score) >= float(self.config.min_authority_score) and
                        float(freshness_score) >= float(self.config.min_freshness_score)
                    )
                except Exception as e:
                    logger.warning(f"Error determining validity: {str(e)}")
                    is_valid = False

                try:
                    details = self._generate_details(content)
                except Exception as e:
                    logger.warning(f"Error generating details: {str(e)}")
                    details = {"error": "Failed to generate details"}

                return ValidationResult(
                    trust_score=float(trust_score),
                    reliability_score=float(reliability_score),
                    authority_score=float(authority_score),
                    freshness_score=float(freshness_score),
                    is_valid=is_valid,
                    details=details
                )

        except Exception as e:
            logger.error(f"Critical error validating content: {str(e)}")
            # Return safe default scores instead of raising
            return ValidationResult(
                trust_score=0.5,
                reliability_score=0.5,
                authority_score=0.5,
                freshness_score=0.5,
                is_valid=False,
                details={"error": f"Validation failed: {str(e)}"}
            )

    def _validate_content_format(self, content: Dict[str, Any]) -> bool:
        """Validates content has required fields."""
        if not content or not isinstance(content, dict):
            return False
            
        required_fields = {"text", "sources", "depth"}
        return all(field in content for field in required_fields)

    async def _calculate_trust_score(self, content: Dict[str, Any]) -> float:
        """Calculates trust score based on source reliability and citations."""
        if not content["sources"]:
            return 0.0

        reliable_count = len([s for s in content["sources"] if s in self.reliable_sources])
        base_score = reliable_count / len(content["sources"])
        
        # Adjust for citations
        citations = content.get("citations", 0)
        citation_bonus = min(citations / 10, 0.3)  # Max 0.3 bonus for citations
        
        return min(base_score + citation_bonus, 1.0)

    async def _calculate_reliability_score(self, content: Dict[str, Any]) -> float:
        """Calculates reliability score based on source quality and verification."""
        if not content["sources"]:
            return 0.0

        # Base reliability from source types
        reliable_sources = len([s for s in content["sources"] if s in self.reliable_sources])
        base_score = reliable_sources / len(content["sources"])

        # Adjust for technical accuracy if available
        try:
            if "technical_accuracy" in content:
                accuracy = float(content["technical_accuracy"])
                if 0 <= accuracy <= 1:  # Validate range
                    base_score = (base_score + accuracy) / 2
        except (ValueError, TypeError):
            logger.warning("Invalid technical_accuracy value, using base score")

        return base_score

    async def _calculate_authority_score(self, content: Dict[str, Any]) -> float:
        """Calculates authority score based on source credibility."""
        if not content["sources"]:
            return 0.0

        # Count authoritative sources
        authority_count = len([s for s in content["sources"] if s in self.authority_sources])
        base_score = authority_count / len(content["sources"])

        # Adjust for depth
        depth_scores = {
            "comprehensive": 1.0,
            "intermediate": 0.7,
            "shallow": 0.4
        }
        depth_factor = depth_scores.get(content["depth"], 0.1)
        
        return (base_score * 0.7 + depth_factor * 0.3)  # Weight authority more than depth

    async def _calculate_freshness_score(self, content: Dict[str, Any]) -> float:
        """Calculates freshness score based on source types and age."""
        # High-quality sources always get maximum freshness
        if any(source in self.authority_sources for source in content["sources"]):
            return 1.0

        # For other sources, check timestamp if available
        if "timestamp" in content:
            current_time = time.time()
            content_age = current_time - content["timestamp"]
            
            # Score based on age brackets
            if content_age < 86400:  # Less than 1 day
                return 1.0
            elif content_age < 604800:  # Less than 1 week
                return 0.9
            elif content_age < 2592000:  # Less than 1 month
                return 0.8
            elif content_age < 7776000:  # Less than 3 months
                return 0.7
            elif content_age < 15552000:  # Less than 6 months
                return 0.6
            else:
                return 0.5

        # Default to medium freshness if no timestamp
        return 0.7

    def _generate_details(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generates detailed validation information."""
        return {
            "source_count": len(content["sources"]),
            "reliable_sources": len([s for s in content["sources"] if s in self.reliable_sources]),
            "authority_sources": len([s for s in content["sources"] if s in self.authority_sources]),
            "has_citations": "citations" in content,
            "depth_level": content["depth"],
            "technical_accuracy": content.get("technical_accuracy", None),
            "timestamp": content.get("timestamp", None)
        }