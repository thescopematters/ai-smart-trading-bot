"""
STRATEGY ENGINE — Technical Analysis Signal Generator
------------------------------------------------------
Built on: 2026-04-27

Purpose:
  Provides pure analysis functions (RSI, EMA, Volume Score) that are
  COMPLETELY SEPARATE from trade execution. The AI can use these signals
  to inform paper trading decisions, but they never execute trades directly.

Future:
  Can be exposed as an MCP tool (@mcp.tool() get_trade_signal) once validated.
"""

from decimal import Decimal


def calculate_rsi(prices: list, period: int = 14) -> float:
    """
    Relative Strength Index.
    < 30 = Oversold (potential BUY signal)
    > 70 = Overbought (potential SELL signal)

    Args:
        prices: List of closing prices (most recent last), needs at least period+1 values.
        period: RSI lookback period (default 14).

    Returns:
        RSI value between 0 and 100.
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral if not enough data

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    recent = deltas[-period:]

    gains = [d for d in recent if d > 0]
    losses = [-d for d in recent if d < 0]

    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_ema(prices: list, period: int = 20) -> float:
    """
    Exponential Moving Average.
    Price above EMA = bullish trend
    Price below EMA = bearish trend

    Args:
        prices: List of closing prices (most recent last).
        period: EMA lookback period (default 20).

    Returns:
        EMA value.
    """
    if len(prices) < period:
        return prices[-1] if prices else 0.0

    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # Start with SMA

    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema

    return round(ema, 2)


def volume_score(volume_24h: float, avg_volume: float) -> str:
    """
    Compare current volume to average.
    HIGH = more activity than normal (momentum)
    LOW = less activity (caution)

    Args:
        volume_24h: Current 24h trading volume.
        avg_volume: Average 24h trading volume.

    Returns:
        'HIGH', 'NORMAL', or 'LOW'
    """
    if avg_volume <= 0:
        return "UNKNOWN"

    ratio = volume_24h / avg_volume
    if ratio > 1.5:
        return "HIGH"
    elif ratio < 0.5:
        return "LOW"
    return "NORMAL"


def generate_signal(symbol: str, prices: list, volume_24h: float = 0, avg_volume: float = 0) -> dict:
    """
    Generate a composite BUY/SELL/HOLD signal based on technical indicators.

    Args:
        symbol: Coin symbol (e.g. "BTC").
        prices: List of recent closing prices (at least 21 values ideal).
        volume_24h: Current 24h trading volume.
        avg_volume: Average 24h volume for comparison.

    Returns:
        dict with signal, confidence, and reasons.
    """
    if not prices or len(prices) < 2:
        return {"signal": "HOLD", "confidence": 0.0, "reasons": ["Insufficient price data."]}

    rsi = calculate_rsi(prices)
    ema = calculate_ema(prices)
    vol = volume_score(volume_24h, avg_volume) if avg_volume > 0 else "UNKNOWN"
    current_price = prices[-1]

    reasons = []
    score = 0  # positive = BUY, negative = SELL

    # RSI analysis
    if rsi < 30:
        score += 2
        reasons.append(f"RSI={rsi} → Oversold (strong BUY signal)")
    elif rsi < 40:
        score += 1
        reasons.append(f"RSI={rsi} → Approaching oversold")
    elif rsi > 70:
        score -= 2
        reasons.append(f"RSI={rsi} → Overbought (strong SELL signal)")
    elif rsi > 60:
        score -= 1
        reasons.append(f"RSI={rsi} → Approaching overbought")
    else:
        reasons.append(f"RSI={rsi} → Neutral range")

    # EMA analysis
    if current_price > ema:
        score += 1
        reasons.append(f"Price (${current_price:,.2f}) above EMA (${ema:,.2f}) → Bullish trend")
    else:
        score -= 1
        reasons.append(f"Price (${current_price:,.2f}) below EMA (${ema:,.2f}) → Bearish trend")

    # Volume analysis
    if vol == "HIGH":
        reasons.append("Volume is HIGH → Strong momentum")
    elif vol == "LOW":
        reasons.append("Volume is LOW → Weak conviction, caution advised")

    # Determine signal
    if score >= 2:
        signal = "BUY"
        confidence = min(0.9, 0.5 + score * 0.1)
    elif score <= -2:
        signal = "SELL"
        confidence = min(0.9, 0.5 + abs(score) * 0.1)
    else:
        signal = "HOLD"
        confidence = 0.4

    return {
        "symbol": symbol.upper(),
        "signal": signal,
        "confidence": round(confidence, 2),
        "rsi": rsi,
        "ema": round(ema, 2),
        "volume": vol,
        "reasons": reasons,
    }
