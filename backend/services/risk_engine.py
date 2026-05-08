from decimal import Decimal
import logging
from typing import Dict, Any

logger = logging.getLogger("RiskEngine")

class RiskEngine:
    def __init__(self, max_order_usd: float = 10000.0, max_slippage: float = 0.01):
        self.max_order_usd = Decimal(str(max_order_usd))
        self.max_slippage = Decimal(str(max_slippage))

    def assess_trade(self, symbol: str, quantity: float, price: float, side: str, wallet_balance: float) -> Dict[str, Any]:
        """
        Assesses a trade for risk and compliance.
        Returns: {
            "action": "ALLOW" | "BLOCK" | "WARN",
            "reason": str,
            "metrics": dict
        }
        """
        qty = Decimal(str(quantity))
        px = Decimal(str(price))
        bal = Decimal(str(wallet_balance))
        total_value = qty * px
        
        side = side.upper()
        
        # 1. Max Order Size Check
        if total_value > self.max_order_usd:
            return {
                "action": "BLOCK",
                "reason": f"Order value ${total_value:,.2f} exceeds max limit of ${self.max_order_usd:,.2f}.",
                "metrics": {"total_value": float(total_value)}
            }
            
        # 2. Insufficient Balance Check (for BUY)
        if side == "BUY" and total_value > bal:
            return {
                "action": "BLOCK",
                "reason": f"Insufficient balance. You need ${total_value:,.2f} but only have ${bal:,.2f}.",
                "metrics": {"total_value": float(total_value), "balance": float(bal)}
            }
            
        # 3. Portfolio Exposure Warning (Simplified: if > 30% of balance)
        if side == "BUY" and bal > 0 and (total_value / bal) > Decimal("0.3"):
            return {
                "action": "WARN",
                "reason": f"High Exposure: This trade represents {(total_value/bal*100):.1f}% of your portfolio.",
                "metrics": {"exposure": float(total_value/bal)}
            }

        return {
            "action": "ALLOW",
            "reason": "Risk checks passed.",
            "metrics": {"total_value": float(total_value)}
        }

risk_engine = RiskEngine()
