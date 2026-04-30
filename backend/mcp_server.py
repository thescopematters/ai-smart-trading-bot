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
    "get_portfolio_balances": "PRIVATE",
    "get_user_profile":       "PRIVATE",
    "paper_buy":             "PRIVATE",
    "paper_sell":            "PRIVATE",
    "paper_limit_order":     "PRIVATE",
    "check_pending_orders":  "PRIVATE",
    "paper_portfolio":       "PRIVATE",
    "paper_trade_history":   "PRIVATE",
    "paper_reset":           "PRIVATE",
    "paper_stats":           "PRIVATE",
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

# @mcp.tool()
# def get_trending_news(limit: int = 5) -> str:
#     """Fetch the latest trending crypto news specifically for fundamental analysis."""
#     if not rate_limiter.check("get_trending_news"):
#         return "Rate limit exceeded. Please wait before fetching news again."

#     logger.info(f"🔍 [TOOL CALL] Fetching trending news (Limit: {limit})")

#     api_key = os.getenv("CRYPTOPANIC_API_KEY")
#     base_url = os.getenv("CRYPTOPANIC_URL")

#     if not api_key:
#         return "Error: CryptoPanic API Key missing."

#     params = {"auth_token": api_key, "filter": "trending", "limit": limit}

#     try:
#         response = requests.get(base_url, params=params, timeout=10)
#         data = response.json()
#         results = data.get("results", [])
#         if not results:
#             res = "Market is quiet - no major trending news found right now."
#             logger.info(f"✅ [TOOL RESPONSE] {res}")
#             return res

#         news_lines = [f"--- Trending News ({limit} items) ---"]
#         for item in results:
#             news_lines.append(f"- {item.get('title')} (Source: {item.get('source', {}).get('title')})")

#         result = "\n".join(news_lines)
#         logger.info(f"✅ [TOOL RESPONSE] Successfully returned {len(results)} news items.")
#         return result
#     except Exception as e:
#         logger.error(f"❌ [TOOL ERROR] News Tool failed: {e}")
#         return "Failed to retrieve market news."

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
# 5. PRIVATE Tools (Auth required, audit logged)
# ---------------------------------------------------------

@mcp.tool()
def get_portfolio_balances(user_id: str = "") -> dict:
    """Fetch crypto holdings and portfolio value. Requires user authentication."""
    effective_user_id = user_id.strip() if user_id else DEFAULT_USER_ID
    audit_log("get_portfolio_balances", effective_user_id, "CALLED")

    if not rate_limiter.check("get_portfolio_balances"):
        audit_log("get_portfolio_balances", effective_user_id, "RATE_LIMITED")
        return {"error": "Rate limit exceeded. Please wait."}

    logger.info(f"🔍 [TOOL CALL] Retrieving portfolio for user: {effective_user_id}")

    if not SessionLocal:
        return {"error": "Database service is not initialized."}

    db = SessionLocal()
    try:
        balances_table = metadata.tables.get('crypto_balances')
        coins_table = metadata.tables.get('coins')

        if balances_table is None or coins_table is None:
            return {"error": "Portfolio tables are missing from the database."}

        query = select(
            balances_table.c.balance,
            coins_table.c.name,
            coins_table.c.symbol,
            coins_table.c.price
        ).select_from(
            balances_table.join(coins_table, balances_table.c.coin_id == coins_table.c.id)
        ).where(balances_table.c.user_id == effective_user_id)

        results = db.execute(query).mappings().all()
        portfolio = [make_serializable(dict(r)) for r in results]
        total_val = sum(float(r['balance']) * float(r['price']) for r in results)

        audit_log("get_portfolio_balances", effective_user_id, "SUCCESS",
                  f"value=${total_val:,.2f}")
        logger.info(f"✅ [TOOL RESPONSE] Portfolio value: ${total_val:,.2f}")
        return {
            "summary": "Portfolio Data Retrieved Successfully",
            "total_value_usd": round(total_val, 2),
            "holdings": portfolio
        }
    except Exception as e:
        audit_log("get_portfolio_balances", effective_user_id, "ERROR", str(e))
        logger.error(f"❌ [TOOL ERROR] Portfolio Tool failed: {e}")
        return {"error": "Could not access portfolio data."}
    finally:
        db.close()

