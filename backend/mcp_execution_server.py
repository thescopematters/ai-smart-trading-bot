from fastmcp import FastMCP
from services.trading_workflow import trading_workflow
from services.market_analyst import market_analyst
from services.execution_monitor import execution_monitor
import logging
import os

mcp = FastMCP("Crypto-Execution")
logger = logging.getLogger("MCPExecutionServer")

@mcp.tool()
def get_market_analysis(symbol: str) -> dict:
    """
    Market Analyst Sub-Agent: Get price, trend, and sentiment for a coin.
    """
    return market_analyst.get_market_insight(symbol)

@mcp.tool()
def initiate_trade_workflow(symbol: str, quantity: float, side: str, session_id: str) -> str:
    """
    Risk & Compliance Sub-Agent: Validate trade and start workflow.
    This performs risk assessment and asks for order type.
    """
    try:
        return trading_workflow.initiate_trade(session_id, symbol, quantity, side)
    except Exception as e:
        return f"Error initiating trade: {str(e)}"

@mcp.tool()
def provide_order_type(order_type: str, session_id: str) -> str:
    """
    Workflow Tool: Provide order type (Market/Limit).
    """
    return trading_workflow.process_order_type(session_id, order_type)

@mcp.tool()
def provide_limit_price(limit_price: float, session_id: str) -> str:
    """
    Workflow Tool: Provide limit price.
    """
    return trading_workflow.process_limit_price(session_id, limit_price)

@mcp.tool()
def confirm_trade_execution(session_id: str) -> str:
    """
    Execution Agent: Final trigger to place the order after user confirms.
    """
    return trading_workflow.confirm_and_execute(session_id)

@mcp.tool()
def get_live_order_status(order_id: str) -> str:
    """
    Execution Monitor: Check the live stream status for an order.
    """
    return execution_monitor.get_live_status(order_id)

if __name__ == "__main__":
    mcp.run()
