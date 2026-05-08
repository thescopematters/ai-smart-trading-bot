import os
import requests
import logging
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ExchangeClient")
BASE_URL = os.getenv("EXCHANGE_API_BASE_URL", "http://localhost:8000/api/v1")

class ExchangeClient:
    def get_quote(self, symbol: str, quantity: float, side: str, token: str = "") -> dict:
        """Calls POST /api/v1/get_quote"""
        url = f"{BASE_URL}/get_quote"
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        payload = {
            "symbol": symbol,
            "quantity": quantity,
            "side": side
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Error fetching quote: {e}")
            return {"success": False, "error": str(e)}

    def place_order(self, symbol: str, quantity: float, side: str, order_type: str, limit_price: float = None, token: str = "") -> dict:
        """Calls POST /api/v1/place_order"""
        url = f"{BASE_URL}/place_order"
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        payload = {
            "symbol": symbol,
            "quantity": quantity,
            "side": side,
            "order_type": order_type,
            "limit_price": limit_price
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"success": False, "error": str(e)}

exchange_client = ExchangeClient()
