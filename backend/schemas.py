from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List
from enum import Enum
import uuid

# --- Workflow State Enum ---
class WorkflowState(str, Enum):
    INITIATED = "INITIATED"
    RISK_CHECKED = "RISK_CHECKED"
    AWAITING_ORDER_TYPE = "AWAITING_ORDER_TYPE"
    AWAITING_LIMIT_PRICE = "AWAITING_LIMIT_PRICE"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    EXECUTING = "EXECUTING"
    FILLED = "FILLED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

# --- Valid State Transitions ---
VALID_TRANSITIONS = {
    WorkflowState.INITIATED:             [WorkflowState.RISK_CHECKED, WorkflowState.FAILED],
    WorkflowState.RISK_CHECKED:          [WorkflowState.AWAITING_ORDER_TYPE, WorkflowState.FAILED],
    WorkflowState.AWAITING_ORDER_TYPE:   [WorkflowState.AWAITING_LIMIT_PRICE, WorkflowState.AWAITING_CONFIRMATION, WorkflowState.FAILED],
    WorkflowState.AWAITING_LIMIT_PRICE:  [WorkflowState.AWAITING_CONFIRMATION, WorkflowState.FAILED],
    WorkflowState.AWAITING_CONFIRMATION: [WorkflowState.EXECUTING, WorkflowState.CANCELLED, WorkflowState.FAILED],
    WorkflowState.EXECUTING:             [WorkflowState.FILLED, WorkflowState.FAILED],
    WorkflowState.FILLED:                [],  # Terminal
    WorkflowState.FAILED:                [],  # Terminal
    WorkflowState.CANCELLED:             [],  # Terminal
}

class TradeRequest(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float
    order_type: Optional[Literal["MARKET", "LIMIT"]] = None
    limit_price: Optional[float] = None

class RiskAssessment(BaseModel):
    action: Literal["ALLOW", "BLOCK", "WARN"]
    reason: str
    metrics: Dict[str, Any] = Field(default_factory=dict)

class ExecutionResult(BaseModel):
    status: Literal["FILLED", "PENDING", "FAILED"]
    order_id: Optional[str] = None
    fill_price: Optional[float] = None
    fee: Optional[float] = None
    total_cost: Optional[float] = None
    new_balance: Optional[float] = None
    error: Optional[str] = None

class TradeState(BaseModel):
    """Persisted state for a trade workflow."""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    symbol: str
    quantity: float
    side: str
    price: float
    order_type: Optional[str] = None
    limit_price: Optional[float] = None
    risk_report: Optional[Dict[str, Any]] = None
    status: WorkflowState = WorkflowState.INITIATED
    confirmation_token: str = Field(default_factory=lambda: str(uuid.uuid4()).split('-')[0])
    execution_request_id: Optional[str] = None
    created_at: float = Field(default_factory=lambda: 0.0) # placeholder for actual timestamp
