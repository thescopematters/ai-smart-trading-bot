import logging
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database import User, PaperOrder # We check DB for idempotency
from schemas import TradeState, ExecutionResult, WorkflowState
from exceptions import DuplicateExecutionError, ExchangeUnavailableError
from services.exchange_client import exchange_client

logger = logging.getLogger("ExecutionService")

class ExecutionService:
    """
    Handles idempotent execution and coordination with exchanges.
    """
    def execute_trade(self, db: Session, user: User, state: TradeState, confirmation_token: str, token: str = "") -> ExecutionResult:
        # 1. Validate confirmation token
        if state.confirmation_token != confirmation_token:
            logger.error(f"Invalid confirmation token: {confirmation_token} (expected {state.confirmation_token})")
            return ExecutionResult(status="FAILED", error="Invalid confirmation token.")

        # 2. Idempotency Check: check if execution_request_id already processed
        if state.execution_request_id:
            logger.warning(f"Duplicate execution attempt for request {state.execution_request_id}")
            raise DuplicateExecutionError(f"Execution {state.execution_request_id} already in progress or completed.")

        # 3. Assign unique execution request ID
        state.execution_request_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Executing trade workflow {state.workflow_id} (Request ID: {state.execution_request_id})")
            
            # 4. Delegate to exchange client
            result = exchange_client.place_order(
                db=db,
                user=user,
                symbol=state.symbol,
                quantity=state.quantity,
                side=state.side,
                order_type=state.order_type,
                limit_price=state.limit_price,
                token=token
            )
            
            if "error" in result:
                logger.error(f"Execution failed: {result['error']}")
                return ExecutionResult(status="FAILED", error=result["error"])

            # 5. Normalize result
            return ExecutionResult(
                status=result.get("status", "PENDING"),
                order_id=str(result.get("id")),
                fill_price=result.get("fill_price"),
                fee=result.get("fee"),
                total_cost=result.get("total_cost"),
                new_balance=result.get("new_cash_balance")
            )

        except Exception as e:
            logger.error(f"Execution service error: {e}")
            return ExecutionResult(status="FAILED", error=str(e))

execution_service = ExecutionService()
