import { Controller, Get, Param, UseGuards, Request } from '@nestjs/common';
import { TradesService } from './trades.service';
import { JwtAuthGuard } from '../common/jwt-auth.guard';
import { JwtService } from '@nestjs/jwt';

@Controller('api/trades')
export class TradesController {
  constructor(
    private readonly tradesService: TradesService,
    private readonly jwtService: JwtService,
  ) {}

  // GET /api/trades/my  → my trade history
  @UseGuards(JwtAuthGuard)
  @Get('my')
  getMyTrades(@Request() req) {
    return this.tradesService.getUserTrades(req.user.sub);
  }

  // GET /api/trades/symbol/BTC%2FUSDT  → recent trades for a pair
  @Get('symbol/:symbol')
  getTradesBySymbol(@Param('symbol') symbol: string) {
    return this.tradesService.getTradesBySymbol(decodeURIComponent(symbol));
  }

  // GET /api/trades/candles/BTC%2FUSDT  → OHLCV for chart
  @Get('candles/:symbol')
  getCandleData(@Param('symbol') symbol: string) {
    return this.tradesService.getCandleData(decodeURIComponent(symbol));
  }
}
