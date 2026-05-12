import logging
import requests
from decimal import Decimal
from services.exchange_client import exchange_client
try:
    from strategy_engine import generate_signal
except ImportError:
    # Fallback if pathing is tricky during tests
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from strategy_engine import generate_signal

logger = logging.getLogger("MarketAnalyst")

class MarketAnalyst:
    def _fetch_binance_klines(self, symbol: str, interval: str = "1h", limit: int = 50):
        """Fetch historical OHLCV data from Binance Public API."""
        try:
            # Map common symbols to USDT pairs
            clean_symbol = symbol.upper().replace("USD", "").replace("USDT", "")
            binance_symbol = f"{clean_symbol}USDT"
            
            url = "https://api.binance.com/api/v3/klines"
            params = {"symbol": binance_symbol, "interval": interval, "limit": limit}
            resp = requests.get(url, params=params, timeout=10)
            
            if resp.status_code != 200:
                logger.warning(f"Binance API returned {resp.status_code} for {binance_symbol}")
                return None
                
            return resp.json()
        except Exception as e:
            logger.error(f"Error fetching Binance klined: {e}")
            return None

    def get_market_insight(self, symbol: str) -> dict:
        """
        Analyzes market data using real indicators (RSI, EMA, Volume).
        """
        try:
            # 1. Fetch historical data for indicators
            klines = self._fetch_binance_klines(symbol)
            
            if not klines or len(klines) < 20:
                # Fallback to simple price if indicators fail
                return {
                    "symbol": symbol.upper(),
                    "note": f"Technical indicators currently unavailable for {symbol}. Showing simulated trend.",
                    "volatility": "MEDIUM",
                    "trend": "NEUTRAL"
                }

            # 2. Extract closes and volume
            # kline format: [ot, o, h, l, c, v, ct, qv, nt, tbv, tqv, i]
            prices = [float(k[4]) for k in klines]
            current_volume = float(klines[-1][5])
            
            # Simple average volume for the period
            avg_volume = sum(float(k[5]) for k in klines) / len(klines)
            
            # 3. Generate Signal via Strategy Engine
            analysis = generate_signal(symbol, prices, current_volume, avg_volume)
            
            return {
                "symbol": symbol.upper(),
                "price": prices[-1],
                "signal": analysis["signal"],
                "confidence": analysis["confidence"],
                "rsi": analysis["rsi"],
                "ema": analysis["ema"],
                "volume_status": analysis["volume"],
                "reasons": analysis["reasons"],
                "note": f"Market analysis for {symbol.upper()} based on the last 50 hours of data."
            }
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {"error": str(e)}

market_analyst = MarketAnalyst()
