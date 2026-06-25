"""
DATA TOOLS — Market data and knowledge base (5 tools)

Source: logic lifted from mcp_servers/mcp_server.py
What changed: API keys now injected from config.yaml at startup
              (not read from os.getenv inside each function)
What did NOT change: all external API calls, all service imports,
                     all response formats — identical to the original

Tools in this file:
  get_live_price       — CoinMarketCap live price
  get_trending_news    — CryptoPanic trending headlines
  get_blockchain_stats — Blockchair network health
  get_market_analysis  — Binance OHLCV → strategy_engine signal
  query_knowledge_base — ChromaDB semantic search over ./data docs

These are PUBLIC tools — no user_id needed.
"""

import requests
import logging

logger = logging.getLogger("DataTools")

# Injected by base_mcp_server.py at startup via set_config()
_config: dict = {}
_rate_limiter = None
_rag_service = None
_market_analyst = None


def set_config(config: dict, rate_limiter, rag_service, market_analyst):
    """Called once at startup by base_mcp_server.py to inject dependencies."""
    global _config, _rate_limiter, _rag_service, _market_analyst
    _config = config
    _rate_limiter = rate_limiter
    _rag_service = rag_service
    _market_analyst = market_analyst


def get_live_price(symbol: str, currency: str = "USD") -> str:
    """Fetch real-time market prices for any crypto coin."""
    if not _rate_limiter.check("get_live_price"):
        return "Rate limit exceeded. Please wait a moment before checking prices again."

    api_key = _config.get("api_keys", {}).get("coinmarketcap", "")
    base_url = _config.get("api_keys", {}).get("coinmarketcap_url", "")

    if not api_key:
        return "Error: CoinMarketCap API key not configured for this client."

    headers = {"X-CMC_PRO_API_KEY": api_key, "Accept": "application/json"}
    params = {"symbol": symbol.upper(), "convert": currency.upper()}

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        coin_data = data["data"].get(symbol.upper())
        if not coin_data:
            return f"Error: The symbol '{symbol}' was not found on CoinMarketCap."

        quote = coin_data[0]["quote"][currency.upper()]
        price = quote["price"]
        change = quote["percent_change_24h"]
        return f"Current {symbol.upper()} price: ${price:,.2f} ({change:+.2f}% 24h change)."
    except Exception as e:
        logger.error(f"get_live_price failed: {e}")
        return f"Unable to fetch price for {symbol} at this time."


def get_trending_news(limit: int = 5) -> str:
    """Fetch the latest trending crypto news for fundamental analysis."""
    if not _rate_limiter.check("get_trending_news"):
        return "Rate limit exceeded. Please wait before fetching news again."

    api_key = _config.get("api_keys", {}).get("cryptopanic", "")
    base_url = _config.get("api_keys", {}).get("cryptopanic_url", "")

    if not api_key:
        return "Error: CryptoPanic API key not configured for this client."

    params = {"auth_token": api_key, "filter": "trending", "limit": limit}

    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        results = data.get("results", [])
        if not results:
            return "Market is quiet — no major trending news found right now."

        lines = [f"--- Trending News ({limit} items) ---"]
        for item in results:
            lines.append(f"- {item.get('title')} (Source: {item.get('source', {}).get('title')})")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_trending_news failed: {e}")
        return "Failed to retrieve market news."


def get_blockchain_stats(chain: str = "bitcoin") -> dict:
    """Fetch live blockchain network health (hashrate, blocks, transactions)."""
    if not _rate_limiter.check("get_blockchain_stats"):
        return {"error": "Rate limit exceeded. Please wait before checking stats again."}

    chain = chain.lower()
    if chain == "eth":
        chain = "ethereum"
    if chain == "btc":
        chain = "bitcoin"

    base_url = _config.get("api_keys", {}).get("blockchair_url", "https://api.blockchair.com")
    url = f"{base_url}/{chain}/stats"

    try:
        response = requests.get(url, timeout=10)
        data = response.json().get("data", {})
        if not data:
            return {"error": f"No data found for the '{chain}' network."}

        return {
            "network": chain.capitalize(),
            "last_block": data.get("blocks"),
            "daily_transactions": data.get("transactions_24h"),
            "current_price_usd": data.get("market_price_usd"),
            "daily_hashrate": data.get("hashrate_24h"),
        }
    except Exception as e:
        logger.error(f"get_blockchain_stats failed: {e}")
        return {"error": "Blockchain network data is currently unreachable."}


def get_market_analysis(symbol: str) -> dict:
    """Get professional price, trend, and sentiment analysis for a coin."""
    if _market_analyst is None:
        return {"error": "Market analyst service unavailable."}
    return _market_analyst.get_market_insight(symbol)


def query_knowledge_base(query: str) -> str:
    """Search internal PDFs and documents for high-quality project research."""
    if not _rate_limiter.check("query_knowledge_base"):
        return "Rate limit exceeded. Please wait before searching again."

    if _rag_service is None:
        return "Our internal documentation repository is currently offline."
    try:
        context = _rag_service.search_knowledge_base(query)
        return context if context else "No local documents match your search query."
    except Exception as e:
        logger.error(f"query_knowledge_base failed: {e}")
        return "Error searching the knowledge repository."


# Registry — base_mcp_server.py reads this to register enabled tools
TOOL_REGISTRY = {
    "get_live_price": get_live_price,
    "get_trending_news": get_trending_news,
    "get_blockchain_stats": get_blockchain_stats,
    "get_market_analysis": get_market_analysis,
    "query_knowledge_base": query_knowledge_base,
}
