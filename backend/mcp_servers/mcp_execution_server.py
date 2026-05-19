from fastmcp import FastMCP
import os
import sys
import logging
import traceback

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, User
from services.trading_workflow import trading_workflow
from services.execution_monitor import execution_monitor

mcp = FastMCP("Crypto-Execution")
logger = logging.getLogger("MCPExecutionServer")

@mcp.tool()
async def initiate_trade_workflow(symbol: str, quantity: float, side: str, session_id: str, user_id: str) -> str:
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
        logger.info(f"initiate_trade_workflow called: symbol={symbol}, qty={quantity}, side={side}, session={session_id}, user={user_id}")
        result = await trading_workflow.initiate_trade(session_id, user_id, symbol, quantity, side)
        logger.info(f"initiate_trade_workflow result: {result[:100]}...")
        return result
    except Exception as e:
        logger.error(f"Error in initiate_trade_workflow: {e}\n{traceback.format_exc()}")
        return f"Error initiating trade: {str(e)}"

@mcp.tool()
async def provide_order_type(order_type: str, session_id: str) -> str:
    """
    Provide the order type (MARKET or LIMIT) for the active trade.
    Args:
        order_type: Either MARKET or LIMIT.
        session_id: The chat session ID.
    """
    try:
        logger.info(f"provide_order_type called: order_type={order_type}, session={session_id}")
        result = await trading_workflow.process_order_type(session_id, order_type)
        logger.info(f"provide_order_type result: {result[:100]}...")
        return result
    except Exception as e:
        logger.error(f"Error in provide_order_type: {e}\n{traceback.format_exc()}")
        return f"Error setting order type: {str(e)}"

@mcp.tool()
async def provide_limit_price(limit_price: float, session_id: str) -> str:
    """
    Provide the limit price for a LIMIT order.
    Args:
        limit_price: The target limit price in USD.
        session_id: The chat session ID.
    """
    try:
        logger.info(f"provide_limit_price called: price={limit_price}, session={session_id}")
        result = await trading_workflow.process_limit_price(session_id, limit_price)
        return result
    except Exception as e:
        logger.error(f"Error in provide_limit_price: {e}\n{traceback.format_exc()}")
        return f"Error setting limit price: {str(e)}"

@mcp.tool()
async def confirm_trade_execution(session_id: str, user_id: str) -> str:
    """
    Final trigger to execute the trade after user confirmation.
    Args:
        session_id: The chat session ID from the system context.
        user_id: The user ID from the system context.
    """
    try:
        logger.info(f"confirm_trade_execution called: session={session_id}, user={user_id}")
        # Create a fresh DB session for the entire execution lifecycle
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return "Error: User not found. Please ensure you are logged in."
            
            result = await trading_workflow.confirm_and_execute(session_id, db, user)
            logger.info(f"confirm_trade_execution result: {result[:100]}...")
            return result
        except Exception as inner_e:
            db.rollback()
            raise inner_e
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in confirm_trade_execution: {e}\n{traceback.format_exc()}")
        return f"Execution error: {str(e)}"

@mcp.tool()
def get_live_order_status(order_id: str) -> str:
    """
    Check the current status of a live order.
    Args:
        order_id: The order ID to check.
    """
    return execution_monitor.get_live_status(order_id)

if __name__ == "__main__":
    mcp.run()
