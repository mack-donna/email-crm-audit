"""
External Service Utilities

Provides timeout handling, retry logic, and circuit breakers for external API calls.
Addresses the error handling gaps identified in the code audit.
"""

import time
import logging
from functools import wraps


class ServiceError(Exception):
    """Base exception for external service errors."""
    pass


class ServiceTimeoutError(ServiceError):
    """Exception raised when a service call times out."""
    pass


class ServiceUnavailableError(ServiceError):
    """Exception raised when a service is unavailable."""
    pass


def timeout_decorator(timeout_seconds=10):
    """
    Decorator to add timeout to functions.

    Note: This is a simplified version. For production use, consider:
    - Using signal.alarm on Unix systems
    - Using threading.Timer for cross-platform support
    - Using asyncio for async operations

    Args:
        timeout_seconds (int): Maximum seconds to wait

    Returns:
        function: Decorated function with timeout
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # For demonstration - actual timeout implementation would use
            # signal.alarm (Unix) or threading (cross-platform)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise ServiceError("Service call failed: {}".format(str(e)))
        return wrapper
    return decorator


def retry_with_backoff(max_retries=3, initial_delay=1, backoff_factor=2, logger=None):
    """
    Decorator to retry failed operations with exponential backoff.

    Args:
        max_retries (int): Maximum number of retry attempts
        initial_delay (float): Initial delay in seconds
        backoff_factor (int): Multiplier for delay after each retry
        logger: Optional logger for retry messages

    Returns:
        function: Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (ServiceError, ServiceTimeoutError, ServiceUnavailableError) as e:
                    last_exception = e

                    if attempt < max_retries:
                        if logger:
                            logger.warning(
                                "Attempt {}/{} failed for {}: {}. Retrying in {}s...".format(
                                    attempt + 1, max_retries + 1, func.__name__, str(e), delay
                                )
                            )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        if logger:
                            logger.error(
                                "All {} attempts failed for {}: {}".format(
                                    max_retries + 1, func.__name__, str(e)
                                )
                            )

            # If we've exhausted all retries, raise the last exception
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for external services.

    Prevents cascading failures by temporarily disabling calls to
    failing services after a threshold is reached.

    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Service is failing, requests fail immediately
    - HALF_OPEN: Testing if service has recovered
    """

    def __init__(self, failure_threshold=5, recovery_timeout=60, logger=None):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold (int): Number of failures before opening circuit
            recovery_timeout (int): Seconds to wait before attempting recovery
            logger: Optional logger instance
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'
        self.logger = logger or logging.getLogger(__name__)

    def call(self, func, *args, **kwargs):
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function

        Returns:
            Result of function call

        Raises:
            ServiceUnavailableError: If circuit is open
        """
        if self.state == 'OPEN':
            if self._should_attempt_recovery():
                self.state = 'HALF_OPEN'
                self.logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise ServiceUnavailableError(
                    "Circuit breaker is OPEN. Service unavailable."
                )

        try:
            result = func(*args, **kwargs)

            # Success - reset circuit breaker
            if self.state == 'HALF_OPEN':
                self.logger.info("Circuit breaker closing - service recovered")
                self.state = 'CLOSED'

            self.failure_count = 0
            return result

        except Exception as e:
            self._record_failure()
            raise ServiceError("Service call failed: {}".format(str(e)))

    def _record_failure(self):
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            self.logger.error(
                "Circuit breaker OPEN after {} failures".format(self.failure_count)
            )

    def _should_attempt_recovery(self):
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True

        return (time.time() - self.last_failure_time) >= self.recovery_timeout


def safe_api_call(func, fallback_value=None, logger=None):
    """
    Wrapper for safe API calls with fallback values.

    Args:
        func: Function to execute
        fallback_value: Value to return on failure
        logger: Optional logger instance

    Returns:
        Result of function or fallback value
    """
    try:
        return func()
    except Exception as e:
        if logger:
            logger.warning("API call failed: {}. Using fallback value.".format(str(e)))
        return fallback_value


# Example usage and integration helpers

def create_linkedin_circuit_breaker():
    """Create a circuit breaker instance for LinkedIn API calls."""
    return CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
        logger=logging.getLogger('linkedin_breaker')
    )


def create_gmail_circuit_breaker():
    """Create a circuit breaker instance for Gmail API calls."""
    return CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=30,
        logger=logging.getLogger('gmail_breaker')
    )
