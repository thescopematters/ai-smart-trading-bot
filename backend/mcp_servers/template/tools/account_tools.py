"""
ACCOUNT TOOLS — Portfolio and trading queries (5 tools)

Source: logic lifted from mcp_servers/mcp_trading_server.py
What changed: DB session uses database_url from config.yaml
              (instead of the global SessionLocal from database.py)
What did NOT change: all exchange_gateway calls, all response formats,
                     User model queries, get_exchange() factory — identical

Tools in this file:
  get_balance      — current paper trading cash balance
  get_quote        — price + fee estimate for a potential trade
  place_order      — place a paper trading order (direct, no workflow)
  get_holdings     — current crypto positions
  get_trade_history — recent filled trades

All tools require user_id. Each tool creates its own DB session per call
(stateless — no session held between calls, aligns with 2026 MCP spec).
"""

import logging
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("AccountTools")

_config: dict = {}
_SessionLocal = None


def set_config(config: dict):
    """Called once at startup by base_mcp_server.py to inject DB config."""
    global _config, _SessionLocal
    _config = config

    database_url = config.get("client", {}).get("database_url", "")
    if database_url:
        engine = create_engine(database_url)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    else:
        # Fall back to the project-wide database.py if no override in config
        try:
            from database import SessionLocal as _fallback
            _SessionLocal = _fallback
            logger.warning("No database_url in config — using project default database.py")
        except ImportError:
            logger.error("No database_url in config and database.py not found.")
            _SessionLocal = None


async def get_balance(user_id: str) -> dict:
    """Get the current paper trading cash balance for a user."""
    if _SessionLocal is None:
        return {"error": "Database not configured."}
    db = _SessionLocal()
    try:
        from database import User
        from exchange_gateway.exchange_router import get_exchange

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found."}

        exchange = get_exchange(db, user)
        quote = exchange.get_quote("BTC", 0, "BUY")
        balance = quote.get("wallet", {}).get("current_balance", 0.0)
        return {
            "balance": balance,
            "currency": "USD",
            "message": f"Your current paper trading balance is **${balance:,.2f} USD**.",
        }
    except Exception as e:
        logger.error(f"get_balance failed: {e}\n{traceback.format_exc()}")
        return {"error": str(e)}
    finally:
        db.close()


async def get_quote(symbol: str, quantity: float, side: str, user_id: str) -> dict:
    """Get a price quote and fee estimate for a potential trade."""
    if _SessionLocal is None:
        return {"error": "Database not configured."}
    db = _SessionLocal()
    try:
        from database import User
        from exchange_gateway.exchange_router import get_exchange

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found."}

        exchange = get_exchange(db, user)
        return exchange.get_quote(symbol, quantity, side)
    except Exception as e:
        logger.error(f"get_quote failed: {e}\n{traceback.format_exc()}")
        return {"error": str(e)}
    finally:
        db.close()


async def place_order(
    symbol: str,
    quantity: float,
    side: str,
    order_type: str,
    limit_price: float = None,
    user_id: str = None,
) -> dict:
    """
    Place a paper trading order directly.
    NOTE: For the managed multi-step workflow use initiate_trade_workflow instead.
    """
    if _SessionLocal is None:
        return {"error": "Database not configured."}
    db = _SessionLocal()
    try:
        from database import User
        from exchange_gateway.exchange_router import get_exchange

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found."}

        exchange = get_exchange(db, user)
        return exchange.place_order(symbol, quantity, side, order_type, limit_price)
    except Exception as e:
        logger.error(f"place_order failed: {e}\n{traceback.format_exc()}")
        return {"error": str(e)}
    finally:
        db.close()


async def get_holdings(user_id: str) -> dict:
    """Get the user's current crypto holdings/positions."""
    if _SessionLocal is None:
        return {"error": "Database not configured."}
    db = _SessionLocal()
    try:
        from database import User
        from exchange_gateway.exchange_router import get_exchange

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found."}

        exchange = get_exchange(db, user)
        return exchange.get_holdings()
    except Exception as e:
        logger.error(f"get_holdings failed: {e}\n{traceback.format_exc()}")
        return {"error": str(e)}
    finally:
        db.close()


async def get_trade_history(user_id: str, limit: int = 20) -> dict:
    """Get the user's recent trade history."""
    if _SessionLocal is None:
        return {"error": "Database not configured."}

    trade_limit = _config.get("limits", {}).get("trade_history_default", limit)
    db = _SessionLocal()
    try:
        from database import User
        from exchange_gateway.exchange_router import get_exchange

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found."}

        exchange = get_exchange(db, user)
        return exchange.get_trade_history(limit=trade_limit)
    except Exception as e:
        logger.error(f"get_trade_history failed: {e}\n{traceback.format_exc()}")
        return {"error": str(e)}
    finally:
        db.close()


TOOL_REGISTRY = {
    "get_balance": get_balance,
    "get_quote": get_quote,
    "place_order": place_order,
    "get_holdings": get_holdings,
    "get_trade_history": get_trade_history,
}
