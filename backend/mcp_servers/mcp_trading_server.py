from fastmcp import FastMCP
import os
import sys
import logging

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from sqlalchemy.orm import Session
from database import SessionLocal, User
from exchange_gateway.exchange_router import get_exchange

mcp = FastMCP("Crypto-Trading")
logger = logging.getLogger("MCPTradingServer")

@mcp.tool()
def get_balance(user_id: str) -> dict:
    """
    Get the current paper trading cash balance for a user.
    """
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found."}
            
            exchange = get_exchange(db, user)
            # We use a dummy quote to get the wallet info
            quote = exchange.get_quote("BTC", 0, "BUY")
            logger.info(f"Quote result: {quote}")
            balance = quote.get("wallet", {}).get("current_balance", 0.0)
            
            return {
                "balance": balance,
                "currency": "USD",
                "message": f"Your current paper trading balance is **${balance:,.2f} USD**."
            }
    except Exception as e:
        # logger.error(f"Error in get_balance: {e}")
        logger.error(f"Error in get_balance: {e}", exc_info=True)
        return {"error": str(e)}

@mcp.tool()
def get_quote(symbol: str, quantity: float, side: str, user_id: str) -> dict:
    """
    Get a price quote and fee estimate for a potential trade.
    """
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found."}
            
            exchange = get_exchange(db, user)
            return exchange.get_quote(symbol, quantity, side)
    except Exception as e:
        logger.error(f"Error in get_quote: {e}")
        return {"error": str(e)}

@mcp.tool()
def place_order(symbol: str, quantity: float, side: str, order_type: str, 
                limit_price: float = None, user_id: str = None) -> dict:
    """
    Place a paper trading order. NOTE: This tool is for direct placement.
    For the managed workflow, use the Execution Agent tools.
    """
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found."}
            
            exchange = get_exchange(db, user)
            return exchange.place_order(symbol, quantity, side, order_type, limit_price)
    except Exception as e:
        logger.error(f"Error in place_order: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_holdings(user_id: str) -> dict:
    """
    Get the user's current crypto holdings/positions.
    """
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found."}
            
            exchange = get_exchange(db, user)
            return exchange.get_holdings()
    except Exception as e:
        logger.error(f"Error in get_holdings: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_trade_history(user_id: str, limit: int = 20) -> dict:
    """
    Get the user's recent trade history.
    """
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found."}
            
            exchange = get_exchange(db, user)
            return exchange.get_trade_history(limit=limit)
    except Exception as e:
        logger.error(f"Error in get_trade_history: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()
