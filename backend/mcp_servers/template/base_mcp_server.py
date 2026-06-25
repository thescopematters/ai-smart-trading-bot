"""
BASE MCP SERVER — Client-Agnostic Template
------------------------------------------
Entry point for any client deployment. This file:

  1. Loads config.yaml (the harness — which client, which tools, which keys)
  2. Sets up shared infrastructure: rate limiter, audit log, sanitization
  3. Injects config into each tool module (data, account, action)
  4. Registers ONLY the tools listed in config tools_enabled
  5. Exposes /config/status — shows which tools are active at runtime
  6. Runs via STDIO (local dev / agent.py) or HTTP (production client deploy)

To deploy for a new client:
  1. Copy config.yaml → config_client_b.yaml
  2. Fill in client name, database_url, api_keys
  3. Set tools_enabled to only what that client is licensed for
  4. Run: python base_mcp_server.py --config config_client_b.yaml

Nothing else changes. Same code. Different harness.

Stateless by design (2026 MCP spec):
  - No server-side session state. Each tool call is independent.
  - Trade workflow state lives in Redis (services/redis_manager.py), not here.
  - _meta field available via FastMCP Context for request tracing.
"""

import os
import sys
import time
import logging
import argparse
from collections import defaultdict
from decimal import Decimal
import datetime

import yaml
from fastmcp import FastMCP

# Ensure backend/ is importable (parent of mcp_servers/template/)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ---------------------------------------------------------
# 1. CLI argument — which config file to load
# ---------------------------------------------------------
parser = argparse.ArgumentParser(description="Client-Agnostic MCP Server")
parser.add_argument(
    "--config",
    default=os.path.join(os.path.dirname(__file__), "config.yaml"),
    help="Path to client config.yaml (default: config.yaml next to this file)",
)
# parse_known_args so FastMCP can also receive its own args without conflict
args, _ = parser.parse_known_args()

# ---------------------------------------------------------
# 2. Load config
# ---------------------------------------------------------
with open(args.config, "r") as f:
    config = yaml.safe_load(f)

client_name = config.get("client", {}).get("name", "unknown")
tools_enabled: list = config.get("tools_enabled", [])

# ---------------------------------------------------------
# 3. Logging
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(f"MCP:{client_name}")
logger.info(f"Starting MCP server for client: {client_name}")
logger.info(f"Tools enabled: {tools_enabled}")

# ---------------------------------------------------------
# 4. Shared Infrastructure (moved from mcp_server.py)
# ---------------------------------------------------------

class RateLimiter:
    """Sliding window rate limiter — 30 calls/min per tool (configurable)."""
    def __init__(self, max_calls_per_minute: int = 30):
        self.max_calls = max_calls_per_minute
        self._calls: dict = defaultdict(list)

    def check(self, tool_name: str) -> bool:
        now = time.time()
        self._calls[tool_name] = [t for t in self._calls[tool_name] if now - t < 60]
        if len(self._calls[tool_name]) >= self.max_calls:
            return False
        self._calls[tool_name].append(now)
        return True


rate_limit_per_min = config.get("limits", {}).get("rate_limit_per_minute", 30)
rate_limiter = RateLimiter(max_calls_per_minute=rate_limit_per_min)

SENSITIVE_FIELDS = frozenset([
    "password", "token", "email_verification_token",
    "reset_password_token", "api_key", "secret_key",
])

audit_logger = logging.getLogger(f"Audit:{client_name}")

def audit_log(tool_name: str, user_id: str, status: str, detail: str = ""):
    audit_logger.info(
        f"[AUDIT] client={client_name} tool={tool_name} user={user_id} status={status} {detail}"
    )

def sanitize_record(record: dict) -> dict:
    return {k: v for k, v in record.items() if k not in SENSITIVE_FIELDS}

def make_serializable(obj):
    """Convert SQLAlchemy / Decimal / datetime types to plain JSON."""
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(v) for v in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    return obj

# ---------------------------------------------------------
# 5. Optional service imports (same optional pattern as original servers)
# ---------------------------------------------------------
try:
    import rag_service
except ImportError:
    logger.warning("rag_service not found — query_knowledge_base will be inactive.")
    rag_service = None

try:
    from services.market_analyst import market_analyst
except ImportError:
    logger.warning("market_analyst not found — get_market_analysis will be inactive.")
    market_analyst = None

# DB SessionLocal — built from config database_url if provided
try:
    db_url = config.get("client", {}).get("database_url", "")
    if db_url:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        _engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        logger.info(f"DB connected via config database_url")
    else:
        from database import SessionLocal
        logger.info("No database_url in config — using project default database.py")
except ImportError:
    logger.error("database.py not found and no database_url in config.")
    SessionLocal = None

# ---------------------------------------------------------
# 6. Inject config into tool modules
# ---------------------------------------------------------
from tools import data_tools, account_tools, action_tools

data_tools.set_config(config, rate_limiter, rag_service, market_analyst)
account_tools.set_config(config)
action_tools.set_config(SessionLocal)

# ---------------------------------------------------------
# 7. Create FastMCP instance and register enabled tools
# ---------------------------------------------------------
mcp = FastMCP(f"Crypto-MCP:{client_name}")

ALL_TOOLS = {
    **data_tools.TOOL_REGISTRY,
    **account_tools.TOOL_REGISTRY,
    **action_tools.TOOL_REGISTRY,
}

registered = []
skipped = []

for tool_name in tools_enabled:
    if tool_name in ALL_TOOLS:
        mcp.tool()(ALL_TOOLS[tool_name])
        registered.append(tool_name)
    else:
        logger.warning(f"tools_enabled listed '{tool_name}' but no matching function found.")

for tool_name in ALL_TOOLS:
    if tool_name not in tools_enabled:
        skipped.append(tool_name)

logger.info(f"Registered {len(registered)} tools: {registered}")
logger.info(f"Disabled {len(skipped)} tools: {skipped}")

# ---------------------------------------------------------
# 8. /config/status endpoint
# Ajitpal's harness visibility — which tools are active at runtime.
# Clients / ops / Surinder can hit this to verify the right harness is loaded.
# ---------------------------------------------------------
@mcp.resource("config://status")
def config_status() -> dict:
    """Returns the active harness state for this client deployment."""
    return {
        "client": client_name,
        "tools_enabled": registered,
        "tools_disabled": skipped,
        "rate_limit_per_minute": rate_limit_per_min,
        "risk": config.get("risk", {}),
    }

# ---------------------------------------------------------
# 9. Run
#
# STDIO  — local development, works with existing agent.py unchanged
# HTTP   — production client deployment (one line change)
#
# To switch to HTTP for a client:
#   mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
# ---------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
