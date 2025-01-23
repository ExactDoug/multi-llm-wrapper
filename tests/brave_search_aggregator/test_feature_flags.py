"""Tests for feature flag management system."""
import pytest
from src.brave_search_aggregator.utils.feature_flags import (
    FeatureFlags,
    FeatureState,
    Feature
)

@pytest.fixture
def feature_flags():
    """Fixture providing a FeatureFlags instance."""
    return FeatureFlags()

def test_feature_initialization(feature_flags):
    """Test feature flag initialization."""
    # Check all expected features are present
    expected_features = {
        "moe_routing",
        "task_vectors",
        "slerp_merging",
        "parallel_processing",
        "source_specific_processing",
        "grid_compatibility"
    }
    
    assert set(feature_flags.features.keys()) == expected_features
    
    # Check each feature has required attributes
    for feature in feature_flags.features.values():
        assert isinstance(feature, Feature)
        assert feature.name
        assert feature.description
        assert isinstance(feature.state, FeatureState)
        assert isinstance(feature.rollout_percentage, float)
        assert 0 <= feature.rollout_percentage <= 100

def test_is_enabled(feature_flags):
    """Test feature enabled check."""
    # Test ON state
    feature_flags.update_feature_state("moe_routing", FeatureState.ON)
    assert feature_flags.is_enabled("moe_routing")
    
    # Test OFF state
    feature_flags.update_feature_state("moe_routing", FeatureState.OFF)
    assert not feature_flags.is_enabled("moe_routing")
    
    # Test BETA state (should return False for is_enabled)
    feature_flags.update_feature_state("moe_routing", FeatureState.BETA)
    assert not feature_flags.is_enabled("moe_routing")
    
    # Test non-existent feature
    assert not feature_flags.is_enabled("non_existent_feature")

def test_beta_feature_rollout(feature_flags):
    """Test beta feature rollout behavior."""
    feature_flags.update_feature_state(
        "task_vectors",
        FeatureState.BETA,
        rollout_percentage=50.0
    )
    
    # Test without user_id
    assert not feature_flags.is_beta_enabled("task_vectors")
    
    # Test with different user_ids
    enabled_count = 0
    total_tests = 1000
    
    for i in range(total_tests):
        if feature_flags.is_beta_enabled("task_vectors", f"user_{i}"):
            enabled_count += 1
    
    # Should be roughly 50% enabled (allowing for some variance)
    percentage = (enabled_count / total_tests) * 100
    assert 45 <= percentage <= 55

def test_feature_state_updates(feature_flags):
    """Test feature state update functionality."""
    # Test valid update
    assert feature_flags.update_feature_state(
        "slerp_merging",
        FeatureState.BETA,
        rollout_percentage=75.0
    )
    
    feature = feature_flags.features["slerp_merging"]
    assert feature.state == FeatureState.BETA
    assert feature.rollout_percentage == 75.0
    
    # Test invalid feature name
    assert not feature_flags.update_feature_state(
        "non_existent",
        FeatureState.ON
    )
    
    # Test rollout percentage bounds
    assert feature_flags.update_feature_state(
        "slerp_merging",
        FeatureState.BETA,
        rollout_percentage=150.0  # Should be capped at 100
    )
    assert feature_flags.features["slerp_merging"].rollout_percentage == 100.0
    
    assert feature_flags.update_feature_state(
        "slerp_merging",
        FeatureState.BETA,
        rollout_percentage=-50.0  # Should be floored at 0
    )
    assert feature_flags.features["slerp_merging"].rollout_percentage == 0.0

def test_feature_state_getters(feature_flags):
    """Test feature state getter methods."""
    # Set up test state
    feature_flags.update_feature_state(
        "parallel_processing",
        FeatureState.BETA,
        rollout_percentage=30.0
    )
    
    # Test get_feature_state
    assert feature_flags.get_feature_state("parallel_processing") == FeatureState.BETA
    assert feature_flags.get_feature_state("non_existent") is None
    
    # Test get_rollout_percentage
    assert feature_flags.get_rollout_percentage("parallel_processing") == 30.0
    assert feature_flags.get_rollout_percentage("non_existent") is None

def test_consistent_beta_rollout(feature_flags):
    """Test that beta rollout is consistent for the same user."""
    feature_flags.update_feature_state(
        "source_specific_processing",
        FeatureState.BETA,
        rollout_percentage=50.0
    )
    
    # Same user should get consistent results
    user_id = "test_user_123"
    first_result = feature_flags.is_beta_enabled("source_specific_processing", user_id)
    
    for _ in range(100):
        assert feature_flags.is_beta_enabled(
            "source_specific_processing",
            user_id
        ) == first_result

def test_grid_compatibility_feature(feature_flags):
    """Test grid compatibility feature behavior."""
    # Should be ON by default
    assert feature_flags.is_enabled("grid_compatibility")
    
    # Test state transitions
    feature_flags.update_feature_state("grid_compatibility", FeatureState.OFF)
    assert not feature_flags.is_enabled("grid_compatibility")
    
    feature_flags.update_feature_state("grid_compatibility", FeatureState.BETA)
    assert not feature_flags.is_enabled("grid_compatibility")
    
    feature_flags.update_feature_state("grid_compatibility", FeatureState.ON)
    assert feature_flags.is_enabled("grid_compatibility")