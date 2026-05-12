import redis.asyncio as redis
import json
import os
import logging
from typing import Optional, Dict, Any
from schemas import TradeState
from config import settings

logger = logging.getLogger("RedisManager")

class RedisConversationManager:
    """
    Handles distributed session and trade state using Redis.
    Uses asyncio for non-blocking performance.
    """
    def __init__(self):
        # Initialize client but don't ping here as __init__ is sync
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.use_redis = True # We enforce Redis for production consistency

    async def get_trade_state(self, session_id: str) -> Optional[TradeState]:
        """Retrieves trade state from Redis. Returns None if missing or on error."""
        try:
            data = await self.client.get(f"trade_state:{session_id}")
            if data:
                return TradeState.parse_raw(data)
            return None
        except Exception as e:
            logger.error(f"Error getting trade state for {session_id}: {e}")
            # We do NOT fallback to local dict here to prevent split-brain in multi-worker setups
            return None

    async def set_trade_state(self, session_id: str, state: TradeState, ex: int = 86400):
        """
        Set trade state with a persistent TTL (default 24h).
        Previous 10m TTL was too short for financial workflows.
        """
        try:
            data = state.json()
            await self.client.set(f"trade_state:{session_id}", data, ex=ex)
        except Exception as e:
            logger.error(f"Error setting trade state for {session_id}: {e}")

    async def clear_trade_state(self, session_id: str):
        """Removes trade state from Redis."""
        try:
            await self.client.delete(f"trade_state:{session_id}")
        except Exception as e:
            logger.error(f"Error clearing trade state for {session_id}: {e}")

    async def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """
        Generic sliding window rate limiter using Redis.
        limit: Max number of calls
        window: Time window in seconds
        """
        try:
            current = await self.client.get(f"rl:{key}")
            if current and int(current) >= limit:
                return True
            
            async with self.client.pipeline(transaction=True) as pipe:
                await pipe.incr(f"rl:{key}")
                await pipe.expire(f"rl:{key}", window)
                await pipe.execute()
            return False
        except Exception as e:
            logger.error(f"Rate limiter error for {key}: {e}")
            return False

redis_manager = RedisConversationManager()
