import redis
import json
import os
import logging
from typing import Optional, Dict, Any
from schemas import TradeState
from config import settings

logger = logging.getLogger("RedisManager")

class RedisConversationManager:
    def __init__(self):
        try:
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.client.ping()
            self.use_redis = True
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Falling back to in-memory storage.")
            self.client = {} # In-memory dict
            self.use_redis = False

    def get_trade_state(self, session_id: str) -> Optional[TradeState]:
        try:
            if self.use_redis:
                data = self.client.get(f"trade_state:{session_id}")
            else:
                data = self.client.get(f"trade_state:{session_id}")
            
            if data:
                return TradeState.parse_raw(data)
            return None
        except Exception as e:
            logger.error(f"Error getting trade state: {e}")
            return None

    def set_trade_state(self, session_id: str, state: TradeState, ex: int = 600):
        """Set trade state with a 10-minute expiry."""
        try:
            data = state.json()
            if self.use_redis:
                self.client.set(f"trade_state:{session_id}", data, ex=ex)
            else:
                self.client[f"trade_state:{session_id}"] = data
        except Exception as e:
            logger.error(f"Error setting trade state: {e}")

    def clear_trade_state(self, session_id: str):
        try:
            if self.use_redis:
                self.client.delete(f"trade_state:{session_id}")
            else:
                self.client.pop(f"trade_state:{session_id}", None)
        except Exception as e:
            logger.error(f"Error clearing trade state: {e}")

redis_manager = RedisConversationManager()
