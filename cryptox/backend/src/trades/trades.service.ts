import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class TradesService {
  constructor(private prisma: PrismaService) {}

  // Get all trades for a user (as buyer or seller)
  async getUserTrades(userId: string) {
    return this.prisma.trade.findMany({
      where: {
        OR: [{ buyerId: userId }, { sellerId: userId }],
      },
      include: { pair: true },
      orderBy: { createdAt: 'desc' },
      take: 100,
    });
  }

  // Get recent trades for a symbol (for chart + trade history panel)
  async getTradesBySymbol(symbol: string, limit = 50) {
    const pair = await this.prisma.tradingPair.findUnique({
      where: { symbol },
    });
    if (!pair) return [];

    return this.prisma.trade.findMany({
      where: { pairId: pair.id },
      orderBy: { createdAt: 'desc' },
      take: limit,
    });
  }

  // Get OHLCV candle data for chart
  // Groups trades by hour and returns open/high/low/close/volume
  async getCandleData(symbol: string) {
    const pair = await this.prisma.tradingPair.findUnique({
      where: { symbol },
    });
    if (!pair) return [];

    // Get last 200 trades
    const trades = await this.prisma.trade.findMany({
      where: { pairId: pair.id },
      orderBy: { createdAt: 'asc' },
      take: 200,
    });

    if (trades.length === 0) return [];

    // Group trades into 1-hour candles
    const candles: Record<
      string,
      {
        time: number;
        open: number;
        high: number;
        low: number;
        close: number;
        volume: number;
      }
    > = {};

    for (const trade of trades) {
      // Round down to nearest hour
      const hourKey = Math.floor(trade.createdAt.getTime() / 60000) * 60;

      if (!candles[hourKey]) {
        candles[hourKey] = {
          time: hourKey,
          open: Number(trade.price),
          high: Number(trade.price),
          low: Number(trade.price),
          close: Number(trade.price),
          volume: Number(trade.quantity),
        };
      } else {
        const c = candles[hourKey];
        c.high = Math.max(c.high, Number(trade.price));
        c.low = Math.min(c.low, Number(trade.price));
        c.close = Number(trade.price);
        c.volume += Number(trade.quantity);
      }
    }

    return Object.values(candles).sort((a, b) => a.time - b.time);
  }
}