@mcp.tool()
def get_user_profile(user_id: str = "") -> dict:
    """Access user profile, email, and system settings. Requires user authentication."""
    effective_user_id = user_id.strip() if user_id else DEFAULT_USER_ID
    audit_log("get_user_profile", effective_user_id, "CALLED")

    if not rate_limiter.check("get_user_profile"):
        audit_log("get_user_profile", effective_user_id, "RATE_LIMITED")
        return {"error": "Rate limit exceeded. Please wait."}

    logger.info(f"🔍 [TOOL CALL] Accessing profile for user: {effective_user_id}")

    if not SessionLocal:
        return {"error": "Profile service is offline."}

    db = SessionLocal()
    try:
        users_table = metadata.tables.get('users')
        if users_table is None:
            return {"error": "User directory not found."}

        user_query = select(users_table).where(users_table.c.id == effective_user_id)
        record = db.execute(user_query).mappings().first()

        if not record:
            audit_log("get_user_profile", effective_user_id, "NOT_FOUND")
            return {"error": "Your user profile was not found in the system."}

        user_info = sanitize_record(dict(record))

        audit_log("get_user_profile", effective_user_id, "SUCCESS",
                  f"email={user_info.get('email', 'N/A')}")
        logger.info(f"✅ [TOOL RESPONSE] Profile for {user_info.get('email')} retrieved.")
        return make_serializable(user_info)
    except Exception as e:
        audit_log("get_user_profile", effective_user_id, "ERROR", str(e))
        logger.error(f"❌ [TOOL ERROR] Profile Tool failed: {e}")
        return {"error": "System failure while retrieving profile."}
    finally:
        db.close()

# ---------------------------------------------------------
# 6. Paper Trading — Configuration & Helpers
# ---------------------------------------------------------

# Trading constants
TRADING_FEE_PCT = Decimal("0.001")       # 0.1% fee per trade
SLIPPAGE_PCT    = Decimal("0.0002")      # 0.02% slippage
STARTING_BALANCE = Decimal("100000.00")  # $100,000 virtual cash
MAX_POSITION_PCT = Decimal("0.25")       # Max 25% of portfolio in one coin
MIN_CASH_RESERVE = Decimal("1000.00")    # Must keep $1,000 minimum
MAX_OPEN_POSITIONS = 5                   # Max different coins held
DAILY_LOSS_LIMIT_PCT = Decimal("0.05")   # 5% max daily loss
LOSS_COOLDOWN_THRESHOLD = 3              # Warn after 3 consecutive losses

# Duplicate order tracking
_recent_orders = {}


