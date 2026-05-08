from services.redis_manager import redis_manager
from services.exchange_client import exchange_client
from services.risk_engine import risk_engine
from services.execution_monitor import execution_monitor
import logging
import asyncio

logger = logging.getLogger("TradingWorkflow")

class TradingWorkflowService:
    def initiate_trade(self, session_id: str, symbol: str, quantity: float, side: str, token: str = ""):
        """
        Starts a new trade workflow.
        Performs an initial Risk Assessment before asking for order type.
        """
        symbol = symbol.upper()
        side = side.upper()
        
        # Get quote for risk assessment
        quote = exchange_client.get_quote(symbol, quantity, side, token)
        if "error" in quote:
            return f"Market Data Error: {quote['error']}"
        
        price = quote["current_price"]
        balance = quote.get("wallet", {}).get("current_balance", 0.0)
        
        # Risk Assessment
        risk_report = risk_engine.assess_trade(symbol, quantity, price, side, balance)
        
        state = {
            "symbol": symbol,
            "quantity": quantity,
            "side": side,
            "price": price,
            "order_type": None,
            "limit_price": None,
            "risk_report": risk_report,
            "status": "awaiting_order_type"
        }
        redis_manager.set_trade_state(session_id, state)
        
        response = f"**Trade Analysis for {side} {quantity} {symbol}**:\n"
        response += f"- Current Price: ${price:,.2f}\n"
        response += f"- Risk Status: **{risk_report['action']}**\n"
        response += f"- Reason: {risk_report['reason']}\n\n"
        
        if risk_report["action"] == "BLOCK":
            redis_manager.clear_trade_state(session_id)
            return response + "This trade has been blocked for compliance reasons."
            
        return response + "Would you like a **Market** or **Limit** order?"

    def process_order_type(self, session_id: str, order_type: str):
        """Processes the order type and moves to confirmation step."""
        state = redis_manager.get_trade_state(session_id)
        if not state:
            return "No active trade found."

        order_type = order_type.upper()
        state["order_type"] = order_type
        
        if order_type == "LIMIT":
            state["status"] = "awaiting_limit_price"
            redis_manager.set_trade_state(session_id, state)
            return "What should be the **limit price**?"

        # For Market orders, move to confirmation
        state["status"] = "awaiting_confirmation"
        redis_manager.set_trade_state(session_id, state)
        return f"Please confirm your **Market {state['side']}** of {state['quantity']} {state['symbol']} at the current price. Type **'Confirm'** to execute."

    def process_limit_price(self, session_id: str, limit_price: float):
        """Sets limit price and moves to confirmation."""
        state = redis_manager.get_trade_state(session_id)
        if not state or state.get("status") != "awaiting_limit_price":
            return "No pending limit order."

        state["limit_price"] = limit_price
        state["status"] = "awaiting_confirmation"
        redis_manager.set_trade_state(session_id, state)
        return f"Please confirm your **Limit {state['side']}** of {state['quantity']} {state['symbol']} at **${limit_price:,.2f}**. Type **'Confirm'** to execute."

    def confirm_and_execute(self, session_id: str, token: str = ""):
        """The final execution trigger after user confirmation."""
        state = redis_manager.get_trade_state(session_id)
        if not state or state.get("status") != "awaiting_confirmation":
            return "No order waiting for confirmation. Please start over."

        # Execute
        result = exchange_client.place_order(
            state["symbol"], state["quantity"], state["side"], 
            state["order_type"], state["limit_price"], token=token
        )
        
        if "error" in result:
            return f"Execution Failed: {result['error']}"

        # Start live monitoring
        order_id = str(result.get("id", "unknown"))
        asyncio.create_task(execution_monitor.monitor_order(order_id))
        
        redis_manager.clear_trade_state(session_id)
        
        response = f"✅ Order Sent! (ID: {order_id})\n"
        response += f"Status: {result.get('status', 'PENDING')}\n"
        response += "I am now monitoring the live order stream for confirmation..."
        return response

trading_workflow = TradingWorkflowService()
