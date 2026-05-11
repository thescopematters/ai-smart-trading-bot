import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Any, Dict

logger = logging.getLogger("Resilience")

class CircuitBreaker:
    """
    Prevents cascading failures by stopping calls to a failing service.
    States: CLOSED (normal), OPEN (blocking), HALF_OPEN (testing)
    """
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    def __call__(self, func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info(f"Circuit {self.name} HALF_OPEN: Attempting recovery.")
                else:
                    logger.warning(f"Circuit {self.name} is OPEN. Blocking call.")
                    return {"error": f"Service {self.name} is temporarily unavailable (Circuit Breaker)."}

            try:
                result = func(*args, **kwargs)
                if isinstance(result, dict) and "error" in result:
                    self._on_failure()
                else:
                    self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e
        return wrapper

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit {self.name} OPENED after {self.failures} failures.")

    def _on_success(self):
        if self.state == "HALF_OPEN":
            logger.info(f"Circuit {self.name} CLOSED: Service recovered.")
        self.failures = 0
        self.state = "CLOSED"

def with_retry(max_retries: int = 3, backoff: float = 2.0):
    """Decorator for synchronous retry with exponential backoff."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(1, max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, dict) and "error" in result:
                        # Business error, maybe don't retry? 
                        # For now, let's assume if it's in a dict, it's a handled error.
                        return result
                    return result
                except Exception as e:
                    last_err = e
                    if attempt < max_retries:
                        sleep_time = backoff ** attempt
                        logger.warning(f"Retry {attempt}/{max_retries} for {func.__name__} after {sleep_time}s: {e}")
                        time.sleep(sleep_time)
            raise last_err
        return wrapper
    return decorator

def with_timeout(seconds: int = 10):
    """Decorator for hard timeout on synchronous calls (via thread)."""
    # Note: Implementing true sync timeout in Python is tricky without signals/threads.
    # For now, this is a placeholder or uses simple timing.
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs) # Placeholder
        return wrapper
    return decorator
