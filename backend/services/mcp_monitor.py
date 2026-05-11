import os
import logging
import time
from typing import Dict, Any

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = logging.getLogger("MCPMonitor")

class MCPProcessMonitor:
    """
    Instruments MCP subprocess lifecycle.
    """
    def __init__(self):
        self.active_processes: Dict[int, Dict[str, Any]] = {}

    def log_spawn(self, server_name: str, pid: int):
        self.active_processes[pid] = {
            "name": server_name,
            "start_time": time.time(),
            "pid": pid
        }
        logger.info(f"MCP Spawned: {server_name} (PID: {pid})")

    def log_terminate(self, pid: int):
        if pid in self.active_processes:
            proc_info = self.active_processes.pop(pid)
            duration = time.time() - proc_info["start_time"]
            logger.info(f"MCP Terminated: {proc_info['name']} (PID: {pid}) | Duration: {duration:.2f}s")

    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "active_count": len(self.active_processes),
            "processes": []
        }
        if not HAS_PSUTIL:
            return stats
            
        for pid, info in self.active_processes.items():
            try:
                proc = psutil.Process(pid)
                mem = proc.memory_info().rss / (1024 * 1024) # MB
                stats["processes"].append({
                    "name": info["name"],
                    "pid": pid,
                    "memory_mb": round(mem, 2),
                    "duration_s": round(time.time() - info["start_time"], 2)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return stats

mcp_monitor = MCPProcessMonitor()
