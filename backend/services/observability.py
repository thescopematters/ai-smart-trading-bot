import time
import logging
from typing import Dict, Any

logger = logging.getLogger("Observability")

class Metrics:
    """
    Hook for recording system performance and health metrics.
    Prometheus/OpenTelemetry-compatible structure.
    """
    def __init__(self, window_size: int = 20):
        self.api_latencies = []
        self.llm_latencies = []
        self.window_size = window_size
        self.counters: Dict[str, int] = {}

    def record_latency(self, operation: str, duration_ms: float):
        """Records the time taken for an operation."""
        if operation == "api_request":
            self.api_latencies.append(duration_ms)
            if len(self.api_latencies) > self.window_size:
                self.api_latencies.pop(0)
        elif operation == "llm_response":
            self.llm_latencies.append(duration_ms)
            if len(self.llm_latencies) > self.window_size:
                self.llm_latencies.pop(0)
        
        logger.debug(f"[METRIC] Latency | {operation}: {duration_ms:.2f}ms")

    def get_summary(self) -> Dict[str, Any]:
        """Returns summarized metrics for the dashboard."""
        avg_api = sum(self.api_latencies) / len(self.api_latencies) if self.api_latencies else 0
        avg_llm = sum(self.llm_latencies) / len(self.llm_latencies) if self.llm_latencies else 0
        
        # Calculate percentages for the UI bars (mocking logical thresholds)
        # 1. API Latency: 500ms = 100% (lower is better, but bar shows usage)
        api_percent = min(100, int((avg_api / 500) * 100)) if avg_api > 0 else 5
        
        # 2. LLM Response: 5s = 100%
        llm_percent = min(100, int((avg_llm / 5000) * 100)) if avg_llm > 0 else 10
        
        # 3. Vector DB: Check real sync status
        from rag_service import get_sync_status
        sync_data = get_sync_status()
        sync_percent = sync_data["percent"]
        
        return {
            "api_latency": f"{int(avg_api)}ms" if avg_api > 0 else "---",
            "api_percent": api_percent,
            "llm_response": f"{avg_llm/1000:.1f}s" if avg_llm > 0 else "---",
            "llm_percent": llm_percent,
            "vector_sync": f"{sync_percent}%",
            "vector_percent": int(sync_percent)
        }

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
