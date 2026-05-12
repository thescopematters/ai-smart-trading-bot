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
    async def get_state(self, session_id: str) -> Optional[TradeState]:
        """Async fetch of trade state."""
        return await redis_manager.get_trade_state(session_id)

    async def save_state(self, state: TradeState):
        """
        Async save of trade state with optimized user-indexing.
        Uses a Redis Set to track active workflows per user for O(1) discovery.
        """
        try:
            # 1. Save the state with 24h TTL
            await redis_manager.set_trade_state(state.session_id, state, ex=86400)
            
            # 2. Add to user's active workflow index
            index_key = f"user_workflows:{state.user_id}"
            await redis_manager.client.sadd(index_key, state.session_id)
            await redis_manager.client.expire(index_key, 86400)
            
        except Exception as e:
            logger.error(f"Repository save_state error: {e}")

    async def delete_state(self, session_id: str):
        """Async deletion with index cleanup."""
        try:
            # Fetch state first to get user_id for index cleanup
            state = await self.get_state(session_id)
            if state:
                await redis_manager.client.srem(f"user_workflows:{state.user_id}", session_id)
            
            await redis_manager.clear_trade_state(session_id)
        except Exception as e:
            logger.error(f"Repository delete_state error: {e}")

    async def list_active_workflows(self, user_id: str) -> List[TradeState]:
        """
        Optimized O(K) fetch where K is the number of active workflows for this user.
        Replaces O(N) SCAN of all global keys.
        """
        active = []
        try:
            index_key = f"user_workflows:{user_id}"
            session_ids = await redis_manager.client.smembers(index_key)
            
            if not session_ids:
                return []

            # Fetch all states in the set
            for session_id in session_ids:
                state = await self.get_state(session_id)
                if state:
                    active.append(state)
                else:
                    # Stale index entry, cleanup
                    await redis_manager.client.srem(index_key, session_id)
                    
        except Exception as e:
            logger.error(f"Repository list_active_workflows error: {e}")
        return active

# For now, we use Redis as primary
workflow_repo = RedisWorkflowRepository()
