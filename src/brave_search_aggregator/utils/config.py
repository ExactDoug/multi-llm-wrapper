"""Configuration models for content enrichment and validation."""
from dataclasses import dataclass
from typing import Dict

@dataclass
class Config:
    """Base configuration class."""
    max_memory_mb: int = 10
    enable_streaming: bool = True
    batch_size: int = 3
    requests_per_second: int = 20
    connection_timeout_sec: int = 30
    max_results: int = 20

@dataclass
class QualityConfig:
    """Configuration for quality scoring components."""
    # Core quality thresholds
    min_quality_score: float = 0.8
    min_confidence_score: float = 0.7
    required_depth: str = "comprehensive"

    # Performance settings
    max_memory_mb: int = 10
    enable_streaming: bool = True
    batch_size: int = 3

    # Source weights for quality calculation
    source_weights: Dict[str, float] = None
    quality_metrics: Dict[str, float] = None

    def __post_init__(self):
        """Initialize default weights and metrics."""
        if self.source_weights is None:
            self.source_weights = {
                "research_paper": 1.0,
                "academic_journal": 0.9,
                "expert_review": 0.8,
                "educational_site": 0.7,
                "blog": 0.5,
                "social_media": 0.3
            }
        
        if self.quality_metrics is None:
            self.quality_metrics = {
                "technical_accuracy": 0.4,
                "source_quality": 0.3,
                "depth_score": 0.2,
                "citation_score": 0.1
            }

