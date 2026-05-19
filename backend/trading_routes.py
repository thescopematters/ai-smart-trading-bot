"""
TRADING REST API ROUTES
-----------------------
Two endpoints for the Chatbot UI:
  POST /api/v1/get_quote
  POST /api/v1/place_order
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP
import requests
import os
import logging
from dotenv import load_dotenv

from database import get_db, PaperWallet, PaperPosition, PaperOrder, PaperTrade
from auth import get_current_user
from database import User

load_dotenv()
logger = logging.getLogger("TradingRoutes")

router = APIRouter(prefix="/api/v1", tags=["Trading"])

CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")
FEE_RATE = Decimal("0.001")  # 0.1%


# ---------------------------------------------------------
# Helper: Fetch Live Price
# ---------------------------------------------------------
def fetch_live_price(symbol: str) -> Decimal:
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"symbol": symbol.upper(), "convert": "USD"}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    data = resp.json()
    price = data["data"][symbol.upper()]["quote"]["USD"]["price"]
    return Decimal(str(price))


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------
class QuoteRequest(BaseModel):
    symbol: str
    quantity: float
    side: str  # BUY or SELL


class OrderRequest(BaseModel):
    symbol: str
    quantity: float
    side: str         # BUY or SELL
    order_type: str   # MARKET or LIMIT
    limit_price: Optional[float] = None


# ---------------------------------------------------------
# POST /api/v1/get_quote
# ---------------------------------------------------------
@router.post("/get_quote")
def get_quote(
    req: QuoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get price quote before placing an order.
    Returns current price, fee, total cost, and wallet balance check.
    """
    try:
        symbol = req.symbol.upper()
        side = req.side.upper()
        qty = Decimal(str(req.quantity))

        # Validate side
        if side not in ["BUY", "SELL"]:
            raise HTTPException(status_code=400, detail="side must be BUY or SELL")

        # Get live price
        price = fetch_live_price(symbol)

        # Calculate costs
        gross_cost = (price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fee = (gross_cost * FEE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_cost = (gross_cost + fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Check wallet
        wallet = db.query(PaperWallet).filter(
            PaperWallet.user_id == current_user.id
        ).first()

        if not wallet:
            initial_cash = Decimal("100000.00")
            wallet = PaperWallet(
                user_id=current_user.id,
                cash_balance=initial_cash,
                initial_balance=initial_cash,
                currency="USD",
                unrealized_pnl=Decimal("0"),
                total_equity=initial_cash
            )
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
            logger.info(f"Auto-initialized paper wallet via route for user {current_user.id}")

        wallet_info = {}
        if wallet:
            balance = Decimal(wallet.cash_balance)
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
            "fee_rate": "0.1%",
            "total_cost": float(total_cost),
            "wallet": wallet_info
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_quote error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# POST /api/v1/place_order
# ---------------------------------------------------------
@router.post("/place_order")
def place_order(
    req: OrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Place a Market or Limit paper trading order.
    """
    try:
        symbol = req.symbol.upper()
        side = req.side.upper()
        order_type = req.order_type.upper()
        qty = Decimal(str(req.quantity))

        # Validations
        if side not in ["BUY", "SELL"]:
            raise HTTPException(status_code=400, detail="side must be BUY or SELL")
        if order_type not in ["MARKET", "LIMIT"]:
            raise HTTPException(status_code=400, detail="order_type must be MARKET or LIMIT")
        if order_type == "LIMIT" and not req.limit_price:
            raise HTTPException(status_code=400, detail="limit_price is required for LIMIT orders")

        # Get wallet
        wallet = db.query(PaperWallet).filter(
            PaperWallet.user_id == current_user.id
        ).first()
        if not wallet:
            initial_cash = Decimal("100000.00")
            wallet = PaperWallet(
                user_id=current_user.id,
                cash_balance=initial_cash,
                initial_balance=initial_cash,
                currency="USD",
                unrealized_pnl=Decimal("0"),
                total_equity=initial_cash
            )
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
            logger.info(f"Auto-initialized paper wallet via order route for user {current_user.id}")

        cash_balance = Decimal(wallet.cash_balance)
        realized_pnl = Decimal("0")

        # --- MARKET ORDER ---
        if order_type == "MARKET":
            fill_price = fetch_live_price(symbol)
            gross_cost = (fill_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            fee = (gross_cost * FEE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total_cost = gross_cost + fee

            if side == "BUY":
                if cash_balance < total_cost:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient balance. Have ${cash_balance:.2f}, need ${total_cost:.2f}"
                    )
                wallet.cash_balance = str((cash_balance - total_cost).quantize(Decimal("0.01")))

                # Update position
                position = db.query(PaperPosition).filter(
                    PaperPosition.user_id == current_user.id,
                    PaperPosition.symbol == symbol
                ).first()

                if position:
                    old_qty = Decimal(position.quantity)
                    old_cost = Decimal(position.total_cost_basis)
                    new_qty = old_qty + qty
                    new_cost = old_cost + gross_cost
                    position.quantity = str(new_qty)
                    position.avg_entry_price = str((new_cost / new_qty).quantize(Decimal("0.01")))
                    position.total_cost_basis = str(new_cost)
                else:
                    db.add(PaperPosition(
                        user_id=current_user.id,
                        symbol=symbol,
                        quantity=str(qty),
                        avg_entry_price=str(fill_price.quantize(Decimal("0.01"))),
                        total_cost_basis=str(gross_cost),
                        realized_pnl="0"
                    ))

            elif side == "SELL":
                position = db.query(PaperPosition).filter(
                    PaperPosition.user_id == current_user.id,
                    PaperPosition.symbol == symbol
                ).first()
                if not position or Decimal(position.quantity) < qty:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient {symbol} holdings to sell"
                    )

                avg_entry = Decimal(position.avg_entry_price)
                realized_pnl = ((fill_price - avg_entry) * qty - fee).quantize(Decimal("0.01"))

                new_qty = Decimal(position.quantity) - qty
                position.quantity = str(new_qty)
                position.realized_pnl = str(Decimal(position.realized_pnl) + realized_pnl)

                proceeds = (fill_price * qty) - fee
                wallet.cash_balance = str((cash_balance + proceeds).quantize(Decimal("0.01")))
                total_cost = gross_cost

            # Save order + trade
            order = PaperOrder(
                user_id=current_user.id,
                symbol=symbol, side=side,
                order_type="MARKET",
                quantity=str(qty),
                status="FILLED"
            )
            db.add(order)
            db.flush()

            db.add(PaperTrade(
                order_id=order.id,
                user_id=current_user.id,
                symbol=symbol, side=side,
                quantity=str(qty),
                fill_price=str(fill_price.quantize(Decimal("0.01"))),
                fee=str(fee),
                total_cost=str(total_cost),
                realized_pnl=str(realized_pnl)
            ))
            db.commit()

            return {
                "status": "FILLED",
                "order_type": "MARKET",
                "symbol": symbol,
                "side": side,
                "quantity": float(qty),
                "fill_price": float(fill_price),
                "fee": float(fee),
                "total_cost": float(total_cost),
                "realized_pnl": float(realized_pnl),
                "new_cash_balance": float(Decimal(wallet.cash_balance))
            }

        # --- LIMIT ORDER ---
        elif order_type == "LIMIT":
            lp = Decimal(str(req.limit_price))
            estimated_cost = (lp * qty * (1 + FEE_RATE)).quantize(Decimal("0.01"))

            if side == "BUY" and cash_balance < estimated_cost:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. Have ${cash_balance:.2f}, need ~${estimated_cost:.2f}"
                )

            order = PaperOrder(
                user_id=current_user.id,
                symbol=symbol, side=side,
                order_type="LIMIT",
                quantity=str(qty),
                target_price=str(lp),
                status="PENDING"
            )
            db.add(order)
            db.commit()

            return {
                "status": "PENDING",
                "order_type": "LIMIT",
                "symbol": symbol,
                "side": side,
                "quantity": float(qty),
                "limit_price": float(lp),
                "estimated_cost": float(estimated_cost),
                "message": f"Limit order placed. Will execute when {symbol} hits ${lp:,.2f}"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"place_order error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
