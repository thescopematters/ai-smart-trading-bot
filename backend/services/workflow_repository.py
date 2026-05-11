from abc import ABC, abstractmethod
from typing import Optional, List
import json
import logging
from schemas import TradeState
from services.redis_manager import redis_manager

logger = logging.getLogger("WorkflowRepository")

class WorkflowRepository(ABC):
    @abstractmethod
    def get_state(self, session_id: str) -> Optional[TradeState]:
        pass

    @abstractmethod
    def save_state(self, state: TradeState):
        pass

    @abstractmethod
    def delete_state(self, session_id: str):
        pass

    @abstractmethod
    def list_active_workflows(self, user_id: str) -> List[TradeState]:
        pass

class RedisWorkflowRepository(WorkflowRepository):
    def get_state(self, session_id: str) -> Optional[TradeState]:
        try:
            if redis_manager.use_redis:
                data = redis_manager.client.get(f"trade_state:{session_id}")
            else:
                data = redis_manager.client.get(f"trade_state:{session_id}")
            if data:
                return TradeState.parse_raw(data)
            return None
        except Exception as e:
            logger.error(f"Repository get_state error: {e}")
            return None

    def save_state(self, state: TradeState):
        try:
            if redis_manager.use_redis:
                redis_manager.client.set(
                    f"trade_state:{state.session_id}",
                    state.json(),
                    ex=600
                )
            else:
                redis_manager.client[f"trade_state:{state.session_id}"] = state.json()
        except Exception as e:
            logger.error(f"Repository save_state error: {e}")

    def delete_state(self, session_id: str):
        try:
            if redis_manager.use_redis:
                redis_manager.client.delete(f"trade_state:{session_id}")
            else:
                redis_manager.client.pop(f"trade_state:{session_id}", None)
        except Exception as e:
            logger.error(f"Repository delete_state error: {e}")

    def list_active_workflows(self, user_id: str) -> List[TradeState]:
        active = []
        try:
            if redis_manager.use_redis:
                for key in redis_manager.client.scan_iter("trade_state:*"):
                    data = redis_manager.client.get(key)
                    if data:
                        state = TradeState.parse_raw(data)
                        if state.user_id == user_id:
                            active.append(state)
            else:
                # In-memory fallback: scan dict keys
                for key, data in redis_manager.client.items():
                    if key.startswith("trade_state:") and data:
                        state = TradeState.parse_raw(data)
                        if state.user_id == user_id:
                            active.append(state)
        except Exception as e:
            logger.error(f"Repository list_active_workflows error: {e}")
        return active

# For now, we use Redis as primary
workflow_repo = RedisWorkflowRepository()
