from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
import requests
import logging
from sqlalchemy import func
from sqlalchemy.orm import Session
from exchange_gateway.base_exchange import BaseExchange
from database import PaperWallet, PaperPosition, PaperOrder, PaperTrade, User, Side, OrderType, OrderStatus
from config import settings

logger = logging.getLogger("PaperExchange")

FEE_RATE = Decimal("0.001") # 0.1%

class PaperExchange(BaseExchange):
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.user = current_user

    def fetch_live_price(self, symbol: str) -> Decimal:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": settings.COINMARKETCAP_API_KEY}
        params = {"symbol": symbol.upper(), "convert": "USD"}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        data = resp.json()
        price = data["data"][symbol.upper()]["quote"]["USD"]["price"]
        return Decimal(str(price))

    def get_quote(self, symbol: str, quantity: float, side: str, token: str = "") -> Dict[str, Any]:
        symbol = symbol.upper()
        side = side.upper()
        qty = Decimal(str(quantity))
        price = self.fetch_live_price(symbol)
        
        gross_cost = (price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fee = (gross_cost * FEE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_cost = (gross_cost + fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        wallet_info = {}
        if self.db and self.user:
            wallet = self.db.query(PaperWallet).filter(PaperWallet.user_id == self.user.id).first()
            if wallet:
                balance = wallet.cash_balance
                wallet_info = {
                    "current_balance": float(balance),
                    "sufficient": balance >= total_cost if side == "BUY" else True,
                    "balance_after": float((balance - total_cost).quantize(Decimal("0.01"))) if side == "BUY" else None
                }

        return {
            "symbol": symbol,
            "side": side,
            "quantity": float(qty),
            "current_price": float(price),
            "gross_cost": float(gross_cost),
            "fee": float(fee),
            "total_cost": float(total_cost),
            "wallet": wallet_info
        }

    def place_order(self, symbol: str, quantity: float, side: str, 
                    order_type: str, limit_price: Optional[float] = None, 
                    token: str = "", execution_request_id: str = None) -> Dict[str, Any]:
        
        # 1. Idempotency Check: prevent duplicate orders with same request ID
        if execution_request_id:
            existing_order = self.db.query(PaperOrder).filter(
                PaperOrder.execution_request_id == execution_request_id
            ).first()
            if existing_order:
                logger.warning(f"Returning existing order for idempotency key: {execution_request_id}")
                return {
                    "id": existing_order.id,
                    "status": existing_order.status.value,
                    "order_type": existing_order.order_type.value,
                    "symbol": existing_order.symbol,
                    "side": existing_order.side.value,
                    "quantity": float(existing_order.quantity),
                    "fill_price": float(existing_order.executed_price) if existing_order.executed_price else None
                }

        symbol = symbol.upper()
        side_enum = Side.BUY if side.upper() == "BUY" else Side.SELL
        order_type_enum = OrderType.MARKET if order_type.upper() == "MARKET" else OrderType.LIMIT
        qty = Decimal(str(quantity))
        
        wallet = self.db.query(PaperWallet).filter(PaperWallet.user_id == self.user.id).first()
        if not wallet:
            return {"error": "Wallet not found"}

        cash_balance = wallet.cash_balance
        realized_pnl = Decimal("0")

        if order_type_enum == OrderType.MARKET:
            fill_price = self.fetch_live_price(symbol)
            gross_cost = (fill_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            fee = (gross_cost * FEE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total_cost = gross_cost + fee

            if side_enum == Side.BUY:
                if cash_balance < total_cost:
                    return {"error": f"Insufficient balance. Have ${cash_balance:.2f}, need ${total_cost:.2f}"}
                wallet.cash_balance = (cash_balance - total_cost).quantize(Decimal("0.01"))

                position = self.db.query(PaperPosition).filter(
                    PaperPosition.user_id == self.user.id,
                    PaperPosition.symbol == symbol
                ).first()

                if position:
                    old_qty = position.quantity
                    old_cost = position.total_cost_basis
                    new_qty = old_qty + qty
                    new_cost = old_cost + gross_cost
                    position.quantity = new_qty
                    position.avg_entry_price = (new_cost / new_qty).quantize(Decimal("0.01"))
                    position.total_cost_basis = new_cost
                else:
                    self.db.add(PaperPosition(
                        user_id=self.user.id,
                        symbol=symbol,
                        quantity=qty,
                        avg_entry_price=fill_price.quantize(Decimal("0.01")),
                        total_cost_basis=gross_cost,
                        realized_pnl=Decimal("0")
                    ))

            elif side_enum == Side.SELL:
                position = self.db.query(PaperPosition).filter(
                    PaperPosition.user_id == self.user.id,
                    PaperPosition.symbol == symbol
                ).first()
                if not position or position.quantity < qty:
                    return {"error": f"Insufficient {symbol} holdings to sell"}

                avg_entry = position.avg_entry_price
                realized_pnl = ((fill_price - avg_entry) * qty - fee).quantize(Decimal("0.01"))

                new_qty = position.quantity - qty
                position.quantity = new_qty
                position.realized_pnl = position.realized_pnl + realized_pnl

                proceeds = (fill_price * qty) - fee
                wallet.cash_balance = (cash_balance + proceeds).quantize(Decimal("0.01"))
                total_cost = gross_cost

            order = PaperOrder(
                user_id=self.user.id,
                symbol=symbol, side=side_enum,
                order_type=OrderType.MARKET,
                quantity=qty,
                executed_price=fill_price,
                status=OrderStatus.FILLED,
                filled_at=func.now(),
                execution_request_id=execution_request_id
            )
            self.db.add(order)
            self.db.flush()

            self.db.add(PaperTrade(
                order_id=order.id,
                user_id=self.user.id,
                symbol=symbol, side=side_enum,
                quantity=qty,
                fill_price=fill_price.quantize(Decimal("0.01")),
                fee=fee,
                total_cost=total_cost,
                realized_pnl=realized_pnl
            ))
            self.db.commit()

            return {
                "id": order.id,
                "status": "FILLED",
                "order_type": "MARKET",
                "symbol": symbol,
                "side": side,
                "quantity": float(qty),
                "fill_price": float(fill_price),
                "fee": float(fee),
                "total_cost": float(total_cost),
                "realized_pnl": float(realized_pnl),
                "new_cash_balance": float(wallet.cash_balance)
            }

        elif order_type_enum == OrderType.LIMIT:
            lp = Decimal(str(limit_price))
            estimated_cost = (lp * qty * (1 + FEE_RATE)).quantize(Decimal("0.01"))

            if side_enum == Side.BUY and cash_balance < estimated_cost:
                return {"error": f"Insufficient balance. Have ${cash_balance:.2f}, need ~${estimated_cost:.2f}"}

            order = PaperOrder(
                user_id=self.user.id,
                symbol=symbol, side=side_enum,
                order_type=OrderType.LIMIT,
                quantity=qty,
                target_price=lp,
                status=OrderStatus.PENDING,
                execution_request_id=execution_request_id
            )
            self.db.add(order)
            self.db.commit()

            return {
                "id": order.id,
                "status": "PENDING",
                "order_type": "LIMIT",
                "symbol": symbol,
                "side": side,
                "quantity": float(qty),
                "limit_price": float(lp),
                "estimated_cost": float(estimated_cost)
            }

    def get_order_status(self, order_id: str, token: str = "") -> Dict[str, Any]:
        order = self.db.query(PaperOrder).filter(PaperOrder.id == int(order_id)).first()
        if not order:
            return {"error": "Order not found"}
        return {
            "id": order.id,
            "status": order.status.value,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": float(order.quantity)
        }

    def get_holdings(self) -> Dict[str, Any]:
        """Returns all open positions for the user."""
        positions = self.db.query(PaperPosition).filter(
            PaperPosition.user_id == self.user.id,
            PaperPosition.quantity > 0
        ).all()
        
        holdings = []
        for p in positions:
            holdings.append({
                "symbol": p.symbol,
                "quantity": float(p.quantity),
                "avg_entry_price": float(p.avg_entry_price),
                "total_cost_basis": float(p.total_cost_basis),
                "realized_pnl": float(p.realized_pnl)
            })
        return {"holdings": holdings}

    def get_trade_history(self, limit: int = 20) -> Dict[str, Any]:
        """Returns the most recent trades for the user."""
        trades = self.db.query(PaperTrade).filter(
            PaperTrade.user_id == self.user.id
        ).order_by(PaperTrade.executed_at.desc()).limit(limit).all()
        
        history = []
        for t in trades:
            history.append({
                "symbol": t.symbol,
                "side": t.side.value,
                "quantity": float(t.quantity),
                "price": float(t.fill_price),
                "total_cost": float(t.total_cost),
                "executed_at": t.executed_at.isoformat()
            })
        return {"trade_history": history}
