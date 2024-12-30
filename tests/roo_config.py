"""
Roo-cline test configuration for Multi-LLM Wrapper
"""

# Test configuration for different components
WRAPPER_TEST_CONFIG = {
    "component_name": "LLMWrapper",
    "test_priorities": [
        "input_validation",
        "error_handling",
        "response_processing",
        "provider_interaction",
        "configuration_handling"
    ],
    "coverage_requirements": {
        "line_coverage": 80,
        "branch_coverage": 70,
        "function_coverage": 90
    },
    "edge_cases": [
        "empty_prompt",
        "invalid_model",
        "timeout_scenarios",
        "rate_limit_handling",
        "malformed_responses"
    ]
}

# Configuration test scenarios
CONFIG_TEST_SCENARIOS = {
    "default_config": {
        "verify_defaults": True,
        "test_overrides": True,
        "validate_types": True
    },
    "custom_config": {
        "test_all_parameters": True,
        "validate_constraints": True
    }
}

# Response validation scenarios
RESPONSE_TEST_SCENARIOS = {
    "success_cases": [
        "standard_response",
        "long_response",
        "special_characters"
    ],
    "error_cases": [
        "provider_error",
        "timeout_error",
        "validation_error"
    ],
    "edge_cases": [
        "empty_response",
        "maximum_length",
        "rate_limit"
    ]
}

# Continuous testing configuration
CONTINUOUS_TEST_CONFIG = {
    "watch_paths": ["src/wrapper.py", "src/config.py"],
    "ignore_patterns": ["*.pyc", "__pycache__"],
    "run_on_change": True,
    "notification_level": "all"
}
