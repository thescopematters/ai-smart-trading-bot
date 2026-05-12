from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseExchange(ABC):
    @abstractmethod
    def get_quote(self, symbol: str, quantity: float, side: str, token: str = "") -> Dict[str, Any]:
        """Returns live price and wallet info."""
        pass

    @abstractmethod
    def place_order(self, symbol: str, quantity: float, side: str, 
                    order_type: str, limit_price: Optional[float] = None, 
                    token: str = "", execution_request_id: str = None) -> Dict[str, Any]:
        """Executes a trade on the exchange with idempotency check."""
        pass

    @abstractmethod
    def get_order_status(self, order_id: str, token: str = "") -> Dict[str, Any]:
        """Retrieves current status of an order."""
        pass