@dataclass
class EnricherConfig:
    """Configuration for content enrichment components."""
    # Core enrichment thresholds
    min_enrichment_score: float = 0.8
    min_diversity_score: float = 0.7
    min_depth_score: float = 0.7
    required_citations: int = 2

    # Performance requirements
    max_enrichment_time_ms: int = 100  # First enrichment < 100ms
    max_memory_mb: int = 10            # Critical memory limit
    max_chunk_size_kb: int = 16        # Streaming chunk size limit

    # Resource constraints
    requests_per_second: int = 20      # API rate limit
    connection_timeout_sec: int = 30   # Connection timeout
    max_results: int = 20              # Results per query limit

    # Streaming support
    enable_streaming: bool = True
    batch_size: int = 3
    min_chunks_per_response: int = 3

    # Memory Management
    enable_memory_tracking: bool = True
    cleanup_timeout_sec: int = 5
    enable_resource_cleanup: bool = True

    # Error Recovery
    enable_early_error_detection: bool = True
    enable_partial_results: bool = True
    max_retries: int = 3
    retry_delay_ms: int = 100

    # Performance Monitoring
    enable_performance_tracking: bool = True
    track_enrichment_timing: bool = True
    track_memory_usage: bool = True
    track_error_rates: bool = True
    track_api_status: bool = True

    # Quality Scoring Configuration
    source_weights: Dict[str, float] = None
    quality_metrics: Dict[str, float] = None

    # Source Validation Configuration
    min_trust_score: float = 0.8
    min_reliability_score: float = 0.8
    min_authority_score: float = 0.7
    min_freshness_score: float = 0.7

    # Enrichment Steps
    enrichment_steps = [
        'quality_assessment',
        'diversity_analysis',
        'depth_evaluation',
        'source_validation'
    ]

    # Enrichment Metrics
    enrichment_metrics = [
        'enrichment_score',
        'diversity_score',
        'depth_score',
        'quality_metrics'
    ]

    # Error Handling Steps
    error_handling_steps = [
        'early_detection',
        'partial_results',
        'recovery_process'
    ]

    # Error Validation Metrics
    error_validation_metrics = [
        'error_detection',
        'result_preservation',
        'cleanup_verification'
    ]

    def __post_init__(self):
        """Initialize default weights and metrics."""
        if self.source_weights is None:
            self.source_weights = {
                "research_paper": 1.0,
                "academic_journal": 0.9,
                "expert_review": 0.8,
                "educational_site": 0.7,
                "blog": 0.5,
                "social_media": 0.3
            }
        
        if self.quality_metrics is None:
            self.quality_metrics = {
                "technical_accuracy": 0.4,
                "source_quality": 0.3,
                "depth_score": 0.2,
                "citation_score": 0.1
            }

    def to_quality_config(self) -> 'QualityConfig':
        """
        Convert EnricherConfig to QualityConfig with type validation.
        
        Returns:
            QualityConfig with validated values
        
        Raises:
            ValueError: If required values are invalid
        """
        # Validate score thresholds
        try:
            min_quality_score = float(self.min_enrichment_score)
            if not 0 <= min_quality_score <= 1:
                raise ValueError(f"min_quality_score out of range: {min_quality_score}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid min_enrichment_score: {e}")

        try:
            min_confidence_score = float(self.min_diversity_score)
            if not 0 <= min_confidence_score <= 1:
                raise ValueError(f"min_confidence_score out of range: {min_confidence_score}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid min_diversity_score: {e}")

        # Determine depth requirement with validation
        try:
            depth_score = float(self.min_depth_score)
            if not 0 <= depth_score <= 1:
                raise ValueError(f"min_depth_score out of range: {depth_score}")
            
            required_depth = (
                "comprehensive" if depth_score >= 0.8 else
                "intermediate" if depth_score >= 0.6 else
                "shallow"
            )
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid min_depth_score: {e}")

        # Validate performance settings
        try:
            max_memory = int(self.max_memory_mb)
            if max_memory <= 0:
                raise ValueError(f"Invalid max_memory_mb: {max_memory}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid max_memory_mb: {e}")

        try:
            batch_size = int(self.batch_size)
            if batch_size <= 0:
                raise ValueError(f"Invalid batch_size: {batch_size}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid batch_size: {e}")

        # Validate source weights
        if self.source_weights is not None:
            if not isinstance(self.source_weights, dict):
                raise ValueError("source_weights must be a dictionary")
            for source, weight in self.source_weights.items():
                try:
                    float_weight = float(weight)
                    if not 0 <= float_weight <= 1:
                        raise ValueError(f"Weight out of range for source {source}: {float_weight}")
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Invalid weight for source {source}: {e}")

        # Validate quality metrics
        if self.quality_metrics is not None:
            if not isinstance(self.quality_metrics, dict):
                raise ValueError("quality_metrics must be a dictionary")
            for metric, value in self.quality_metrics.items():
                try:
                    float_value = float(value)
                    if not 0 <= float_value <= 1:
                        raise ValueError(f"Metric out of range for {metric}: {float_value}")
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Invalid value for metric {metric}: {e}")

        # Create config with validated values
        return QualityConfig(
            min_quality_score=min_quality_score,
            min_confidence_score=min_confidence_score,
            required_depth=required_depth,
            max_memory_mb=max_memory,
            enable_streaming=bool(self.enable_streaming),
            batch_size=batch_size,
            source_weights=self.source_weights,
            quality_metrics=self.quality_metrics
        )

    def to_validation_config(self) -> 'SourceValidationConfig':
        """
        Convert EnricherConfig to SourceValidationConfig with type validation.
        
        Returns:
            SourceValidationConfig with validated values
        
        Raises:
            ValueError: If required values are invalid
        """
        validated = {}

        # Validate score thresholds
        for score_name in ['min_trust_score', 'min_reliability_score',
                         'min_authority_score', 'min_freshness_score']:
            try:
                score = float(getattr(self, score_name))
                if not 0 <= score <= 1:
                    raise ValueError(f"{score_name} out of range: {score}")
                validated[score_name] = score
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid {score_name}: {e}")

        # Validate integer requirements
        int_fields = {
            'required_citations': (1, None),  # min, max (None for no max)
            'max_enrichment_time_ms': (1, None),
            'max_memory_mb': (1, None),
            'max_chunk_size_kb': (1, None),
            'requests_per_second': (1, None),
            'connection_timeout_sec': (1, None),
            'max_results': (1, None),
            'batch_size': (1, None),
            'min_chunks_per_response': (1, None),
            'cleanup_timeout_sec': (1, None),
            'max_retries': (0, None),
            'retry_delay_ms': (0, None)
        }

        for field, (min_val, max_val) in int_fields.items():
            try:
                value = int(getattr(self, field))
                if min_val is not None and value < min_val:
                    raise ValueError(f"{field} below minimum: {value} < {min_val}")
                if max_val is not None and value > max_val:
                    raise ValueError(f"{field} above maximum: {value} > {max_val}")
                validated[field] = value
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid {field}: {e}")

        # Validate boolean flags
        bool_fields = [
            'enable_streaming',
            'enable_memory_tracking',
            'enable_resource_cleanup',
            'enable_early_error_detection',
            'enable_partial_results',
            'enable_performance_tracking',
            'track_memory_usage',
            'track_error_rates',
            'track_api_status'
        ]

        for field in bool_fields:
            validated[field] = bool(getattr(self, field))

        # Create config with validated values
        return SourceValidationConfig(
            min_trust_score=validated['min_trust_score'],
            min_reliability_score=validated['min_reliability_score'],
            min_authority_score=validated['min_authority_score'],
            min_freshness_score=validated['min_freshness_score'],
            required_citations=validated['required_citations'],
            max_validation_time_ms=validated['max_enrichment_time_ms'],
            max_memory_mb=validated['max_memory_mb'],
            max_chunk_size_kb=validated['max_chunk_size_kb'],
            requests_per_second=validated['requests_per_second'],
            connection_timeout_sec=validated['connection_timeout_sec'],
            max_results=validated['max_results'],
            enable_streaming=validated['enable_streaming'],
            batch_size=validated['batch_size'],
            min_chunks_per_response=validated['min_chunks_per_response'],
            enable_memory_tracking=validated['enable_memory_tracking'],
            cleanup_timeout_sec=validated['cleanup_timeout_sec'],
            enable_resource_cleanup=validated['enable_resource_cleanup'],
            enable_early_error_detection=validated['enable_early_error_detection'],
            enable_partial_results=validated['enable_partial_results'],
            max_retries=validated['max_retries'],
            retry_delay_ms=validated['retry_delay_ms'],
            enable_performance_tracking=validated['enable_performance_tracking'],
            track_memory_usage=validated['track_memory_usage'],
            track_error_rates=validated['track_error_rates'],
            track_api_status=validated['track_api_status']
        )


