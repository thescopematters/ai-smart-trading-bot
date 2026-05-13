import { Controller, Get, Param } from '@nestjs/common';
import { PairsService } from './pairs.service';

@Controller('api/pairs')
export class PairsController {
  constructor(private readonly pairsService: PairsService) {}

  // GET /api/pairs
  @Get()
  getAllPairs() {
    return this.pairsService.getAllPairs();
  }

  // GET /api/pairs/BTC%2FUSDT
  @Get(':symbol')
  getPair(@Param('symbol') symbol: string) {
    return this.pairsService.getPairBySymbol(decodeURIComponent(symbol));
  }
}
