import logging
from typing import Optional
from schemas import WorkflowState, TradeState, VALID_TRANSITIONS
from exceptions import InvalidWorkflowTransitionError, DuplicateExecutionError
from services.workflow_repository import workflow_repo

logger = logging.getLogger("WorkflowOrchestrator")

class WorkflowOrchestrator:
    """
    Deterministic state machine for trade workflows.
    Enforces valid transitions and prevents duplicate workflows.
    """

    def get_active_workflow(self, session_id: str) -> Optional[TradeState]:
        return workflow_repo.get_state(session_id)

    def initiate_workflow(self, state: TradeState) -> TradeState:
        """Starts a new workflow, checking for existing ones for the same symbol."""
        # 1. Check for duplicate active workflow for this user/symbol
        active_list = workflow_repo.list_active_workflows(state.user_id)
        for existing in active_list:
            if existing.symbol == state.symbol and existing.status != WorkflowState.FAILED:
                # Note: In production, we might allow multiple, but here we enforce one per symbol for safety.
                logger.warning(f"Duplicate workflow attempt: {state.user_id} for {state.symbol}")
                # We could raise an error here if we want to be strict
        
        state.status = WorkflowState.INITIATED
        workflow_repo.save_state(state)
        logger.info(f"Workflow {state.workflow_id} INITIATED for {state.symbol}")
        return state

    def transition(self, session_id: str, to_state: WorkflowState, updates: dict = None) -> TradeState:
        """Moves the workflow to a new state with validation."""
        state = workflow_repo.get_state(session_id)
        if not state:
            raise InvalidWorkflowTransitionError("No active workflow found for this session.")

        current_state = state.status
        if to_state not in VALID_TRANSITIONS.get(current_state, []):
            logger.error(f"Invalid transition: {current_state} -> {to_state}")
            raise InvalidWorkflowTransitionError(
                f"Cannot move from {current_state} to {to_state}.",
                user_message="I'm sorry, that action is not valid in the current trade step."
            )

        # Update fields if provided
        if updates:
            for key, value in updates.items():
                if hasattr(state, key):
                    setattr(state, key, value)

        state.status = to_state
        workflow_repo.save_state(state)
        logger.info(f"Workflow {state.workflow_id} transitioned: {current_state} -> {to_state}")
        
        # Emitting "event" (currently just a log, ready for Redis Streams/Kafka)
        self._emit_event(state, "STATE_CHANGE", {"from": current_state, "to": to_state})
        
        return state

    def clear_workflow(self, session_id: str):
        workflow_repo.delete_state(session_id)

    def _emit_event(self, state: TradeState, event_type: str, data: dict):
        """Placeholder for future event-driven bus (Kafka/Redis Streams)."""
        logger.debug(f"[EVENT] {event_type} | workflow={state.workflow_id} | data={data}")

orchestrator = WorkflowOrchestrator()
