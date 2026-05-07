"""
MCP TRADING SERVER
------------------
Handles Paper Trading tools for the AI Agent.
Tools:
  1. get_quote     - Get current price + fee estimate before placing order
  2. place_order   - Place Market or Limit order (BUY/SELL)
"""

from fastmcp import FastMCP
import os
import logging
import requests
from decimal import Decimal, ROUND_HALF_UP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Crypto-Trading")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPTradingServer")

CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")
FEE_RATE = Decimal("0.001")  # 0.1% fee

try:
    from database import SessionLocal, PaperWallet, PaperPosition, PaperOrder, PaperTrade
except ImportError:
    logger.error("database.py not found.")
    SessionLocal = None

DEFAULT_USER_ID = "eceee63a-c1fa-48de-aa15-b75fcfd79809"

# ---------------------------------------------------------
# Helper: Get Live Price from CoinMarketCap
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
# Tool 1: get_quote
# ---------------------------------------------------------
@mcp.tool()
def get_quote(symbol: str, quantity: float, side: str, user_id: str = DEFAULT_USER_ID) -> dict:
    """
    Get a price quote before placing an order.
    Shows current price, estimated total cost, and fees.

    Args:
        symbol:   Crypto symbol e.g. BTC, ETH
        quantity: Amount to buy/sell e.g. 0.01
        side:     BUY or SELL
        user_id:  User ID
    """
    try:
        symbol = symbol.upper()
        side = side.upper()
        qty = Decimal(str(quantity))

        # Get live price
        price = fetch_live_price(symbol)

        # Calculate cost and fee
        gross_cost = (price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fee = (gross_cost * FEE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (gross_cost + fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Check wallet balance for BUY
        wallet_info = ""
        if SessionLocal:
            db = SessionLocal()
            wallet = db.query(PaperWallet).filter(PaperWallet.user_id == user_id).first()
            if wallet:
                balance = Decimal(wallet.cash_balance)
                if side == "BUY":
                    if balance < total:
                        wallet_info = f"⚠️ Insufficient balance. You have ${balance:.2f} but need ${total:.2f}"
                    else:
                        wallet_info = f"✅ Balance after order: ${(balance - total):.2f}"
            db.close()

        return {
            "symbol": symbol,
            "side": side,
            "quantity": float(qty),
            "current_price": float(price),
            "gross_cost": float(gross_cost),
            "fee": float(fee),
            "total_cost": float(total),
            "fee_rate": "0.1%",
            "wallet_info": wallet_info,
            "message": f"Quote ready. Confirm to place {side} order for {qty} {symbol} at ${price:,.2f}"
        }

    except Exception as e:
        logger.error(f"get_quote error: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------
# Tool 2: place_order
# ---------------------------------------------------------
@mcp.tool()
def place_order(
    symbol: str,
    quantity: float,
    side: str,
    order_type: str,
    limit_price: float = None,
    user_id: str = DEFAULT_USER_ID
) -> dict:
    """
    Place a paper trading order (Market or Limit).

    Args:
        symbol:      Crypto symbol e.g. BTC, ETH
        quantity:    Amount to buy/sell
        side:        BUY or SELL
        order_type:  MARKET or LIMIT
        limit_price: Required if order_type is LIMIT
        user_id:     User ID
    """
    if not SessionLocal:
        return {"error": "Database not available"}

    try:
        symbol = symbol.upper()
        side = side.upper()
        order_type = order_type.upper()
        qty = Decimal(str(quantity))

        db = SessionLocal()

        # Get or create wallet
        wallet = db.query(PaperWallet).filter(PaperWallet.user_id == user_id).first()
        if not wallet:
            db.close()
            return {"error": "Wallet not found. Please contact support."}

        cash_balance = Decimal(wallet.cash_balance)

        # --- MARKET ORDER ---
        if order_type == "MARKET":
            fill_price = fetch_live_price(symbol)
            gross_cost = (fill_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            fee = (gross_cost * FEE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total_cost = gross_cost + fee

            if side == "BUY":
                if cash_balance < total_cost:
                    db.close()
                    return {"error": f"Insufficient balance. Have ${cash_balance:.2f}, need ${total_cost:.2f}"}

                # Deduct balance
                wallet.cash_balance = str((cash_balance - total_cost).quantize(Decimal("0.01")))

                # Update position
                position = db.query(PaperPosition).filter(
                    PaperPosition.user_id == user_id,
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
                    position = PaperPosition(
                        user_id=user_id,
                        symbol=symbol,
                        quantity=str(qty),
                        avg_entry_price=str(fill_price.quantize(Decimal("0.01"))),
                        total_cost_basis=str(gross_cost),
                        realized_pnl="0"
                    )
                    db.add(position)

            elif side == "SELL":
                position = db.query(PaperPosition).filter(
                    PaperPosition.user_id == user_id,
                    PaperPosition.symbol == symbol
                ).first()

                if not position or Decimal(position.quantity) < qty:
                    db.close()
                    return {"error": f"Insufficient {symbol} to sell. You don't have enough."}

                # Calculate P&L
                avg_entry = Decimal(position.avg_entry_price)
                realized_pnl = ((fill_price - avg_entry) * qty - fee).quantize(Decimal("0.01"))

                # Update position
                new_qty = Decimal(position.quantity) - qty
                position.quantity = str(new_qty)
                position.realized_pnl = str(Decimal(position.realized_pnl) + realized_pnl)

                # Credit balance
                proceeds = (fill_price * qty) - fee
                wallet.cash_balance = str((cash_balance + proceeds).quantize(Decimal("0.01")))

                total_cost = gross_cost  # for response

            # Save order
            order = PaperOrder(
                user_id=user_id,
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=str(qty),
                status="FILLED"
            )
            db.add(order)
            db.flush()

            # Save trade
            trade = PaperTrade(
                order_id=order.id,
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=str(qty),
                fill_price=str(fill_price.quantize(Decimal("0.01"))),
                fee=str(fee),
                total_cost=str(total_cost),
                realized_pnl=str(realized_pnl) if side == "SELL" else "0"
            )
            db.add(trade)
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
                "new_cash_balance": float(Decimal(wallet.cash_balance)),
                "message": f"✅ {side} order filled! {qty} {symbol} at ${fill_price:,.2f}"
            }

        # --- LIMIT ORDER ---
        elif order_type == "LIMIT":
            if not limit_price:
                db.close()
                return {"error": "limit_price is required for LIMIT orders"}

            lp = Decimal(str(limit_price))
            estimated_cost = (lp * qty * (1 + FEE_RATE)).quantize(Decimal("0.01"))

            if side == "BUY" and cash_balance < estimated_cost:
                db.close()
                return {"error": f"Insufficient balance for limit order. Have ${cash_balance:.2f}, need ~${estimated_cost:.2f}"}

            order = PaperOrder(
                user_id=user_id,
                symbol=symbol,
                side=side,
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
                "message": f"📋 Limit order placed! {side} {qty} {symbol} when price hits ${lp:,.2f}"
            }

        else:
            db.close()
            return {"error": f"Unknown order_type: {order_type}. Use MARKET or LIMIT."}

    except Exception as e:
        logger.error(f"place_order error: {e}", exc_info=True)
        if 'db' in locals():
            db.rollback()
            db.close()
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()
