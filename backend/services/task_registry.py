import asyncio
import logging
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger("TaskRegistry")

class TaskRegistry:
    """
    Local Process Task Registry. Not durable across restarts.
    Migration Path: Celery/Arq for distributed durability.
    """
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}

    def register(self, name: str, coro, on_failure: Optional[Callable] = None) -> asyncio.Task:
        """
        Runs a coroutine as a supervised task.
        """
        if name in self.tasks and not self.tasks[name].done():
            logger.warning(f"Task {name} is already running. Cancelling old one.")
            self.tasks[name].cancel()

        task = asyncio.create_task(coro)
        self.tasks[name] = task

        def _done_callback(t: asyncio.Task):
            try:
                t.result() # Raises exception if task failed
                logger.debug(f"Task {name} completed successfully.")
            except asyncio.CancelledError:
                logger.info(f"Task {name} was cancelled.")
            except Exception as e:
                logger.error(f"Task {name} failed: {e}", exc_info=True)
                if on_failure:
                    try:
                        on_failure(e)
                    except Exception as fe:
                        logger.error(f"Task failure callback failed: {fe}")
            finally:
                if self.tasks.get(name) == t:
                    del self.tasks[name]

        task.add_done_callback(_done_callback)
        return task

    def cancel(self, name: str):
        if name in self.tasks:
            self.tasks[name].cancel()

    def cancel_all(self):
        logger.info(f"Cancelling all {len(self.tasks)} managed tasks...")
        for task in self.tasks.values():
            task.cancel()
        self.tasks.clear()

    def list_active(self) -> Dict[str, str]:
        return {name: "RUNNING" for name in self.tasks}

task_registry = TaskRegistry()
