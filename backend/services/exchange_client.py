import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database import User
from exchange_gateway.exchange_router import get_exchange

logger = logging.getLogger("ExchangeClient")

class ExchangeClient:
    """
    Client interface for interacting with crypto exchanges.
    Delegates to the appropriate gateway via exchange_router.
    """
    def get_quote(self, db: Session, user: User, symbol: str, quantity: float, side: str, token: str = "") -> Dict[str, Any]:
        """Returns live price and wallet info."""
        try:
            exchange = get_exchange(db, user)
            return exchange.get_quote(symbol, quantity, side, token)
        except Exception as e:
            logger.error(f"ExchangeClient get_quote error: {e}")
            return {"error": str(e)}

    def place_order(self, db: Session, user: User, symbol: str, quantity: float, side: str, 
                    order_type: str, limit_price: float = None, token: str = "",
                    execution_request_id: str = None) -> Dict[str, Any]:
        """Executes a trade on the active exchange with idempotency support."""
        try:
            exchange = get_exchange(db, user)
            return exchange.place_order(symbol, quantity, side, order_type, limit_price, token, execution_request_id)
        except Exception as e:
            logger.error(f"ExchangeClient place_order error: {e}")
            return {"error": str(e)}

    def get_order_status(self, db: Session, user: User, order_id: str, token: str = "") -> Dict[str, Any]:
        """Retrieves status for a specific order."""
        try:
            exchange = get_exchange(db, user)
            return exchange.get_order_status(order_id, token)
        except Exception as e:
            logger.error(f"ExchangeClient get_order_status error: {e}")
            return {"error": str(e)}

exchange_client = ExchangeClient()