@dataclass
class SourceValidationConfig:
    """Configuration for source validation components."""
    # Core validation thresholds
    min_trust_score: float = 0.8
    min_reliability_score: float = 0.8
    min_authority_score: float = 0.7
    min_freshness_score: float = 0.7
    required_citations: int = 2

    # Performance requirements (aligned with critical requirements)
    max_validation_time_ms: int = 100  # First validation < 100ms
    complete_timeout_ms: int = 5000    # Complete within 5s
    max_memory_mb: int = 10            # Critical memory limit
    max_chunk_size_kb: int = 16        # Streaming chunk size limit

    # Resource constraints (aligned with API limits)
    requests_per_second: int = 20      # API rate limit
    connection_timeout_sec: int = 30   # Connection timeout
    max_results: int = 20              # Results per query limit

    # Async Iterator Pattern Support
    enable_streaming: bool = True
    batch_size: int = 3
    min_chunks_per_response: int = 3

    # Memory Management
    enable_memory_tracking: bool = True
    cleanup_timeout_sec: int = 5
    enable_resource_cleanup: bool = True

    # Error Recovery
    enable_early_error_detection: bool = True
    enable_partial_results: bool = True
    max_retries: int = 3
    retry_delay_ms: int = 100

    # Performance Monitoring
    enable_performance_tracking: bool = True
    track_validation_timing: bool = True
    track_memory_usage: bool = True
    track_error_rates: bool = True
    track_api_status: bool = True

    # Validation Steps
    validation_steps = [
        'authority_check',
        'reliability_assessment',
        'freshness_evaluation'
    ]

    # Validation Metrics
    validation_metrics = [
        'trust_score',
        'reliability_metrics',
        'authority_level'
    ]

    # Error Handling Steps
    error_handling_steps = [
        'early_detection',
        'partial_results',
        'recovery_process'
    ]

    # Error Validation Metrics
    error_validation_metrics = [
        'error_detection',
        'result_preservation',
        'cleanup_verification'
    ]