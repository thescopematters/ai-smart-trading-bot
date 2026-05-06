"""
MCP CRYPTO SERVER (Production-Hardened + Paper Trading)
-------------------------------------------------------
Built on: 2026-04-24
Updated:  2026-04-27 — Added 8 Paper Trading tools

Architecture:
  This server runs as a SEPARATE SUBPROCESS.
  The google-adk MCPToolset connects to it via STDIO pipes.

Security Features:
  1. AUTH:           User-specific tools accept user_id
  2. RATE LIMITS:    30 calls/min per tool
  3. ACCESS CONTROL: Tools classified as PUBLIC or PRIVATE
  4. AUDIT LOG:      All sensitive operations logged
  5. SANITIZATION:   Passwords/tokens never returned to AI

Paper Trading Features:
  - Market BUY/SELL with fees (0.1%) and slippage (0.02%)
  - LIMIT and STOP-LOSS pending orders
  - Weighted average entry price tracking
  - Risk management (position limits, daily loss cap, cooldown)
  - Portfolio P&L with live price updates
  - Full trade history and performance analytics
"""

from fastmcp import FastMCP
import os
import time
import requests
import logging
import json
import datetime
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.sql import func as sql_func

# ---------------------------------------------------------
# 1. Initialization
# ---------------------------------------------------------
load_dotenv()

mcp = FastMCP("Crypto-Insights")

# Setup Logging to both Console and File
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPServer")

