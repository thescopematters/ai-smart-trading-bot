from fastmcp import FastMCP
import os
import sys
import logging

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
    """
    try:
        return await trading_workflow.initiate_trade(session_id, user_id, symbol, quantity, side)
    except Exception as e:
        logger.error(f"Error in initiate_trade_workflow: {e}")
        return f"Error initiating trade: {str(e)}"

@mcp.tool()
async def provide_order_type(order_type: str, session_id: str) -> str:
    """
    Provide the order type (MARKET or LIMIT) for the active trade.
    """
    return await trading_workflow.process_order_type(session_id, order_type)

@mcp.tool()
async def provide_limit_price(limit_price: float, session_id: str) -> str:
    """
    Provide the limit price for a LIMIT order.
    """
    return await trading_workflow.process_limit_price(session_id, limit_price)

@mcp.tool()
async def confirm_trade_execution(session_id: str, user_id: str) -> str:
    """
    Final trigger to execute the trade after user confirmation.
    """
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return "Error: User not found."
            return await trading_workflow.confirm_and_execute(session_id, db, user)
    except Exception as e:
        logger.error(f"Error in confirm_trade_execution: {e}")
        return f"Execution error: {str(e)}"

@mcp.tool()
def get_live_order_status(order_id: str) -> str:
    """
    Check the current status of a live order.
    """
    return execution_monitor.get_live_status(order_id)

if __name__ == "__main__":
    mcp.run()
