import logging
from decimal import Decimal
from services.exchange_client import exchange_client

logger = logging.getLogger("MarketAnalyst")

class MarketAnalyst:
    def get_market_insight(self, symbol: str) -> dict:
        """
        Analyzes market data to provide insights.
        Simulates volatility and trend analysis.
        """
        try:
            # Get current quote
            # Note: We use 1.0 quantity just to get the price
            quote = exchange_client.get_quote(symbol, 1.0, "BUY")
            if "error" in quote:
                return {"error": quote["error"]}
            
            price = quote["current_price"]
            
            # Simulated Insights
            return {
                "symbol": symbol.upper(),
                "price": price,
                "volatility": "MEDIUM",
                "trend": "BULLISH",
                "support_level": price * 0.95,
                "resistance_level": price * 1.05,
                "sentiment": "NEUTRAL",
                "note": f"The market for {symbol} is currently stable with a slight upward trend."
            }
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {"error": str(e)}

market_analyst = MarketAnalyst()
