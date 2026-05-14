import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { BalancesService } from '../balances/balances.service';
import { EventEmitter2 } from '@nestjs/event-emitter';

@Injectable()
export class MatchingEngineService {
  constructor(
    private prisma: PrismaService,
    private balancesService: BalancesService,
    private eventEmitter: EventEmitter2,
  ) {}

  async matchOrder(newOrderId: string) {
    // 1. Load the new order
    const newOrder = await this.prisma.order.findUnique({
      where: { id: newOrderId },
      include: { pair: true },
    });

    if (!newOrder || newOrder.status === 'CANCELLED') return;

    const { pair } = newOrder;

    // 2. Find matching opposite orders
    // If new order is BUY → look for SELL orders with price <= newOrder.price
    // If new order is SELL → look for BUY orders with price >= newOrder.price
    const oppositeSide = newOrder.side === 'BUY' ? 'SELL' : 'BUY';

    const candidates = await this.prisma.order.findMany({
      where: {
        pairId: newOrder.pairId,
        side: oppositeSide,
        status: { in: ['OPEN', 'PARTIAL'] },
        // Price match condition
        price:
          newOrder.side === 'BUY'
            ? { lte: newOrder.price ?? undefined } // buy: find sells <= our price
            : { gte: newOrder.price ?? undefined }, // sell: find buys >= our price
      },
      orderBy: [
        // Best price first (cheapest sell / highest buy)
        { price: newOrder.side === 'BUY' ? 'asc' : 'desc' },
        { createdAt: 'asc' }, // oldest first (time priority)
      ],
    });

    // 3. Loop through candidates and match
    let remainingQty = Number(newOrder.quantity) - Number(newOrder.filledQty);

    for (const candidate of candidates) {
      if (remainingQty <= 0) break;

      const candidateRemaining =
        Number(candidate.quantity) - Number(candidate.filledQty);
      const tradeQty = Math.min(remainingQty, candidateRemaining);
      const tradePrice = Number(candidate.price); // always use resting order price

      // 4. Determine buyer and seller
      const buyerId =
        newOrder.side === 'BUY' ? newOrder.userId : candidate.userId;
      const sellerId =
        newOrder.side === 'SELL' ? newOrder.userId : candidate.userId;
      const buyOrderId = newOrder.side === 'BUY' ? newOrder.id : candidate.id;
      const sellOrderId = newOrder.side === 'SELL' ? newOrder.id : candidate.id;

      // 5. Create trade record
      const trade = await this.prisma.trade.create({
        data: {
          pairId: newOrder.pairId,
          buyOrderId,
          sellOrderId,
          buyerId,
          sellerId,
          price: tradePrice,
          quantity: tradeQty,
        },
      });

      // 6. Settle balances
      await this.balancesService.settleTrade(
        buyerId,
        sellerId,
        pair.baseCurrency,
        pair.quoteCurrency,
        tradeQty,
        tradePrice,
      );

      // 7. Update filled quantities
      remainingQty -= tradeQty;
      const newFilled =
        Number(newOrder.filledQty) +
        (Number(newOrder.quantity) - remainingQty - Number(newOrder.filledQty));

      await this.prisma.order.update({
        where: { id: newOrder.id },
        data: {
          filledQty: newFilled,
          status: remainingQty <= 0 ? 'FILLED' : 'PARTIAL',
        },
      });

      const candidateFilled = Number(candidate.filledQty) + tradeQty;
      await this.prisma.order.update({
        where: { id: candidate.id },
        data: {
          filledQty: candidateFilled,
          status:
            candidateFilled >= Number(candidate.quantity)
              ? 'FILLED'
              : 'PARTIAL',
        },
      });

      // 8. Emit event for WebSocket (real-time update)
      this.eventEmitter.emit('trade.executed', {
        trade,
        symbol: pair.symbol,
      });

      console.log(
        `✅ Trade executed: ${tradeQty} ${pair.baseCurrency} @ $${tradePrice}`,
      );
    }
  }
}
