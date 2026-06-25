"""
ACTION TOOLS — Trade execution workflow (5 tools)

Source: logic lifted from mcp_servers/mcp_execution_server.py
What changed: nothing in the logic — these tools delegate 100% to
              services/trading_workflow.py and services/execution_monitor.py
              which remain completely untouched.
What did NOT change: all service imports, all arguments, all responses.

Tools in this file:
  initiate_trade_workflow  — start workflow: risk check → ask order type
  provide_order_type       — MARKET or LIMIT selection
  provide_limit_price      — set price for LIMIT orders
  confirm_trade_execution  — final trigger: execute the trade
  get_live_order_status    — check current order status

Trade state (INITIATED → RISK_CHECKED → AWAITING_ORDER_TYPE →
AWAITING_CONFIRMATION → EXECUTING → FILLED) lives in Redis,
not in this server process — stateless per the 2026 MCP spec.

Require both user_id and session_id (execution tools are user+session scoped).
"""

import logging
import traceback

logger = logging.getLogger("ActionTools")

_SessionLocal = None


def set_config(SessionLocal):
    """Called once at startup by base_mcp_server.py."""
    global _SessionLocal
    _SessionLocal = SessionLocal


async def initiate_trade_workflow(
    symbol: str, quantity: float, side: str, session_id: str, user_id: str
) -> str:
    """
    Initiate a new trade workflow. Performs risk assessment and asks for order type.
    Args:
        symbol: The crypto symbol to trade (e.g. BTC, ETH).
        quantity: The amount to buy or sell.
        side: BUY or SELL.
        session_id: The chat session ID from the system context.
        user_id: The user ID from the system context.
    """
    try:
        from services.trading_workflow import trading_workflow
        result = await trading_workflow.initiate_trade(session_id, user_id, symbol, quantity, side)
        return result
    except Exception as e:
        logger.error(f"initiate_trade_workflow failed: {e}\n{traceback.format_exc()}")
        return f"Error initiating trade: {str(e)}"


async def provide_order_type(order_type: str, session_id: str) -> str:
    """
    Provide the order type (MARKET or LIMIT) for the active trade.
    Args:
        order_type: Either MARKET or LIMIT.
        session_id: The chat session ID.
    """
    try:
        from services.trading_workflow import trading_workflow
        result = await trading_workflow.process_order_type(session_id, order_type)
        return result
    except Exception as e:
        logger.error(f"provide_order_type failed: {e}\n{traceback.format_exc()}")
        return f"Error setting order type: {str(e)}"


async def provide_limit_price(limit_price: float, session_id: str) -> str:
    """
    Provide the limit price for a LIMIT order.
    Args:
        limit_price: The target limit price in USD.
        session_id: The chat session ID.
    """
    try:
        from services.trading_workflow import trading_workflow
        result = await trading_workflow.process_limit_price(session_id, limit_price)
        return result
    except Exception as e:
        logger.error(f"provide_limit_price failed: {e}\n{traceback.format_exc()}")
        return f"Error setting limit price: {str(e)}"


async def confirm_trade_execution(session_id: str, user_id: str) -> str:
    """
    Final trigger to execute the trade after user confirmation.
    Args:
        session_id: The chat session ID from the system context.
        user_id: The user ID from the system context.
    """
    if _SessionLocal is None:
        return "Error: Database not configured."
    db = _SessionLocal()
    try:
        from database import User
        from services.trading_workflow import trading_workflow

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "Error: User not found. Please ensure you are logged in."

        result = await trading_workflow.confirm_and_execute(session_id, db, user)
        return result
    except Exception as e:
        db.rollback()
        logger.error(f"confirm_trade_execution failed: {e}\n{traceback.format_exc()}")
        return f"Execution error: {str(e)}"
    finally:
        db.close()


def get_live_order_status(order_id: str) -> str:
    """
    Check the current status of a live order.
    Args:
        order_id: The order ID to check.
    """
    try:
        from services.execution_monitor import execution_monitor
        return execution_monitor.get_live_status(order_id)
    except Exception as e:
        logger.error(f"get_live_order_status failed: {e}")
        return f"Error fetching order status: {str(e)}"


TOOL_REGISTRY = {
    "initiate_trade_workflow": initiate_trade_workflow,
    "provide_order_type": provide_order_type,
    "provide_limit_price": provide_limit_price,
    "confirm_trade_execution": confirm_trade_execution,
    "get_live_order_status": get_live_order_status,
}
