import logging
import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional, Union

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """Context information for errors."""
    operation: str
    timestamp: float = field(default_factory=time.time)
    partial_results: List = field(default_factory=list)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

class ErrorHandler:
    """
    Enhanced error handling for streaming operations.
    Provides partial result preservation and recovery strategies.
    """
    def __init__(self):
        self._recovery_strategies = {}
        self._partial_results = {}
        self._error_stats = {
            "total_errors": 0,
            "recovered_errors": 0,
            "unrecoverable_errors": 0
        }
    
    def register_recovery_strategy(self, error_type, strategy_func):
        """
        Register a recovery strategy for a specific error type.
        
        Args:
            error_type: The type of exception to handle
            strategy_func: A callable that handles the error recovery
        """
        self._recovery_strategies[error_type] = strategy_func
    
    async def handle_error(self, error: Exception, context: ErrorContext) -> Dict:
        """
        Handle an error with appropriate recovery strategy.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            Dict containing error details and partial results if available
        """
        self._error_stats["total_errors"] += 1
        
        # Log the error
        logger.error(f"Error in {context.operation}: {str(error)}")
        logger.debug(f"Error traceback: {traceback.format_exc()}")
        
        # Store partial results
        self._partial_results[context.operation] = context.partial_results
        
        # Check if we have a recovery strategy
        for error_type, strategy in self._recovery_strategies.items():
            if isinstance(error, error_type):
                if context.recovery_attempts < context.max_recovery_attempts:
                    context.recovery_attempts += 1
                    try:
                        logger.info(f"Attempting recovery for {context.operation} (attempt {context.recovery_attempts})")
                        result = await strategy(error, context)
                        self._error_stats["recovered_errors"] += 1
                        
                        # Ensure result has the correct type
                        if isinstance(result, dict) and "type" not in result:
                            result["type"] = "error"
                        elif not isinstance(result, dict):
                            result = {
                                "type": "error",
                                "operation": context.operation,
                                "error": str(error),
                                "partial_results": context.partial_results,
                                "recoverable": True
                            }
                        return result
                    except Exception as recovery_error:
                        logger.error(f"Recovery failed: {str(recovery_error)}")
                else:
                    logger.warning(f"Maximum recovery attempts ({context.max_recovery_attempts}) reached")
        
        # If we get here, we couldn't recover
        self._error_stats["unrecoverable_errors"] += 1
        
        # Create error response with partial results
        return {
            "type": "error",
            "operation": context.operation,
            "error": str(error),
            "partial_results": context.partial_results,
            "recoverable": False
        }
    
    async def get_partial_results(self, operation: str) -> List:
        """
        Get partial results from a failed operation.
        
        Args:
            operation: The operation identifier
            
        Returns:
            List of partial results if available, or empty list
        """
        return self._partial_results.get(operation, [])
    
    def get_error_stats(self) -> Dict[str, int]:
        """
        Get error handling statistics.
        
        Returns:
            Dict containing error statistics
        """
        return self._error_stats.copy()