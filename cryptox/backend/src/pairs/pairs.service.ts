import { Injectable, OnModuleInit } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class PairsService implements OnModuleInit {
  constructor(private prisma: PrismaService) {}

  // Auto-seed trading pairs when app starts
  async onModuleInit() {
    const count = await this.prisma.tradingPair.count();
    if (count === 0) {
      await this.prisma.tradingPair.createMany({
        data: [
          {
            symbol: 'BTC/USDT',
            baseCurrency: 'BTC',
            quoteCurrency: 'USDT',
            minOrderSize: 0.0001,
          },
          {
            symbol: 'ETH/USDT',
            baseCurrency: 'ETH',
            quoteCurrency: 'USDT',
            minOrderSize: 0.001,
          },
        ],
      });
      console.log('✅ Trading pairs seeded');
    }
  }

  async getAllPairs() {
    return this.prisma.tradingPair.findMany({
      where: { isActive: true },
    });
  }

  async getPairBySymbol(symbol: string) {
    return this.prisma.tradingPair.findUnique({
      where: { symbol },
    });
  }
}
