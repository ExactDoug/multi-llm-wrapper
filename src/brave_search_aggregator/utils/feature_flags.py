"""Feature flag management for controlled feature rollout."""
from dataclasses import dataclass
from typing import Dict, Optional
import os
from enum import Enum

class FeatureState(Enum):
    """Possible states for a feature."""
    OFF = "off"
    BETA = "beta"
    ON = "on"

    @classmethod
    def from_env(cls, value: str) -> 'FeatureState':
        """Convert environment variable value to FeatureState."""
        value = value.lower()
        if value in ("false", "0", "off"):
            return cls.OFF
        elif value in ("true", "1", "on"):
            return cls.ON
        elif value == "beta":
            return cls.BETA
        return cls.OFF  # Default to OFF for safety

@dataclass
class Feature:
    """Feature configuration."""
    name: str
    description: str
    state: FeatureState
    rollout_percentage: float = 100.0  # For beta features

class FeatureFlags:
    """
    Feature flag management system for controlling feature rollout.
    Supports staged rollouts and A/B testing configurations.
    """
    
    def __init__(self):
        """Initialize feature flags with default configuration."""
        self.features: Dict[str, Feature] = {
            "moe_routing": Feature(
                name="moe_routing",
                description="MoE-style routing for model selection",
                state=FeatureState.from_env(os.getenv("FEATURE_MOE_ROUTING", "off")),
                rollout_percentage=float(os.getenv("FEATURE_MOE_ROUTING_ROLLOUT", "50.0"))
            ),
            "task_vectors": Feature(
                name="task_vectors",
                description="Task vector operations for knowledge combination",
                state=FeatureState.from_env(os.getenv("FEATURE_TASK_VECTORS", "off")),
                rollout_percentage=float(os.getenv("FEATURE_TASK_VECTORS_ROLLOUT", "30.0"))
            ),
            "slerp_merging": Feature(
                name="slerp_merging",
                description="SLERP-based response merging",
                state=FeatureState.from_env(os.getenv("FEATURE_SLERP_MERGING", "off")),
                rollout_percentage=float(os.getenv("FEATURE_SLERP_MERGING_ROLLOUT", "30.0"))
            ),
            "parallel_processing": Feature(
                name="parallel_processing",
                description="Parallel query processing across sources",
                state=FeatureState.from_env(os.getenv("FEATURE_PARALLEL_PROCESSING", "on")),
                rollout_percentage=100.0
            ),
            "source_specific_processing": Feature(
                name="source_specific_processing",
                description="Source-specific processing with nuance preservation",
                state=FeatureState.from_env(os.getenv("FEATURE_SOURCE_SPECIFIC", "off")),
                rollout_percentage=float(os.getenv("FEATURE_SOURCE_SPECIFIC_ROLLOUT", "50.0"))
            ),
            "grid_compatibility": Feature(
                name="grid_compatibility",
                description="Maintain compatibility with existing grid interface",
                state=FeatureState.from_env(os.getenv("FEATURE_GRID_COMPAT", "on")),
                rollout_percentage=100.0
            )
        }
    
    def is_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: Name of the feature to check
            
        Returns:
            True if feature is enabled, False otherwise
        """
        feature = self.features.get(feature_name)
        if not feature:
            return False
            
        return feature.state == FeatureState.ON

    def is_beta_enabled(self, feature_name: str, user_id: Optional[str] = None) -> bool:
        """
        Check if a beta feature is enabled for a specific user.
        
        Args:
            feature_name: Name of the feature to check
            user_id: Optional user identifier for consistent rollout
            
        Returns:
            True if beta feature is enabled for this user, False otherwise
        """
        feature = self.features.get(feature_name)
        if not feature:
            return False
            
        if feature.state == FeatureState.ON:
            return True
            
        if feature.state == FeatureState.OFF:
            return False
            
        # For beta features, use rollout percentage
        if feature.state == FeatureState.BETA:
            if not user_id:
                return False
                
            # Use hash of user_id for consistent rollout
            user_hash = hash(user_id)
            normalized_hash = (user_hash % 100) + 100 if user_hash < 0 else user_hash % 100
            return normalized_hash < feature.rollout_percentage
            
        return False

    def get_feature_state(self, feature_name: str) -> Optional[FeatureState]:
        """
        Get the current state of a feature.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            FeatureState if feature exists, None otherwise
        """
        feature = self.features.get(feature_name)
        return feature.state if feature else None

    def get_rollout_percentage(self, feature_name: str) -> Optional[float]:
        """
        Get the rollout percentage for a feature.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            Rollout percentage if feature exists, None otherwise
        """
        feature = self.features.get(feature_name)
        return feature.rollout_percentage if feature else None

    def update_feature_state(
        self,
        feature_name: str,
        state: FeatureState,
        rollout_percentage: Optional[float] = None
    ) -> bool:
        """
        Update the state of a feature.
        
        Args:
            feature_name: Name of the feature to update
            state: New state for the feature
            rollout_percentage: Optional new rollout percentage
            
        Returns:
            True if update successful, False otherwise
        """
        feature = self.features.get(feature_name)
        if not feature:
            return False
            
        feature.state = state
        if rollout_percentage is not None:
            feature.rollout_percentage = max(0.0, min(100.0, rollout_percentage))
            
        return True

# Global instance
feature_flags = FeatureFlags()