import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class BalancesService {
  constructor(private prisma: PrismaService) {}

  // Get all balances for a user
  async getUserBalances(userId: string) {
    const balances = await this.prisma.balance.findMany({
      where: { userId },
    });
    if (!balances.length) {
      throw new NotFoundException('No balances found');
    }
    return balances;
  }

  // Add dummy funds (for testing)
  async topUp(userId: string, currency: string, amount: number) {
    const balance = await this.prisma.balance.findUnique({
      where: { userId_currency: { userId, currency } },
    });

    if (!balance) {
      // Create if doesn't exist
      return this.prisma.balance.create({
        data: { userId, currency, available: amount },
      });
    }

    return this.prisma.balance.update({
      where: { userId_currency: { userId, currency } },
      data: { available: { increment: amount } },
    });
  }

  // Internal: lock funds when order is placed
  async lockFunds(userId: string, currency: string, amount: number) {
    const balance = await this.prisma.balance.findUnique({
      where: { userId_currency: { userId, currency } },
    });

    if (!balance || Number(balance.available) < amount) {
      throw new Error('Insufficient balance');
    }

    return this.prisma.balance.update({
      where: { userId_currency: { userId, currency } },
      data: {
        available: { decrement: amount },
        locked: { increment: amount },
      },
    });
  }

  // Internal: unlock funds when order is cancelled
  async unlockFunds(userId: string, currency: string, amount: number) {
    return this.prisma.balance.update({
      where: { userId_currency: { userId, currency } },
      data: {
        available: { increment: amount },
        locked: { decrement: amount },
      },
    });
  }

  // Internal: settle trade balances
  async settleTrade(
    buyerId: string,
    sellerId: string,
    baseCurrency: string,
    quoteCurrency: string,
    quantity: number,
    price: number,
  ) {
    const totalCost = quantity * price;

    // Buyer: loses USDT (locked), gains BTC (available)
    await this.prisma.balance.update({
      where: { userId_currency: { userId: buyerId, currency: quoteCurrency } },
      data: { locked: { decrement: totalCost } },
    });
    await this.prisma.balance.upsert({
      where: { userId_currency: { userId: buyerId, currency: baseCurrency } },
      update: { available: { increment: quantity } },
      create: { userId: buyerId, currency: baseCurrency, available: quantity },
    });

    // Seller: loses BTC (locked), gains USDT (available)
    await this.prisma.balance.update({
      where: { userId_currency: { userId: sellerId, currency: baseCurrency } },
      data: { locked: { decrement: quantity } },
    });
    await this.prisma.balance.upsert({
      where: { userId_currency: { userId: sellerId, currency: quoteCurrency } },
      update: { available: { increment: totalCost } },
      create: {
        userId: sellerId,
        currency: quoteCurrency,
        available: totalCost,
      },
    });
  }
}
