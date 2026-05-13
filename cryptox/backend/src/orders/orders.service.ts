import {
  Injectable,
  BadRequestException,
  NotFoundException,
} from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { BalancesService } from '../balances/balances.service';
import { MatchingEngineService } from '../matching-engine/matching-engine.service';
import { CreateOrderDto, OrderSide, OrderType } from './dto/create-order.dto';

@Injectable()
export class OrdersService {
  constructor(
    private prisma: PrismaService,
    private balancesService: BalancesService,
    private matchingEngine: MatchingEngineService,
  ) {}

  async createOrder(userId: string, dto: CreateOrderDto) {
    // 1. Find trading pair
    const pair = await this.prisma.tradingPair.findUnique({
      where: { symbol: dto.symbol },
    });
    if (!pair) throw new BadRequestException('Trading pair not found');
    if (!pair.isActive)
      throw new BadRequestException('Trading pair is not active');

    // 2. Validate price for limit orders
    if (dto.type === OrderType.LIMIT && !dto.price) {
      throw new BadRequestException('Price is required for limit orders');
    }

    // 3. Lock funds before placing order
    if (dto.side === OrderSide.BUY) {
      if (dto.type === OrderType.MARKET) {
        // Market BUY: no price known yet
        // Lock full available USDT balance as safety
        const balance = await this.prisma.balance.findUnique({
          where: { userId_currency: { userId, currency: pair.quoteCurrency } },
        });
        const available = Number(balance?.available || 0);
        if (available <= 0) {
          throw new BadRequestException(
            `Insufficient ${pair.quoteCurrency} balance`,
          );
        }
        // Lock only what this order needs: qty * best available estimate
        // We lock full available so matching engine can settle properly
        await this.balancesService.lockFunds(
          userId,
          pair.quoteCurrency,
          available, // lock all available — will be released after matching
        );
      } else {
        // Limit BUY: lock exact amount (qty * price)
        const lockAmount = dto.quantity * (dto.price || 0);
        if (lockAmount <= 0) {
          throw new BadRequestException('Invalid order amount');
        }
        await this.balancesService.lockFunds(
          userId,
          pair.quoteCurrency,
          lockAmount,
        );
      }
    } else {
      // SELL: always lock base currency (BTC/ETH) regardless of order type
      await this.balancesService.lockFunds(
        userId,
        pair.baseCurrency,
        dto.quantity,
      );
    }

    // 4. Create order in DB
    const order = await this.prisma.order.create({
      data: {
        userId,
        pairId: pair.id,
        side: dto.side,
        type: dto.type,
        price: dto.price,
        quantity: dto.quantity,
        status: 'OPEN',
      },
    });

    // 5. Run matching engine
    await this.matchingEngine.matchOrder(order.id);

    // 6. Return updated order
    return this.prisma.order.findUnique({ where: { id: order.id } });
  }

  async getUserOrders(userId: string) {
    return this.prisma.order.findMany({
      where: { userId },
      include: { pair: true },
      orderBy: { createdAt: 'desc' },
    });
  }

  async cancelOrder(userId: string, orderId: string) {
    const order = await this.prisma.order.findUnique({
      where: { id: orderId },
      include: { pair: true },
    });

    if (!order) throw new NotFoundException('Order not found');
    if (order.userId !== userId)
      throw new BadRequestException('Not your order');
    if (order.status === 'FILLED')
      throw new BadRequestException('Cannot cancel filled order');
    if (order.status === 'CANCELLED')
      throw new BadRequestException('Already cancelled');

    // Unlock remaining funds
    const remainingQty = Number(order.quantity) - Number(order.filledQty);

    if (order.side === 'BUY') {
      if (order.price) {
        // Limit order — unlock remaining qty * price
        const unlockAmount = remainingQty * Number(order.price);
        await this.balancesService.unlockFunds(
          userId,
          order.pair.quoteCurrency,
          unlockAmount,
        );
      } else {
        // Market order — unlock whatever is still locked
        const balance = await this.prisma.balance.findUnique({
          where: {
            userId_currency: {
              userId,
              currency: order.pair.quoteCurrency,
            },
          },
        });
        const lockedAmount = Number(balance?.locked || 0);
        if (lockedAmount > 0) {
          await this.balancesService.unlockFunds(
            userId,
            order.pair.quoteCurrency,
            lockedAmount,
          );
        }
      }
    } else {
      // SELL — unlock remaining base currency
      await this.balancesService.unlockFunds(
        userId,
        order.pair.baseCurrency,
        remainingQty,
      );
    }

    return this.prisma.order.update({
      where: { id: orderId },
      data: { status: 'CANCELLED' },
    });
  }

  async getOrderBook(symbol: string) {
    const pair = await this.prisma.tradingPair.findUnique({
      where: { symbol },
    });
    if (!pair) throw new NotFoundException('Pair not found');

    const [bids, asks] = await Promise.all([
      this.prisma.order.findMany({
        where: {
          pairId: pair.id,
          side: 'BUY',
          status: { in: ['OPEN', 'PARTIAL'] },
        },
        orderBy: { price: 'desc' },
        take: 20,
      }),
      this.prisma.order.findMany({
        where: {
          pairId: pair.id,
          side: 'SELL',
          status: { in: ['OPEN', 'PARTIAL'] },
        },
        orderBy: { price: 'asc' },
        take: 20,
      }),
    ]);

    return { bids, asks };
  }
}
