import time
import logging
from typing import Dict, Tuple
from services.redis_manager import redis_manager

logger = logging.getLogger("RateLimiter")

class RateLimiter:
    """
    Redis-based sliding window rate limiter.
    """
    def is_allowed(self, user_id: str, action: str, limit: int, window: int = 60) -> Tuple[bool, int]:
        """
        Checks if user is within the limit for a specific action.
        Returns (is_allowed, current_count)
        """
        key = f"ratelimit:{action}:{user_id}"
        now = time.time()
        
        try:
            # Use Redis pipeline for atomicity
            pipe = redis_manager.client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window)
            results = pipe.execute()
            
            current_count = results[2]
            allowed = current_count <= limit
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for user {user_id} on {action}: {current_count}/{limit}")
            
            return allowed, current_count
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True, 0 # Fail open in case of Redis error for UX

rate_limiter = RateLimiter()
