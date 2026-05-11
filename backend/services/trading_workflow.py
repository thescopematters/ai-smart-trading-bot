from schemas import TradeState, WorkflowState
from services.workflow_orchestrator import orchestrator
from services.execution_service import execution_service
from services.exchange_client import exchange_client
from services.risk_engine import risk_engine
from services.execution_monitor import execution_monitor
from services.audit_logger import audit_logger
from services.task_registry import task_registry
from exceptions import RiskViolationError, InvalidWorkflowTransitionError
from typing import Any
import logging
import asyncio

logger = logging.getLogger("TradingWorkflow")

class TradingWorkflowService:
    def initiate_trade(self, session_id: str, user_id: str, symbol: str, quantity: float, side: str, token: str = ""):
        """
        Starts a new trade workflow.
        Performs an initial Risk Assessment before asking for order type.
        """
        from database import SessionLocal, User
        
        symbol = symbol.upper()
        side = side.upper()
        price = 0.0
        risk_report = None
        
        # Get quote for risk assessment
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return "Error: User context missing. Please login again."
                
            quote = exchange_client.get_quote(db, user, symbol, quantity, side, token)
            if "error" in quote:
                return f"Market Data Error: {quote['error']}"
            
            price = quote["current_price"]
            balance = quote.get("wallet", {}).get("current_balance", 0.0)
            
            # Risk Assessment
            risk_report = risk_engine.assess_trade(symbol, quantity, price, side, balance)
            
            state = TradeState(
                session_id=session_id,
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                side=side,
                price=price,
                risk_report=risk_report.dict()
            )
            
            orchestrator.initiate_workflow(state)
            audit_logger.log_event("INITIATE_TRADE", session_id, user_id, state.workflow_id, payload=state.dict())
        
        # Variables are now safely accessible outside the 'with' block
        response = f"**Trade Analysis for {side} {quantity} {symbol}**:\n"
        response += f"- Current Price: ${price:,.2f}\n"
        response += f"- Risk Status: **{risk_report.action}**\n"
        response += f"- Reason: {risk_report.reason}\n\n"
        
        if risk_report.action == "BLOCK":
            orchestrator.transition(session_id, WorkflowState.FAILED)
            return response + "This trade has been blocked for compliance reasons."
            
        orchestrator.transition(session_id, WorkflowState.RISK_CHECKED)
        orchestrator.transition(session_id, WorkflowState.AWAITING_ORDER_TYPE)
        
        return response + "Would you like a **Market** or **Limit** order?"

    def process_order_type(self, session_id: str, order_type: str):
        """Processes the order type and moves to confirmation step."""
        state = orchestrator.get_active_workflow(session_id)
        if not state:
            return "No active trade found."

        order_type = order_type.upper()
        
        if order_type == "LIMIT":
            orchestrator.transition(session_id, WorkflowState.AWAITING_LIMIT_PRICE, {"order_type": "LIMIT"})
            return "What should be the **limit price**?"

        # For Market orders, move to confirmation
        orchestrator.transition(session_id, WorkflowState.AWAITING_CONFIRMATION, {"order_type": "MARKET"})
        return f"Please confirm your **Market {state.side}** of {state.quantity} {state.symbol} at the current price. Type **'Confirm'** to execute."

    def process_limit_price(self, session_id: str, limit_price: float):
        """Sets limit price and moves to confirmation."""
        orchestrator.transition(session_id, WorkflowState.AWAITING_CONFIRMATION, {"limit_price": limit_price})
        state = orchestrator.get_active_workflow(session_id)
        if not state:
            return "Trade state lost. Please start a new trade."
        return f"Please confirm your **Limit {state.side}** of {state.quantity} {state.symbol} at **${limit_price:,.2f}**. Type **'Confirm'** to execute."

    def confirm_and_execute(self, session_id: str, db: Any, user: Any, token: str = ""):
        """The final execution trigger after user confirmation."""
        state = orchestrator.get_active_workflow(session_id)
        if not state or state.status != WorkflowState.AWAITING_CONFIRMATION:
            return "No order waiting for confirmation. Please start over."

        orchestrator.transition(session_id, WorkflowState.EXECUTING)
        
        # Execute via service (Idempotent)
        result = execution_service.execute_trade(db, user, state, state.confirmation_token, token)
        
        if result.status == "FAILED":
            orchestrator.transition(session_id, WorkflowState.FAILED)
            audit_logger.log_event("EXECUTION_FAILED", session_id, state.user_id, state.workflow_id, result=result.dict())
            return f"Execution Failed: {result.error}"

        # Start live monitoring as a supervised task
        order_id = result.order_id
        task_registry.register(
            f"monitor_order_{order_id}", 
            execution_monitor.monitor_order(order_id),
            on_failure=lambda e: audit_logger.log_event("MONITOR_FAILED", session_id, state.user_id, state.workflow_id, result={"error": str(e)})
        )
        
        if result.status == "FILLED":
            orchestrator.transition(session_id, WorkflowState.FILLED)
        else:
            # Still pending (e.g. Limit order)
            pass 

        audit_logger.log_event("EXECUTION_SUCCESS", session_id, state.user_id, state.workflow_id, result=result.dict())
        
        response = f"✅ Order Sent! (ID: {order_id})\n"
        response += f"Status: {result.status}\n"
        response += "I am now monitoring the live order stream for confirmation..."
        return response

trading_workflow = TradingWorkflowService()
