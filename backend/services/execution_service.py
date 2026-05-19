import logging
import uuid
import traceback
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database import User, PaperOrder
from schemas import TradeState, ExecutionResult, WorkflowState
from exceptions import DuplicateExecutionError, ExchangeUnavailableError
from services.exchange_client import exchange_client
from services.workflow_repository import workflow_repo

logger = logging.getLogger("ExecutionService")

class ExecutionService:
    """
    Handles idempotent execution and coordination with exchanges.
    """
    async def execute_trade(self, db: Session, user: User, state: TradeState, confirmation_token: str, token: str = "") -> ExecutionResult:
        logger.info(f"execute_trade called: workflow={state.workflow_id}, symbol={state.symbol}, qty={state.quantity}")
        
        # 1. Validate confirmation token
        if state.confirmation_token != confirmation_token:
            logger.error(f"Invalid confirmation token: {confirmation_token} (expected {state.confirmation_token})")
            return ExecutionResult(status="FAILED", error="Invalid confirmation token.")

        # 2. Idempotency Check & Pre-Execution Persistence
        if not state.execution_request_id:
            state.execution_request_id = str(uuid.uuid4())
            # CRITICAL: Save the ID to Redis BEFORE calling the exchange.
            await workflow_repo.save_state(state)
            logger.info(f"Assigned new execution request ID: {state.execution_request_id}")
        else:
            logger.warning(f"Retrying execution for existing request {state.execution_request_id}")

        try:
            logger.info(f"Placing order: symbol={state.symbol}, qty={state.quantity}, side={state.side}, type={state.order_type}")
            
            # 3. Delegate to exchange client with the idempotency key
            result = exchange_client.place_order(
                db=db,
                user=user,
                symbol=state.symbol,
                quantity=state.quantity,
                side=state.side,
                order_type=state.order_type,
                limit_price=state.limit_price,
                token=token,
                execution_request_id=state.execution_request_id
            )
            
            logger.info(f"Exchange result: {result}")
            
            if "error" in result:
                logger.error(f"Execution failed: {result['error']}")
                return ExecutionResult(status="FAILED", error=result["error"])

            # 4. Normalize result
            return ExecutionResult(
                status=result.get("status", "PENDING"),
                order_id=str(result.get("id")),
                fill_price=result.get("fill_price"),
                fee=result.get("fee"),
                total_cost=result.get("total_cost"),
                new_balance=result.get("new_cash_balance")
            )

        except Exception as e:
            logger.error(f"Execution service error: {e}\n{traceback.format_exc()}")
            return ExecutionResult(status="FAILED", error=str(e))

execution_service = ExecutionService()
