"""
General retry utility with exponential backoff and jitter.

This module provides a reusable retry decorator that can be applied to any function
to handle transient failures with intelligent backoff strategies.
"""

from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type, RetryError
from typing import Callable, Any, Union, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def retry_it(func: Callable, attempts: int = 3) -> Callable:
    """
    General retry decorator with exponential backoff and jitter.
    
    Args:
        func: Function to retry
        attempts: Maximum number of attempts (default: 3)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry_it(attempts=5)
        def api_call():
            # Some API call that might fail
            pass
            
        # Or use it directly
        result = retry_it(some_function, attempts=5)()
    """
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential_jitter(initial=1, max=60)
    )(func)


class EmptySearchError(Exception):
    """Exception raised when a search returns empty results."""
    pass


class AnalysisError(Exception):
    """Exception raised when analysis processing fails."""
    pass


class APIError(Exception):
    """Exception raised when API calls fail."""
    pass


def create_retry_wrapper(func: Callable, attempts: int = 3, 
                        retry_on_empty: bool = True, 
                        retry_on_api_failure: bool = True,
                        retry_on_any_exception: bool = False,
                        return_on_failure: Optional[Any] = None,
                        fail_gracefully: bool = True) -> Callable:
    """
    Create a retry wrapper with configurable retry conditions.
    
    Args:
        func: Function to wrap
        attempts: Maximum retry attempts
        retry_on_empty: Whether to retry on empty search results
        retry_on_api_failure: Whether to retry on API failures
        retry_on_any_exception: Whether to retry on ANY exception (overrides other settings)
        return_on_failure: Value to return when all retries fail (if fail_gracefully=True)
        fail_gracefully: If True, return return_on_failure instead of raising RetryError
        
    Returns:
        Wrapped function with retry logic
    """
    
    # Build list of exception types to retry on
    retry_exceptions = []
    
    if retry_on_any_exception:
        # Retry on any exception - this will catch everything including RateLimitError
        retry_exceptions = [Exception]
    else:
        # Use specific exception types
        if retry_on_empty:
            retry_exceptions.append(EmptySearchError)
        
        if retry_on_api_failure:
            retry_exceptions.extend([APIError, ConnectionError, TimeoutError])
    
    # Create the proper tenacity retry condition
    if retry_exceptions:
        retry_condition = retry_if_exception_type(tuple(retry_exceptions))
    else:
        # If no exceptions specified, don't retry
        retry_condition = retry_if_exception_type(())
    
    @retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential_jitter(initial=1, max=60),
        retry=retry_condition
    )
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.info(f"Function {func.__name__} failed: {str(e)}")
            raise
    
    def graceful_wrapper(*args, **kwargs):
        """Outer wrapper that handles RetryError gracefully if configured."""
        try:
            return wrapper(*args, **kwargs)
        except RetryError as e:
            if fail_gracefully:
                logger.warning(f"Function {func.__name__} failed after {attempts} attempts, returning default value")
                return return_on_failure
            else:
                # Re-raise the RetryError if not failing gracefully
                raise
    
    return graceful_wrapper 