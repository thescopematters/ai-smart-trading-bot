import logging
import asyncio
import random

logger = logging.getLogger("ExecutionMonitor")

class ExecutionMonitor:
    def __init__(self):
        # In a real app, this would connect to a WebSocket stream
        self.active_monitors = {}

    async def monitor_order(self, order_id: str):
        """
        Simulates monitoring an order stream for status updates.
        """
        logger.info(f"Started monitoring order {order_id}...")
        
        # Simulate stream updates
        statuses = ["RECEIVED", "PENDING", "PROCESSING", "FILLED"]
        
        for status in statuses:
            await asyncio.sleep(1.5) # Wait for "stream" update
            logger.info(f"Order {order_id} status update: {status}")
            self.active_monitors[order_id] = status
            
            if status == "FILLED":
                break
        
        logger.info(f"Order {order_id} reached terminal state.")

    def get_live_status(self, order_id: str) -> str:
        """Returns the latest status from the stream."""
        return self.active_monitors.get(order_id, "UNKNOWN")

execution_monitor = ExecutionMonitor()
