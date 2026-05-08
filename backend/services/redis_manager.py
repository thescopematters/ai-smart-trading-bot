import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class RedisConversationManager:
    def __init__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True)

    def get_trade_state(self, session_id: str) -> dict:
        state = self.client.get(f"trade_state:{session_id}")
        return json.loads(state) if state else {}

    def set_trade_state(self, session_id: str, state: dict, ex: int = 600):
        """Set trade state with a 10-minute expiry."""
        self.client.set(f"trade_state:{session_id}", json.dumps(state), ex=ex)

    def clear_trade_state(self, session_id: str):
        self.client.delete(f"trade_state:{session_id}")

redis_manager = RedisConversationManager()
