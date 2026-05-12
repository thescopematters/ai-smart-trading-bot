from decimal import Decimal
import logging
from typing import Dict, Any
from schemas import RiskAssessment
from config import settings

logger = logging.getLogger("RiskEngine")

class RiskEngine:
    def __init__(self, max_order_usd: float = None, max_portfolio_exposure: float = None, max_daily_loss: float = None):
        self.max_order_usd = Decimal(str(max_order_usd or settings.MAX_ORDER_USD))
        self.max_portfolio_exposure = Decimal(str(max_portfolio_exposure or settings.MAX_PORTFOLIO_EXPOSURE))
        self.max_daily_loss = Decimal(str(max_daily_loss or settings.MAX_DAILY_LOSS_USD))

    def assess_trade(self, symbol: str, quantity: float, price: float, side: str, wallet_balance: float, daily_pnl: float = 0) -> RiskAssessment:
        """
        Assesses a trade for risk and compliance.
        Includes check for daily loss limits.
        """
        qty = Decimal(str(quantity))
        px = Decimal(str(price))
        bal = Decimal(str(wallet_balance))
        dpnl = Decimal(str(daily_pnl))
        total_value = qty * px
        
        side = side.upper()

        # 0. Daily Loss Limit Check
        if dpnl < 0 and abs(dpnl) >= self.max_daily_loss:
            return RiskAssessment(
                action="BLOCK",
                reason=f"Daily Loss Limit Reached: Current loss of ${abs(dpnl):,.2f} exceeds limit of ${self.max_daily_loss:,.2f}.",
                metrics={"daily_pnl": float(dpnl)}
            )
        
        # 1. Max Order Size Check
        if total_value > self.max_order_usd:
            return RiskAssessment(
                action="BLOCK",
                reason=f"Order value ${total_value:,.2f} exceeds max limit of ${self.max_order_usd:,.2f}.",
                metrics={"total_value": float(total_value)}
            )
            
        # 2. Insufficient Balance Check (for BUY)
        if side == "BUY" and total_value > bal:
            return RiskAssessment(
                action="BLOCK",
                reason=f"Insufficient balance. You need ${total_value:,.2f} but only have ${bal:,.2f}.",
                metrics={"total_value": float(total_value), "balance": float(bal)}
            )
            
        # 3. Portfolio Exposure Warning
        if side == "BUY" and bal > 0 and (total_value / bal) > self.max_portfolio_exposure:
            return RiskAssessment(
                action="WARN",
                reason=f"High Exposure: This trade represents {(total_value/bal*100):.1f}% of your portfolio.",
                metrics={"exposure": float(total_value/bal)}
            )

        return RiskAssessment(
            action="ALLOW",
            reason="Risk checks passed.",
            metrics={"total_value": float(total_value)}
        )

risk_engine = RiskEngine()