# Add a file handler so we can see logs even if the console hides child processes
file_handler = logging.FileHandler("mcp_server.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)
logger.info("🚀 MCP Server starting up...")

# Database connection
try:
    from database import SessionLocal, metadata
except ImportError:
    logger.error("database.py not found. DB tools inactive.")
    SessionLocal = None
    metadata = None

# RAG knowledge base
try:
    import rag_service
except ImportError:
    logger.warning("rag_service.py not found.")
    rag_service = None

# Fallback user ID — used ONLY when no user_id is provided
DEFAULT_USER_ID = "eceee63a-c1fa-48de-aa15-b75fcfd79809"

# ---------------------------------------------------------
# 2. Security Infrastructure
# ---------------------------------------------------------

class RateLimiter:
    def __init__(self, max_calls_per_minute: int = 30):
        self.max_calls = max_calls_per_minute
        self._calls = defaultdict(list)

    def check(self, tool_name: str) -> bool:
        now = time.time()
        self._calls[tool_name] = [t for t in self._calls[tool_name] if now - t < 60]
        if len(self._calls[tool_name]) >= self.max_calls:
            return False
        self._calls[tool_name].append(now)
        return True

rate_limiter = RateLimiter(max_calls_per_minute=30)

TOOL_ACCESS = {
    "get_live_price":        "PUBLIC",
    "get_trending_news":     "PUBLIC",
    "get_blockchain_stats":  "PUBLIC",
    "query_knowledge_base":  "PUBLIC",
}

audit_logger = logging.getLogger("AuditLog")

def audit_log(tool_name: str, user_id: str, status: str, detail: str = ""):
    audit_logger.info(
        f"🔒 [AUDIT] tool={tool_name} | user={user_id} | status={status} | {detail}"
    )

SENSITIVE_FIELDS = frozenset([
    'password', 'token', 'email_verification_token',
    'reset_password_token', 'api_key', 'secret_key'
])

def sanitize_record(record: dict) -> dict:
    return {k: v for k, v in record.items() if k not in SENSITIVE_FIELDS}

# ---------------------------------------------------------
# 3. Helper Utilities
# ---------------------------------------------------------
def make_serializable(obj):
    """Convert SQL/Decimal types into plain JSON for the AI."""
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
# 4. PUBLIC Tools (No auth required)
# ---------------------------------------------------------

@mcp.tool()
def get_live_price(symbol: str, currency: str = "USD") -> str:
    """Fetch real-time market prices for any crypto coin."""
    if not rate_limiter.check("get_live_price"):
        return "Rate limit exceeded. Please wait a moment before checking prices again."

    logger.info(f"🔍 [TOOL CALL] Fetching live price for: {symbol}")

    api_key = os.getenv("COINMARKETCAP_API_KEY")
    base_url = os.getenv("COINMARKETCAP_URL")

    if not api_key:
        return "Error: CoinMarketCap API Key not found in .env"

    headers = {"X-CMC_PRO_API_KEY": api_key, "Accept": "application/json"}
    params = {"symbol": symbol.upper(), "convert": currency.upper()}

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        coin_data = data["data"].get(symbol.upper())
        if not coin_data:
            err = f"Error: The symbol '{symbol}' was not found on CoinMarketCap."
            logger.warning(f"⚠️ [TOOL ERROR] {err}")
            return err

        quote = coin_data[0]["quote"][currency.upper()]
        price = quote["price"]
        change = quote["percent_change_24h"]

        result = f"Current {symbol.upper()} price: ${price:,.2f} ({change:+.2f}% 24h change)."
        logger.info(f"✅ [TOOL RESPONSE] Returned price data for {symbol}")
        return result
    except Exception as e:
        logger.error(f"❌ [TOOL ERROR] Price Tool failed: {e}")
        return f"Unable to fetch price for {symbol} at this time."

@mcp.tool()
def get_trending_news(limit: int = 5) -> str:
    """Fetch the latest trending crypto news specifically for fundamental analysis."""
    if not rate_limiter.check("get_trending_news"):
        return "Rate limit exceeded. Please wait before fetching news again."

    logger.info(f"🔍 [TOOL CALL] Fetching trending news (Limit: {limit})")

    api_key = os.getenv("CRYPTOPANIC_API_KEY")
    base_url = os.getenv("CRYPTOPANIC_URL")

    if not api_key:
        return "Error: CryptoPanic API Key missing."

    params = {"auth_token": api_key, "filter": "trending", "limit": limit}

    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        results = data.get("results", [])
        if not results:
            res = "Market is quiet - no major trending news found right now."
            logger.info(f"✅ [TOOL RESPONSE] {res}")
            return res

        news_lines = [f"--- Trending News ({limit} items) ---"]
        for item in results:
            news_lines.append(f"- {item.get('title')} (Source: {item.get('source', {}).get('title')})")

        result = "\n".join(news_lines)
        logger.info(f"✅ [TOOL RESPONSE] Successfully returned {len(results)} news items.")
        return result
    except Exception as e:
        logger.error(f"❌ [TOOL ERROR] News Tool failed: {e}")
        return "Failed to retrieve market news."

@mcp.tool()
def get_blockchain_stats(chain: str = "bitcoin") -> dict:
    """Fetch live blockchain network health (hashrate, blocks, transactions)."""
    if not rate_limiter.check("get_blockchain_stats"):
        return {"error": "Rate limit exceeded. Please wait before checking stats again."}

    logger.info(f"🔍 [TOOL CALL] Fetching chain stats for: {chain}")
    chain = chain.lower()
    if chain == "eth": chain = "ethereum"
    if chain == "btc": chain = "bitcoin"

    base_url = os.getenv("BLOCKCHAIR_BASE_URL", "https://api.blockchair.com")
    url = f"{base_url}/{chain}/stats"

    try:
        response = requests.get(url, timeout=10)
        data = response.json().get("data", {})
        if not data:
            logger.warning(f"⚠️ [TOOL ERROR] No data for chain: {chain}")
            return {"error": f"No data found for the '{chain}' network."}

        logger.info(f"✅ [TOOL RESPONSE] Returning stats for {chain}")
        return {
            "network": chain.capitalize(),
            "last_block": data.get("blocks"),
            "daily_transactions": data.get("transactions_24h"),
            "current_price_usd": data.get("market_price_usd"),
            "daily_hashrate": data.get("hashrate_24h"),
        }
    except Exception as e:
        logger.error(f"❌ [TOOL ERROR] Chain Stats failed: {e}")
        return {"error": "Blockchain network data is currently unreachable."}

@mcp.tool()
def query_knowledge_base(query: str) -> str:
    """Search internal PDFs and documents for high-quality project research."""
    if not rate_limiter.check("query_knowledge_base"):
        return "Rate limit exceeded. Please wait before searching again."

    logger.info(f"🔍 [TOOL CALL] Querying knowledge base: {query}")
    if not rag_service:
        return "Our internal documentation repository is currently offline."
    try:
        context = rag_service.search_knowledge_base(query)
        res = context if context else "No local documents match your search query."
        logger.info(f"✅ [TOOL RESPONSE] Found {len(res)} chars of context.")
        return res
    except Exception as e:
        logger.error(f"❌ [TOOL ERROR] Knowledge Base failed: {e}")
        return "Error searching the knowledge repository."

# ---------------------------------------------------------
# 8. Server Execution
# ---------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
