"""
Comprehensive error handling and retry logic for RAG pipeline.

Features:
- Custom exception hierarchy
- Retry decorators with exponential backoff
- Circuit breaker pattern for external services
- Graceful degradation strategies
"""

from __future__ import annotations

import functools
import logging
import time
from enum import Enum
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ── Custom Exceptions ─────────────────────────────────────────────────────────


class RAGException(Exception):
    """Base exception for all RAG pipeline errors."""
    pass


class RetrievalError(RAGException):
    """Error during retrieval phase."""
    pass


class GenerationError(RAGException):
    """Error during generation phase."""
    pass


class EmbeddingError(RAGException):
    """Error during embedding computation."""
    pass


class CacheError(RAGException):
    """Error in caching layer."""
    pass


class ExternalServiceError(RAGException):
    """Error communicating with external service (LLM API, etc.)."""
    pass


class RateLimitError(ExternalServiceError):
    """Rate limit exceeded on external service."""
    pass


class TimeoutError(RAGException):
    """Operation exceeded timeout."""
    pass


# ── Retry Logic ───────────────────────────────────────────────────────────────


class RetryStrategy(Enum):
    """Retry strategy options."""
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"            # Fixed delay
    IMMEDIATE = "immediate"      # No delay


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    logger_name: str | None = None,
) -> Callable:
    """
    Decorator for retrying functions with configurable backoff.
    
    Args:
        max_attempts: Maximum number of attempts (including initial)
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        strategy: Retry delay strategy
        exceptions: Tuple of exceptions to retry on
        logger_name: Optional logger name for logging retries
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 0
            last_exception = None
            log = logging.getLogger(logger_name) if logger_name else logger
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    attempt += 1
                    last_exception = exc
                    
                    if attempt >= max_attempts:
                        log.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, max_attempts, exc
                        )
                        break
                    
                    # Calculate delay
                    if strategy == RetryStrategy.EXPONENTIAL:
                        delay = min(
                            initial_delay * (exponential_base ** (attempt - 1)),
                            max_delay
                        )
                    elif strategy == RetryStrategy.LINEAR:
                        delay = initial_delay
                    else:  # IMMEDIATE
                        delay = 0.0
                    
                    log.warning(
                        "%s failed (attempt %d/%d): %s. Retrying in %.1fs...",
                        func.__name__, attempt, max_attempts, exc, delay
                    )
                    
                    if delay > 0:
                        time.sleep(delay)
            
            # All attempts exhausted
            raise last_exception  # type: ignore[misc]
        
        return wrapper
    return decorator


# ── Circuit Breaker ───────────────────────────────────────────────────────────


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.
    
    Prevents cascading failures by "opening" the circuit after
    a threshold of failures, giving the service time to recover.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying half-open
            success_threshold: Successes needed to close circuit from half-open
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            ExternalServiceError: If circuit is open
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise ExternalServiceError(
                    f"Circuit breaker OPEN for {func.__name__}. "
                    f"Service unavailable for {self.recovery_timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise exc
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try half-open state."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker CLOSED (service recovered)")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker re-OPENED (service still failing)")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                "Circuit breaker OPENED after %d failures",
                self.failure_count
            )
    
    def reset(self) -> None:
        """Manually reset circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually RESET")


# ── Graceful Degradation ──────────────────────────────────────────────────────


class DegradationStrategy:
    """
    Strategies for graceful degradation when components fail.
    """
    
    @staticmethod
    def fallback_to_cache(
        primary_func: Callable[..., T],
        cache_func: Callable[..., T | None],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Try primary function, fall back to cache on failure.
        
        Args:
            primary_func: Primary function to call
            cache_func: Cache lookup function
            *args: Arguments for both functions
            **kwargs: Keyword arguments
            
        Returns:
            Result from primary or cache
            
        Raises:
            Exception: If both primary and cache fail
        """
        try:
            return primary_func(*args, **kwargs)
        except Exception as exc:
            logger.warning(
                "Primary function %s failed: %s. Trying cache...",
                primary_func.__name__, exc
            )
            
            cached = cache_func(*args, **kwargs)
            if cached is not None:
                logger.info("Serving stale result from cache")
                return cached
            
            logger.error("Cache miss. No fallback available.")
            raise exc
    
    @staticmethod
    def fallback_to_simpler_model(
        primary_func: Callable[..., T],
        fallback_func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Try primary function, fall back to simpler alternative.
        
        Args:
            primary_func: Primary (complex) function
            fallback_func: Fallback (simpler) function
            *args: Arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result from primary or fallback
        """
        try:
            return primary_func(*args, **kwargs)
        except Exception as exc:
            logger.warning(
                "Primary function %s failed: %s. Using fallback...",
                primary_func.__name__, exc
            )
            return fallback_func(*args, **kwargs)


# ── Error Context Manager ─────────────────────────────────────────────────────


class ErrorContext:
    """
    Context manager for error handling with logging and cleanup.
    """
    
    def __init__(
        self,
        operation: str,
        reraise: bool = True,
        cleanup_func: Callable | None = None,
    ):
        """
        Initialize error context.
        
        Args:
            operation: Description of operation for logging
            reraise: Whether to reraise exceptions
            cleanup_func: Optional cleanup function to call on error
        """
        self.operation = operation
        self.reraise = reraise
        self.cleanup_func = cleanup_func
        self.start_time: float = 0.0
    
    def __enter__(self) -> ErrorContext:
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        elapsed = time.time() - self.start_time
        
        if exc_type is not None:
            logger.error(
                "Operation '%s' failed after %.2fs: %s: %s",
                self.operation, elapsed, exc_type.__name__, exc_val
            )
            
            # Run cleanup if provided
            if self.cleanup_func:
                try:
                    self.cleanup_func()
                except Exception as cleanup_exc:
                    logger.error(
                        "Cleanup failed after error: %s", cleanup_exc
                    )
            
            # Return False to reraise, True to suppress
            return not self.reraise
        
        logger.debug("Operation '%s' completed in %.2fs", self.operation, elapsed)
        return False


# ── Timeout Decorator ─────────────────────────────────────────────────────────


def timeout_after(seconds: float) -> Callable:
    """
    Decorator to enforce timeout on function execution.
    
    Note: This is a simple implementation. For production, consider
    using threading or multiprocessing for true timeout enforcement.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            
            if elapsed > seconds:
                logger.warning(
                    "%s exceeded timeout (%.1fs > %.1fs)",
                    func.__name__, elapsed, seconds
                )
            
            return result
        return wrapper
    return decorator