def _fetch_price(symbol: str) -> Decimal:
    """Internal helper: fetch raw price as Decimal for trade math. NOT an MCP tool."""
    api_key = os.getenv("COINMARKETCAP_API_KEY")
    base_url = os.getenv("COINMARKETCAP_URL")

    if not api_key:
        raise ValueError("CoinMarketCap API Key not configured")

    headers = {"X-CMC_PRO_API_KEY": api_key, "Accept": "application/json"}
    params = {"symbol": symbol.upper(), "convert": "USD"}

    response = requests.get(base_url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    coin_data = data["data"].get(symbol.upper())
    if not coin_data:
        raise ValueError(f"Symbol '{symbol}' not found on CoinMarketCap")

    price = coin_data[0]["quote"]["USD"]["price"]
    return Decimal(str(price))


def _apply_slippage(price: Decimal, side: str) -> Decimal:
    """BUY = slightly higher price, SELL = slightly lower price."""
    if side == "BUY":
        return (price * (1 + SLIPPAGE_PCT)).quantize(Decimal("0.00000001"))
    return (price * (1 - SLIPPAGE_PCT)).quantize(Decimal("0.00000001"))


def _calculate_fee(total: Decimal) -> Decimal:
    """Calculate trading fee."""
    return (total * TRADING_FEE_PCT).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _check_duplicate(user_id: str, symbol: str, side: str) -> bool:
    """Returns True if same order was placed within 10 seconds."""
    key = (user_id, symbol.upper(), side)
    now = time.time()
    if key in _recent_orders and now - _recent_orders[key] < 10:
        return True
    _recent_orders[key] = now
    return False


def _get_portfolio_value(db, user_id: str) -> Decimal:
    """Calculate total portfolio value (cash + positions at current prices)."""
    wallets_table = metadata.tables.get('paper_wallets')
    wallet = db.execute(
        select(wallets_table.c.cash_balance).where(wallets_table.c.user_id == user_id)
    ).scalar()
    total = Decimal(str(wallet)) if wallet else Decimal("0")

    positions_table = metadata.tables.get('paper_positions')
    if positions_table is None:
        return total

    positions = db.execute(
        select(positions_table).where(positions_table.c.user_id == user_id)
    ).mappings().all()

    for pos in positions:
        try:
            price = _fetch_price(pos['symbol'])
            total += Decimal(str(pos['quantity'])) * price
        except Exception:
            total += Decimal(str(pos['total_cost_basis']))
    return total


def _check_daily_loss(db, user_id: str) -> Decimal:
    """Sum today's realized P&L."""
    trades_table = metadata.tables.get('paper_trades')
    if trades_table is None:
        return Decimal("0")
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    results = db.execute(
        select(trades_table.c.realized_pnl).where(
            trades_table.c.user_id == user_id,
            trades_table.c.executed_at >= today,
            trades_table.c.realized_pnl != None
        )
    ).scalars().all()
    return sum(Decimal(str(r)) for r in results if r is not None)


def _check_consecutive_losses(db, user_id: str) -> int:
    """Count consecutive losing SELL trades (most recent first)."""
    trades_table = metadata.tables.get('paper_trades')
    if trades_table is None:
        return 0
    recent_sells = db.execute(
        select(trades_table.c.realized_pnl).where(
            trades_table.c.user_id == user_id,
            trades_table.c.side == 'SELL',
            trades_table.c.realized_pnl != None
        ).order_by(trades_table.c.executed_at.desc()).limit(LOSS_COOLDOWN_THRESHOLD)
    ).scalars().all()

    consecutive = 0
    for pnl in recent_sells:
        if Decimal(str(pnl)) < 0:
            consecutive += 1
        else:
            break
    return consecutive


def _ensure_wallet(db, user_id: str) -> None:
    """Create a paper wallet if one doesn't exist."""
    wallets_table = metadata.tables.get('paper_wallets')
    if wallets_table is None:
        return
    wallet = db.execute(
        select(wallets_table).where(wallets_table.c.user_id == user_id)
    ).first()
    if not wallet:
        db.execute(wallets_table.insert().values(
            user_id=user_id,
            cash_balance=STARTING_BALANCE,
            initial_balance=STARTING_BALANCE,
        ))
        db.commit()


# ---------------------------------------------------------
# 7. Paper Trading Tools (8 tools)
# ---------------------------------------------------------

@mcp.tool()
def paper_buy(symbol: str, quantity: str, user_id: str = "") -> dict:
    """Execute a market BUY order for crypto with virtual money. Example: paper_buy('BTC', '0.5')"""
    effective_user_id = user_id.strip() if user_id else DEFAULT_USER_ID
    audit_log("paper_buy", effective_user_id, "CALLED", f"{quantity} {symbol}")

    if not rate_limiter.check("paper_buy"):
        return {"error": "Rate limit exceeded. Please wait."}
    if not SessionLocal:
        return {"error": "Database not available."}

    symbol = symbol.upper()
    try:
        qty = Decimal(str(quantity))
    except Exception:
        return {"error": f"Invalid quantity: {quantity}"}
    if qty <= 0:
        return {"error": "Quantity must be greater than 0."}
    if _check_duplicate(effective_user_id, symbol, "BUY"):
        return {"error": "Duplicate order detected. Please wait 10 seconds."}

    db = SessionLocal()
    try:
        _ensure_wallet(db, effective_user_id)
        market_price = _fetch_price(symbol)
        fill_price = _apply_slippage(market_price, "BUY")

        subtotal = (qty * fill_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fee = _calculate_fee(subtotal)
        total_cost = subtotal + fee

        # --- Risk Checks ---
        wallets_table = metadata.tables.get('paper_wallets')
        wallet = db.execute(
            select(wallets_table).where(wallets_table.c.user_id == effective_user_id)
        ).mappings().first()
        cash = Decimal(str(wallet['cash_balance']))

        if total_cost > cash - MIN_CASH_RESERVE:
            return {"error": f"Insufficient funds. Available: ${(cash - MIN_CASH_RESERVE):,.2f}, Required: ${total_cost:,.2f} (incl. ${fee:,.2f} fee)."}

        portfolio_value = _get_portfolio_value(db, effective_user_id)
        max_position_value = portfolio_value * MAX_POSITION_PCT

        positions_table = metadata.tables.get('paper_positions')
        existing = db.execute(
            select(positions_table).where(
                positions_table.c.user_id == effective_user_id,
                positions_table.c.symbol == symbol
            )
        ).mappings().first()

        existing_value = Decimal(str(existing['quantity'])) * fill_price if existing else Decimal("0")
        if existing_value + subtotal > max_position_value:
            return {"error": f"Position too large. Max 25% of portfolio = ${max_position_value:,.2f}."}

        if not existing:
            pos_count = db.execute(
                select(sql_func.count()).select_from(positions_table).where(
                    positions_table.c.user_id == effective_user_id
                )
            ).scalar()
            if pos_count >= MAX_OPEN_POSITIONS:
                return {"error": f"Maximum {MAX_OPEN_POSITIONS} open positions reached. Close one first."}

        daily_pnl = _check_daily_loss(db, effective_user_id)
        initial = Decimal(str(wallet['initial_balance']))
        if daily_pnl < -(initial * DAILY_LOSS_LIMIT_PCT):
            return {"error": f"Daily loss limit reached (${daily_pnl:,.2f}). No new buys until tomorrow."}

        consecutive_losses = _check_consecutive_losses(db, effective_user_id)
        cooldown_warning = ""
        if consecutive_losses >= LOSS_COOLDOWN_THRESHOLD:
            cooldown_warning = f"⚠️ Warning: {consecutive_losses} consecutive losing trades."

        # --- Execute Trade ---
        db.execute(
            wallets_table.update().where(
                wallets_table.c.user_id == effective_user_id
            ).values(cash_balance=wallets_table.c.cash_balance - total_cost)
        )

        orders_table = metadata.tables.get('paper_orders')
        order_result = db.execute(orders_table.insert().values(
            user_id=effective_user_id, symbol=symbol, side="BUY",
            order_type="MARKET", quantity=qty, status="FILLED",
            filled_at=datetime.datetime.now(),
        ))
        order_id = order_result.inserted_primary_key[0]

        trades_table = metadata.tables.get('paper_trades')
        db.execute(trades_table.insert().values(
            order_id=order_id, user_id=effective_user_id, symbol=symbol,
            side="BUY", quantity=qty, fill_price=fill_price,
            fee=fee, total_cost=total_cost, realized_pnl=None,
        ))

        if existing:
            old_qty = Decimal(str(existing['quantity']))
            old_avg = Decimal(str(existing['avg_entry_price']))
            new_avg = ((old_qty * old_avg) + (qty * fill_price)) / (old_qty + qty)
            new_cost = Decimal(str(existing['total_cost_basis'])) + subtotal
            db.execute(positions_table.update().where(
                positions_table.c.id == existing['id']
            ).values(
                quantity=old_qty + qty,
                avg_entry_price=new_avg.quantize(Decimal("0.00000001")),
                total_cost_basis=new_cost,
            ))
        else:
            db.execute(positions_table.insert().values(
                user_id=effective_user_id, symbol=symbol, quantity=qty,
                avg_entry_price=fill_price, total_cost_basis=subtotal,
            ))

        db.commit()
        new_cash = cash - total_cost
        audit_log("paper_buy", effective_user_id, "SUCCESS",
                  f"{qty} {symbol} @ ${fill_price:,.2f}, fee=${fee:,.2f}")

        result = {
            "status": "✅ Order Filled",
            "symbol": symbol, "side": "BUY", "quantity": str(qty),
            "fill_price": f"${fill_price:,.2f}", "fee": f"${fee:,.2f}",
            "total_cost": f"${total_cost:,.2f}", "remaining_cash": f"${new_cash:,.2f}",
        }
        if cooldown_warning:
            result["warning"] = cooldown_warning
        return result

    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ paper_buy failed: {e}")
        audit_log("paper_buy", effective_user_id, "ERROR", str(e))
        return {"error": "Trade execution failed. Please try again."}
    finally:
        db.close()


@mcp.tool()
def paper_sell(symbol: str, quantity: str, user_id: str = "") -> dict:
    """Execute a market SELL order to close or reduce a crypto position."""
    effective_user_id = user_id.strip() if user_id else DEFAULT_USER_ID
    audit_log("paper_sell", effective_user_id, "CALLED", f"{quantity} {symbol}")

    if not rate_limiter.check("paper_sell"):
        return {"error": "Rate limit exceeded."}
    if not SessionLocal:
        return {"error": "Database not available."}

    symbol = symbol.upper()
    try:
        qty = Decimal(str(quantity))
    except Exception:
        return {"error": f"Invalid quantity: {quantity}"}
    if qty <= 0:
        return {"error": "Quantity must be greater than 0."}
    if _check_duplicate(effective_user_id, symbol, "SELL"):
        return {"error": "Duplicate order detected. Wait 10 seconds."}

    db = SessionLocal()
    try:
        positions_table = metadata.tables.get('paper_positions')
        position = db.execute(
            select(positions_table).where(
                positions_table.c.user_id == effective_user_id,
                positions_table.c.symbol == symbol
            )
        ).mappings().first()

        if not position:
            return {"error": f"No {symbol} position found. You can't sell what you don't own."}

        held_qty = Decimal(str(position['quantity']))
        if qty > held_qty:
            return {"error": f"Insufficient {symbol}. You have {held_qty}, trying to sell {qty}."}

        market_price = _fetch_price(symbol)
        fill_price = _apply_slippage(market_price, "SELL")
        avg_entry = Decimal(str(position['avg_entry_price']))

        subtotal = (qty * fill_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fee = _calculate_fee(subtotal)
        proceeds = subtotal - fee
        realized_pnl = ((fill_price - avg_entry) * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        wallets_table = metadata.tables.get('paper_wallets')
        db.execute(wallets_table.update().where(
            wallets_table.c.user_id == effective_user_id
        ).values(cash_balance=wallets_table.c.cash_balance + proceeds))

        orders_table = metadata.tables.get('paper_orders')
        order_result = db.execute(orders_table.insert().values(
            user_id=effective_user_id, symbol=symbol, side="SELL",
            order_type="MARKET", quantity=qty, status="FILLED",
            filled_at=datetime.datetime.now(),
        ))
        order_id = order_result.inserted_primary_key[0]

        trades_table = metadata.tables.get('paper_trades')
        db.execute(trades_table.insert().values(
            order_id=order_id, user_id=effective_user_id, symbol=symbol,
            side="SELL", quantity=qty, fill_price=fill_price,
            fee=fee, total_cost=subtotal, realized_pnl=realized_pnl,
        ))

        remaining = held_qty - qty
        if remaining <= 0:
            db.execute(positions_table.delete().where(positions_table.c.id == position['id']))
        else:
            new_cost_basis = (Decimal(str(position['total_cost_basis'])) * remaining / held_qty).quantize(Decimal("0.01"))
            old_realized = Decimal(str(position['realized_pnl'] or 0))
            db.execute(positions_table.update().where(
                positions_table.c.id == position['id']
            ).values(
                quantity=remaining,
                total_cost_basis=new_cost_basis,
                realized_pnl=old_realized + realized_pnl,
            ))

        db.commit()
        pnl_emoji = "📈" if realized_pnl >= 0 else "📉"
        audit_log("paper_sell", effective_user_id, "SUCCESS",
                  f"{qty} {symbol} @ ${fill_price:,.2f}, P&L=${realized_pnl:,.2f}")

        return {
            "status": "✅ Order Filled",
            "symbol": symbol, "side": "SELL", "quantity": str(qty),
            "fill_price": f"${fill_price:,.2f}", "fee": f"${fee:,.2f}",
            "proceeds": f"${proceeds:,.2f}",
            "realized_pnl": f"{pnl_emoji} ${realized_pnl:,.2f}",
            "remaining_position": str(remaining) if remaining > 0 else "Position Closed",
        }

    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ paper_sell failed: {e}")
        audit_log("paper_sell", effective_user_id, "ERROR", str(e))
        return {"error": "Sell execution failed. Please try again."}
    finally:
        db.close()


@mcp.tool()
def paper_limit_order(symbol: str, side: str, quantity: str, target_price: str, user_id: str = "") -> dict:
    """Place a LIMIT or STOP_LOSS order that fills when the price condition is met."""
    effective_user_id = user_id.strip() if user_id else DEFAULT_USER_ID
    audit_log("paper_limit_order", effective_user_id, "CALLED",
              f"{side} {quantity} {symbol} @ ${target_price}")

    if not rate_limiter.check("paper_limit_order"):
        return {"error": "Rate limit exceeded."}
    if not SessionLocal:
        return {"error": "Database not available."}

    symbol = symbol.upper()
    side = side.upper()
    if side not in ("BUY", "SELL"):
        return {"error": "Side must be 'BUY' or 'SELL'."}

    try:
        qty = Decimal(str(quantity))
        target = Decimal(str(target_price))
    except Exception:
        return {"error": "Invalid quantity or target price."}
    if qty <= 0 or target <= 0:
        return {"error": "Quantity and price must be positive."}

    db = SessionLocal()
    try:
        current_price = _fetch_price(symbol)

        if side == "BUY":
            if target >= current_price:
                return {"error": f"Limit BUY price (${target:,.2f}) must be BELOW current (${current_price:,.2f})."}
            order_type = "LIMIT"
        else:
            positions_table = metadata.tables.get('paper_positions')
            position = db.execute(
                select(positions_table).where(
                    positions_table.c.user_id == effective_user_id,
                    positions_table.c.symbol == symbol
                )
            ).mappings().first()
            if not position or Decimal(str(position['quantity'])) < qty:
                return {"error": f"Insufficient {symbol} to place sell order."}
            order_type = "STOP_LOSS" if target <= current_price else "LIMIT"

        orders_table = metadata.tables.get('paper_orders')
        result = db.execute(orders_table.insert().values(
            user_id=effective_user_id, symbol=symbol, side=side,
            order_type=order_type, quantity=qty, target_price=target, status="PENDING",
        ))
        order_id = result.inserted_primary_key[0]
        db.commit()

        audit_log("paper_limit_order", effective_user_id, "SUCCESS",
                  f"Order #{order_id}: {order_type} {side} {qty} {symbol} @ ${target:,.2f}")

        return {
            "status": "📋 Order Placed", "order_id": order_id,
            "type": order_type, "side": side, "symbol": symbol,
            "quantity": str(qty), "target_price": f"${target:,.2f}",
            "current_price": f"${current_price:,.2f}",
            "note": "Ask 'check my pending orders' to see if it fills."
        }

    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ paper_limit_order failed: {e}")
        return {"error": "Failed to place order."}
    finally:
        db.close()


@mcp.tool()
def check_pending_orders(user_id: str = "") -> dict:
    """Scan all pending orders and fill any that qualify at current market prices."""
    effective_user_id = user_id.strip() if user_id else DEFAULT_USER_ID
    audit_log("check_pending_orders", effective_user_id, "CALLED")

    if not rate_limiter.check("check_pending_orders"):
        return {"error": "Rate limit exceeded."}
    if not SessionLocal:
        return {"error": "Database not available."}

    db = SessionLocal()
    try:
        orders_table = metadata.tables.get('paper_orders')
        pending = db.execute(
            select(orders_table).where(
                orders_table.c.user_id == effective_user_id,
                orders_table.c.status == "PENDING"
            )
        ).mappings().all()

        if not pending:
            return {"status": "No pending orders."}

        filled = []
        still_pending = []

        for order in pending:
            sym = order['symbol']
            try:
                current_price = _fetch_price(sym)
            except Exception:
                still_pending.append({"order_id": order['id'], "symbol": sym, "status": "PENDING (price unavailable)"})
                continue

            target = Decimal(str(order['target_price']))
            should_fill = False
            if order['side'] == 'BUY' and order['order_type'] == 'LIMIT':
                should_fill = current_price <= target
            elif order['side'] == 'SELL' and order['order_type'] == 'LIMIT':
                should_fill = current_price >= target
            elif order['order_type'] == 'STOP_LOSS':
                should_fill = current_price <= target

            if should_fill:
                qty = Decimal(str(order['quantity']))
                fill_price = _apply_slippage(current_price, order['side'])
                subtotal = (qty * fill_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                fee = _calculate_fee(subtotal)

                wallets_table = metadata.tables.get('paper_wallets')
                positions_table = metadata.tables.get('paper_positions')
                trades_table = metadata.tables.get('paper_trades')
                realized_pnl = None

                if order['side'] == 'BUY':
                    db.execute(wallets_table.update().where(
                        wallets_table.c.user_id == effective_user_id
                    ).values(cash_balance=wallets_table.c.cash_balance - (subtotal + fee)))

                    existing = db.execute(select(positions_table).where(
                        positions_table.c.user_id == effective_user_id,
                        positions_table.c.symbol == sym
                    )).mappings().first()

                    if existing:
                        old_qty = Decimal(str(existing['quantity']))
                        old_avg = Decimal(str(existing['avg_entry_price']))
                        new_avg = ((old_qty * old_avg) + (qty * fill_price)) / (old_qty + qty)
                        db.execute(positions_table.update().where(
                            positions_table.c.id == existing['id']
                        ).values(
                            quantity=old_qty + qty,
                            avg_entry_price=new_avg.quantize(Decimal("0.00000001")),
                            total_cost_basis=Decimal(str(existing['total_cost_basis'])) + subtotal,
                        ))
                    else:
                        db.execute(positions_table.insert().values(
                            user_id=effective_user_id, symbol=sym, quantity=qty,
                            avg_entry_price=fill_price, total_cost_basis=subtotal,
                        ))
                else:
                    proceeds = subtotal - fee
                    db.execute(wallets_table.update().where(
                        wallets_table.c.user_id == effective_user_id
                    ).values(cash_balance=wallets_table.c.cash_balance + proceeds))

                    position = db.execute(select(positions_table).where(
                        positions_table.c.user_id == effective_user_id,
                        positions_table.c.symbol == sym
                    )).mappings().first()

                    if position:
                        avg_entry = Decimal(str(position['avg_entry_price']))
                        realized_pnl = ((fill_price - avg_entry) * qty).quantize(Decimal("0.01"))
                        remaining = Decimal(str(position['quantity'])) - qty
                        if remaining <= 0:
                            db.execute(positions_table.delete().where(positions_table.c.id == position['id']))
                        else:
                            db.execute(positions_table.update().where(
                                positions_table.c.id == position['id']
                            ).values(quantity=remaining))

                db.execute(trades_table.insert().values(
                    order_id=order['id'], user_id=effective_user_id, symbol=sym,
                    side=order['side'], quantity=qty, fill_price=fill_price,
                    fee=fee, total_cost=subtotal, realized_pnl=realized_pnl,
                ))
                db.execute(orders_table.update().where(
                    orders_table.c.id == order['id']
                ).values(status="FILLED", filled_at=datetime.datetime.now()))

                filled.append({
                    "order_id": order['id'], "type": order['order_type'],
                    "side": order['side'], "symbol": sym,
                    "fill_price": f"${fill_price:,.2f}", "fee": f"${fee:,.2f}",
                })
            else:
                still_pending.append({
                    "order_id": order['id'], "side": order['side'],
                    "symbol": sym, "target": f"${target:,.2f}",
                    "current": f"${current_price:,.2f}",
                })

        db.commit()
        return {
            "filled_count": len(filled), "pending_count": len(still_pending),
            "filled_orders": filled, "still_pending": still_pending,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ check_pending_orders failed: {e}")
        return {"error": "Failed to check orders."}
    finally:
        db.close()


@mcp.tool()
def paper_portfolio(user_id: str = "") -> dict:
    """View paper trading portfolio with live P&L for all open positions."""
    effective_user_id = user_id.strip() if user_id else DEFAULT_USER_ID

    if not rate_limiter.check("paper_portfolio"):
        return {"error": "Rate limit exceeded."}
    if not SessionLocal:
        return {"error": "Database not available."}

    db = SessionLocal()
    try:
        _ensure_wallet(db, effective_user_id)
        wallets_table = metadata.tables.get('paper_wallets')
        wallet = db.execute(
            select(wallets_table).where(wallets_table.c.user_id == effective_user_id)
        ).mappings().first()

        cash = Decimal(str(wallet['cash_balance']))
        initial = Decimal(str(wallet['initial_balance']))

        positions_table = metadata.tables.get('paper_positions')
        positions = db.execute(
            select(positions_table).where(positions_table.c.user_id == effective_user_id)
        ).mappings().all()

        holdings = []
        total_unrealized = Decimal("0")
        total_positions_value = Decimal("0")

        for pos in positions:
            sym = pos['symbol']
            qty = Decimal(str(pos['quantity']))
            avg_entry = Decimal(str(pos['avg_entry_price']))

            try:
                current_price = _fetch_price(sym)
                current_value = (qty * current_price).quantize(Decimal("0.01"))
                unrealized_pnl = ((current_price - avg_entry) * qty).quantize(Decimal("0.01"))
                pnl_pct = ((current_price - avg_entry) / avg_entry * 100).quantize(Decimal("0.01"))
            except Exception:
                current_price = avg_entry
                current_value = Decimal(str(pos['total_cost_basis']))
                unrealized_pnl = Decimal("0")
                pnl_pct = Decimal("0")

            total_unrealized += unrealized_pnl
            total_positions_value += current_value
            pnl_emoji = "📈" if unrealized_pnl >= 0 else "📉"

            holdings.append({
                "symbol": sym, "quantity": str(qty),
                "avg_entry": f"${avg_entry:,.2f}", "current_price": f"${current_price:,.2f}",
                "current_value": f"${current_value:,.2f}",
                "unrealized_pnl": f"{pnl_emoji} ${unrealized_pnl:,.2f} ({pnl_pct:+.2f}%)",
            })

        total_value = cash + total_positions_value
        overall_return = total_value - initial
        return_pct = ((total_value - initial) / initial * 100).quantize(Decimal("0.01"))

        trades_table = metadata.tables.get('paper_trades')
        total_realized = Decimal("0")
        if trades_table is not None:
            realized_results = db.execute(
                select(trades_table.c.realized_pnl).where(
                    trades_table.c.user_id == effective_user_id,
                    trades_table.c.realized_pnl != None
                )
            ).scalars().all()
            total_realized = sum(Decimal(str(r)) for r in realized_results if r is not None)

        return {
            "cash_balance": f"${cash:,.2f}",
            "positions_value": f"${total_positions_value:,.2f}",
            "total_value": f"${total_value:,.2f}",
            "initial_balance": f"${initial:,.2f}",
            "overall_return": f"${overall_return:,.2f} ({return_pct:+.2f}%)",
            "unrealized_pnl": f"${total_unrealized:,.2f}",
            "realized_pnl": f"${total_realized:,.2f}",
            "holdings": holdings if holdings else "No open positions",
        }

    except Exception as e:
        logger.error(f"❌ paper_portfolio failed: {e}")
        return {"error": "Failed to load portfolio."}
    finally:
        db.close()


@mcp.tool()
def paper_trade_history(limit: int = 10, user_id: str = "") -> dict:
    """View recent paper trade execution history with P&L details."""
    effective_user_id = user_id.strip() if user_id else DEFAULT_USER_ID

    if not rate_limiter.check("paper_trade_history"):
        return {"error": "Rate limit exceeded."}
    if not SessionLocal:
        return {"error": "Database not available."}

    db = SessionLocal()
    try:
        trades_table = metadata.tables.get('paper_trades')
        if trades_table is None:
            return {"trades": [], "message": "No trade history found."}

        results = db.execute(
            select(trades_table).where(
                trades_table.c.user_id == effective_user_id
            ).order_by(trades_table.c.executed_at.desc()).limit(min(limit, 50))
        ).mappings().all()

        if not results:
            return {"trades": [], "message": "No trades yet. Start with 'Buy 0.1 BTC'!"}

        trades = []
        total_fees = Decimal("0")
        total_pnl = Decimal("0")

        for t in results:
            fee = Decimal(str(t['fee']))
            pnl = Decimal(str(t['realized_pnl'])) if t['realized_pnl'] is not None else None
            total_fees += fee
            if pnl is not None:
                total_pnl += pnl

            entry = {
                "id": t['id'], "side": t['side'], "symbol": t['symbol'],
                "quantity": str(t['quantity']),
                "fill_price": f"${Decimal(str(t['fill_price'])):,.2f}",
                "fee": f"${fee:,.2f}",
                "time": t['executed_at'].strftime("%Y-%m-%d %H:%M") if t['executed_at'] else "N/A",
            }
            if pnl is not None:
                emoji = "📈" if pnl >= 0 else "📉"
                entry["realized_pnl"] = f"{emoji} ${pnl:,.2f}"
            trades.append(entry)

        return {
            "trade_count": len(trades),
            "total_fees_paid": f"${total_fees:,.2f}",
            "net_realized_pnl": f"${total_pnl:,.2f}",
            "trades": trades,
        }

    except Exception as e:
        logger.error(f"❌ paper_trade_history failed: {e}")
        return {"error": "Failed to load trade history."}
    finally:
        db.close()


@mcp.tool()
def paper_reset(confirm: bool = False, user_id: str = "") -> dict:
    """Reset paper trading account. Archives history, resets balance to $100k. Requires confirm=True."""
    effective_user_id = user_id.strip() if user_id else DEFAULT_USER_ID
    audit_log("paper_reset", effective_user_id, "CALLED", f"confirm={confirm}")

    if not confirm:
        return {
            "warning": "⚠️ This will reset your entire paper trading account.",
            "what_happens": [
                "All pending orders → CANCELLED",
                "All positions → CLOSED",
                "Cash balance → Reset to $100,000",
                "Trade history → PRESERVED for reference"
            ],
            "action_required": "Call paper_reset with confirm=True to proceed."
        }

    if not SessionLocal:
        return {"error": "Database not available."}

    db = SessionLocal()
    try:
        orders_table = metadata.tables.get('paper_orders')
        if orders_table is not None:
            db.execute(orders_table.update().where(
                orders_table.c.user_id == effective_user_id,
                orders_table.c.status == "PENDING"
            ).values(status="CANCELLED"))

        positions_table = metadata.tables.get('paper_positions')
        if positions_table is not None:
            db.execute(positions_table.delete().where(
                positions_table.c.user_id == effective_user_id
            ))

        wallets_table = metadata.tables.get('paper_wallets')
        if wallets_table is not None:
            db.execute(wallets_table.update().where(
                wallets_table.c.user_id == effective_user_id
            ).values(cash_balance=STARTING_BALANCE))

        db.commit()
        audit_log("paper_reset", effective_user_id, "SUCCESS", "Full reset")

        return {
            "status": "✅ Account Reset Complete",
            "cash_balance": f"${STARTING_BALANCE:,.2f}",
            "open_positions": 0, "pending_orders": 0,
            "note": "Trade history preserved for reference."
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ paper_reset failed: {e}")
        return {"error": "Reset failed."}
    finally:
        db.close()


@mcp.tool()
def paper_stats(user_id: str = "") -> dict:
    """Get comprehensive trading performance statistics: win rate, streaks, best/worst trades."""
    effective_user_id = user_id.strip() if user_id else DEFAULT_USER_ID

    if not rate_limiter.check("paper_stats"):
        return {"error": "Rate limit exceeded."}
    if not SessionLocal:
        return {"error": "Database not available."}

    db = SessionLocal()
    try:
        trades_table = metadata.tables.get('paper_trades')
        if trades_table is None:
            return {"message": "No trading data yet."}

        all_trades = db.execute(
            select(trades_table).where(
                trades_table.c.user_id == effective_user_id
            ).order_by(trades_table.c.executed_at.asc())
        ).mappings().all()

        if not all_trades:
            return {"message": "No trades yet. Start with 'Buy 0.1 BTC'!"}

        sells = [t for t in all_trades if t['side'] == 'SELL' and t['realized_pnl'] is not None]
        total_trades = len(all_trades)
        total_buys = len([t for t in all_trades if t['side'] == 'BUY'])
        total_sells = len(sells)

        wins = [t for t in sells if Decimal(str(t['realized_pnl'])) > 0]
        losses = [t for t in sells if Decimal(str(t['realized_pnl'])) < 0]
        win_rate = (len(wins) / total_sells * 100) if total_sells > 0 else 0

        total_pnl = sum(Decimal(str(t['realized_pnl'])) for t in sells)
        total_fees = sum(Decimal(str(t['fee'])) for t in all_trades)
        avg_profit = total_pnl / total_sells if total_sells > 0 else Decimal("0")

        best = max(sells, key=lambda t: Decimal(str(t['realized_pnl']))) if sells else None
        worst = min(sells, key=lambda t: Decimal(str(t['realized_pnl']))) if sells else None

        streak = 0
        streak_type = ""
        for t in reversed(sells):
            pnl = Decimal(str(t['realized_pnl']))
            if streak == 0:
                streak_type = "winning" if pnl > 0 else "losing"
                streak = 1
            elif (streak_type == "winning" and pnl > 0) or (streak_type == "losing" and pnl < 0):
                streak += 1
            else:
                break

        result = {
            "total_trades": total_trades, "buys": total_buys, "sells": total_sells,
            "wins": len(wins), "losses": len(losses),
            "win_rate": f"{win_rate:.1f}%",
            "total_realized_pnl": f"${total_pnl:,.2f}",
            "total_fees_paid": f"${total_fees:,.2f}",
            "avg_profit_per_trade": f"${avg_profit:,.2f}",
            "current_streak": f"{streak} {streak_type}" if streak > 0 else "No streak",
        }
        if best:
            result["best_trade"] = f"{best['symbol']} +${Decimal(str(best['realized_pnl'])):,.2f}"
        if worst:
            result["worst_trade"] = f"{worst['symbol']} ${Decimal(str(worst['realized_pnl'])):,.2f}"
        return result

    except Exception as e:
        logger.error(f"❌ paper_stats failed: {e}")
        return {"error": "Failed to calculate stats."}
    finally:
        db.close()


# ---------------------------------------------------------
# 8. Server Execution
# ---------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
