import time
import logging
from typing import Dict, Any

logger = logging.getLogger("Observability")

class Metrics:
    """
    Hook for recording system performance and health metrics.
    Prometheus/OpenTelemetry-compatible structure.
    """
    def __init__(self):
        # In a real app, this would use prometheus_client or opentelemetry SDK
        self.counters: Dict[str, int] = {}
        self.histograms: Dict[str, list] = {}

    def record_latency(self, operation: str, duration_ms: float):
        """Records the time taken for an operation."""
        logger.debug(f"[METRIC] Latency | {operation}: {duration_ms:.2f}ms")
        # Placeholder for histogram accumulation

    def increment_counter(self, name: str, labels: Dict[str, str] = None):
        """Increments a named counter."""
        self.counters[name] = self.counters.get(name, 0) + 1
        label_str = f"| {labels}" if labels else ""
        logger.debug(f"[METRIC] Counter | {name}{label_str}")

    def record_gauge(self, name: str, value: float):
        """Records a point-in-time value."""
        logger.debug(f"[METRIC] Gauge | {name}: {value}")

metrics = Metrics()

def instrument_sync(operation_name: str):
    """Decorator for timing synchronous functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = (time.perf_counter() - start) * 1000
                metrics.record_latency(operation_name, duration)
        return wrapper
    return decorator

def instrument_async(operation_name: str):
    """Decorator for timing asynchronous functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = (time.perf_counter() - start) * 1000
                metrics.record_latency(operation_name, duration)
        return wrapper
    return decorator
